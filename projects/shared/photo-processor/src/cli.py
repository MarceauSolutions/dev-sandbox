"""CLI interface and main orchestration for Photo Processor."""

import argparse
import shutil
import tempfile
from pathlib import Path

from .image_compressor import CompressResult, ImageCompressor
from .photo_exporter import PhotoExporter, PhotoInfo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="photo-processor",
        description="Export photos from macOS Photos.app, resize/compress to a max file size.",
    )

    # Selection mode (mutually exclusive)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--album",
        type=str,
        help='Export all photos from a named album (e.g., --album "Vacation 2025")',
    )
    selection.add_argument(
        "--recent",
        type=int,
        help="Export the N most recent photos (e.g., --recent 10)",
    )
    selection.add_argument(
        "--pick",
        action="store_true",
        help="Open an interactive album picker dialog",
    )
    selection.add_argument(
        "--browse",
        action="store_true",
        help="Browse recent photos and pick individual ones by number",
    )

    # Required output
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=True,
        help="Output folder path (created if it doesn't exist)",
    )

    # Optional flags
    parser.add_argument(
        "--max-size",
        type=float,
        default=5.0,
        help="Maximum file size in MB (default: 5.0)",
    )
    parser.add_argument(
        "--min-quality",
        type=int,
        default=20,
        help="Minimum JPEG quality before dimension reduction (default: 20)",
    )
    parser.add_argument(
        "--no-resize",
        action="store_true",
        help="Skip resize/compression, export originals only",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be exported without actually exporting",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed progress for each photo",
    )
    parser.add_argument(
        "--indices",
        type=str,
        help='Photo indices to export from --recent list (e.g., "1,3,5-8" or "all")',
    )

    return parser


def run(args) -> int:
    """Main execution logic. Returns exit code (0=success)."""
    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    exporter = PhotoExporter(verbose=args.verbose)

    # Get photos based on selection mode
    if args.album:
        print(f'Finding photos in album "{args.album}"...')
        photos = exporter.get_photos_by_album(args.album)
        if not photos:
            albums = exporter.list_albums()
            print(f'Album "{args.album}" not found or empty.')
            if albums:
                print(f"Available albums: {', '.join(albums[:20])}")
            return 1
    elif args.recent:
        print(f"Finding {args.recent} most recent photos...")
        photos = exporter.get_recent_photos(args.recent)
    elif args.browse:
        photos = exporter.browse_and_pick()
        if not photos:
            print("No photos selected.")
            return 1
    elif args.pick:
        album_name = exporter.pick_album_interactive()
        if not album_name:
            print("No album selected. Exiting.")
            return 1
        print(f'Finding photos in album "{album_name}"...')
        photos = exporter.get_photos_by_album(album_name)
    else:
        return 1

    if not photos:
        print("No photos found matching the criteria.")
        return 1

    # Filter by indices if provided (e.g., "1,3,5-8")
    if args.indices and args.indices.lower() != "all":
        selected_indices: set[int] = set()
        for part in args.indices.split(","):
            part = part.strip()
            if "-" in part:
                try:
                    start, end = part.split("-", 1)
                    for idx in range(int(start), int(end) + 1):
                        selected_indices.add(idx)
                except ValueError:
                    continue
            else:
                try:
                    selected_indices.add(int(part))
                except ValueError:
                    continue
        photos = [photos[i - 1] for i in sorted(selected_indices) if 1 <= i <= len(photos)]

    print(f"Found {len(photos)} photo(s) to process.\n")

    # Dry run
    if args.dry_run:
        for p in photos:
            date_str = p.date.strftime("%Y-%m-%d %H:%M") if p.date else "unknown date"
            heic_tag = " [HEIC]" if p.is_heic else ""
            print(f"  {p.filename}{heic_tag}  ({date_str})")
        print(f"\nDry run complete. Use without --dry-run to export.")
        return 0

    # Set up compressor
    max_bytes = int(args.max_size * 1024 * 1024)
    compressor = ImageCompressor(
        max_size_bytes=max_bytes,
        min_quality=args.min_quality,
        verbose=args.verbose,
    )

    # Process photos
    results: list[CompressResult] = []
    tmp_dir = Path(tempfile.mkdtemp(prefix="photo-processor-"))

    try:
        for i, photo in enumerate(photos, 1):
            print(f"[{i}/{len(photos)}] {photo.filename}...", end=" ", flush=True)

            # Export from Photos.app
            exported_path = exporter.export_photo(photo, tmp_dir)
            if exported_path is None:
                print("FAILED (export error)")
                results.append(
                    CompressResult(
                        input_path=Path(photo.filename),
                        output_path=output_dir / photo.filename,
                        error="Failed to export from Photos.app",
                    )
                )
                continue

            # Determine output filename (always .jpg for compressed output)
            if args.no_resize:
                dest = output_dir / photo.filename
                dest = _unique_path(dest)
                shutil.copy2(exported_path, dest)
                size_mb = dest.stat().st_size / (1024 * 1024)
                print(f"copied ({size_mb:.1f} MB)")
                results.append(
                    CompressResult(
                        input_path=exported_path,
                        output_path=dest,
                        original_size=exported_path.stat().st_size,
                        final_size=dest.stat().st_size,
                        skipped=True,
                    )
                )
            else:
                out_name = Path(photo.filename).stem + ".jpg"
                dest = _unique_path(output_dir / out_name)
                result = compressor.compress_to_target(exported_path, dest)
                results.append(result)
                _print_result_inline(result)
    finally:
        # Clean up temp directory
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # Print summary
    print()
    _print_summary(results, output_dir, args.max_size)

    failed = sum(1 for r in results if r.error)
    return 1 if failed == len(results) else 0


def _print_result_inline(result: CompressResult) -> None:
    if result.error:
        print(f"FAILED ({result.error})")
    elif result.skipped:
        size_mb = result.final_size / (1024 * 1024)
        print(f"OK (already under limit, {size_mb:.1f} MB)")
    else:
        orig_mb = result.original_size / (1024 * 1024)
        final_mb = result.final_size / (1024 * 1024)
        reduction = (1 - result.final_size / result.original_size) * 100 if result.original_size > 0 else 0
        extra = ""
        if result.converted_from_heic:
            extra = ", HEIC→JPG"
        if result.scale_used and result.scale_used < 1.0:
            extra += f", scaled {result.scale_used*100:.0f}%"
        print(f"{orig_mb:.1f} MB → {final_mb:.1f} MB ({reduction:.0f}% smaller, q={result.quality_used}{extra})")


def _print_summary(results: list[CompressResult], output_dir: Path, max_size_mb: float) -> None:
    total = len(results)
    successful = sum(1 for r in results if not r.error)
    failed = total - successful
    skipped = sum(1 for r in results if r.skipped and not r.error)
    compressed = successful - skipped

    total_original = sum(r.original_size for r in results if not r.error)
    total_final = sum(r.final_size for r in results if not r.error)
    saved = total_original - total_final

    print("=" * 50)
    print(f"  Output: {output_dir}")
    print(f"  Photos: {successful}/{total} successful", end="")
    if failed > 0:
        print(f" ({failed} failed)", end="")
    print()

    if compressed > 0:
        print(f"  Compressed: {compressed} photos")
    if skipped > 0:
        print(f"  Already under {max_size_mb} MB: {skipped} photos")

    if total_original > 0:
        print(f"  Total size: {total_original / (1024*1024):.1f} MB → {total_final / (1024*1024):.1f} MB")
        print(f"  Space saved: {saved / (1024*1024):.1f} MB ({saved / total_original * 100:.0f}%)")
    print("=" * 50)


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
