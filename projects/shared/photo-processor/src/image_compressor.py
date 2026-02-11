"""Image compression module — resize/compress images to a target max file size."""

import io
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from PIL import Image

HEIC_EXTENSIONS = {".heic", ".heif"}
DIMENSION_SCALE_STEPS = [0.75, 0.5, 0.35, 0.25]


@dataclass
class CompressResult:
    input_path: Path
    output_path: Path
    original_size: int = 0
    final_size: int = 0
    quality_used: Optional[int] = None
    scale_used: Optional[float] = None
    converted_from_heic: bool = False
    skipped: bool = False
    error: Optional[str] = None


class ImageCompressor:
    """Compress images to fit under a maximum file size using binary search on JPEG quality."""

    def __init__(
        self,
        max_size_bytes: int = 5 * 1024 * 1024,
        min_quality: int = 20,
        verbose: bool = False,
    ):
        self.max_size_bytes = max_size_bytes
        self.min_quality = min_quality
        self.verbose = verbose

    def compress_to_target(self, input_path: Path, output_path: Path) -> CompressResult:
        """Compress a single image to be under max_size_bytes.

        Pipeline:
        1. If already under limit, copy unchanged.
        2. Convert HEIC to JPEG via sips if needed.
        3. Binary search on JPEG quality.
        4. If min quality still too large, reduce dimensions progressively.
        5. Last resort: thumbnail to 2000x2000 at quality 15.
        """
        result = CompressResult(input_path=input_path, output_path=output_path)

        try:
            result.original_size = input_path.stat().st_size

            # Step 1: Already under limit?
            if result.original_size <= self.max_size_bytes:
                is_heic = input_path.suffix.lower() in HEIC_EXTENSIONS
                if is_heic:
                    # Still need to convert HEIC → JPEG even if small
                    jpeg_path = self._convert_heic(input_path)
                    if jpeg_path is None:
                        result.error = "HEIC conversion failed"
                        return result
                    result.converted_from_heic = True
                    shutil.copy2(jpeg_path, output_path)
                    result.final_size = output_path.stat().st_size
                    result.skipped = result.final_size <= self.max_size_bytes
                    if result.skipped:
                        return result
                    # If converted JPEG is over limit, continue to compression
                else:
                    shutil.copy2(input_path, output_path)
                    result.final_size = result.original_size
                    result.skipped = True
                    return result

            # Step 2: Convert HEIC if needed
            is_heic = input_path.suffix.lower() in HEIC_EXTENSIONS
            if is_heic:
                working_path = self._convert_heic(input_path)
                if working_path is None:
                    result.error = "HEIC conversion failed"
                    return result
                result.converted_from_heic = True
            else:
                working_path = input_path

            # Load image
            img = Image.open(working_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Step 3: Binary search on quality at original dimensions
            quality, size = self._find_optimal_quality(img)
            if size <= self.max_size_bytes:
                self._save_final(img, output_path, quality)
                result.final_size = output_path.stat().st_size
                result.quality_used = quality
                result.scale_used = 1.0
                return result

            # Step 4: Progressive dimension reduction
            original_w, original_h = img.size
            for scale in DIMENSION_SCALE_STEPS:
                new_w = int(original_w * scale)
                new_h = int(original_h * scale)
                if new_w < 100 or new_h < 100:
                    continue

                resized = img.resize((new_w, new_h), Image.LANCZOS)
                quality, size = self._find_optimal_quality(resized)
                if size <= self.max_size_bytes:
                    self._save_final(resized, output_path, quality)
                    result.final_size = output_path.stat().st_size
                    result.quality_used = quality
                    result.scale_used = scale
                    if self.verbose:
                        print(f"    Scaled to {scale*100:.0f}% ({new_w}x{new_h}), quality={quality}")
                    return result

            # Step 5: Last resort — aggressive thumbnail
            img.thumbnail((2000, 2000), Image.LANCZOS)
            self._save_final(img, output_path, 15)
            result.final_size = output_path.stat().st_size
            result.quality_used = 15
            result.scale_used = 0.0  # indicates thumbnail
            return result

        except Exception as e:
            result.error = str(e)
            return result

    def _find_optimal_quality(self, img: Image.Image) -> tuple:
        """Binary search for highest JPEG quality that fits under max_size_bytes.

        Returns (quality, file_size_bytes).
        """
        lo, hi = self.min_quality, 95
        best_quality = lo
        best_size = self._save_to_buffer(img, lo)

        # Quick check: if min quality already under limit, search upward
        if best_size > self.max_size_bytes:
            return lo, best_size

        while lo <= hi:
            mid = (lo + hi) // 2
            size = self._save_to_buffer(img, mid)

            if size <= self.max_size_bytes:
                best_quality = mid
                best_size = size
                lo = mid + 1
            else:
                hi = mid - 1

        return best_quality, best_size

    def _save_to_buffer(self, img: Image.Image, quality: int) -> int:
        """Save image to in-memory buffer, return size in bytes."""
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.tell()

    def _save_final(self, img: Image.Image, output_path: Path, quality: int) -> None:
        """Save the final compressed image to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, format="JPEG", quality=quality, optimize=True)

    def _convert_heic(self, heic_path: Path) -> Optional[Path]:
        """Convert HEIC to JPEG using macOS sips. Returns path to JPEG or None."""
        try:
            tmp_dir = tempfile.mkdtemp(prefix="photo-processor-")
            jpeg_path = Path(tmp_dir) / (heic_path.stem + ".jpg")
            result = subprocess.run(
                ["sips", "-s", "format", "jpeg", str(heic_path), "--out", str(jpeg_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                if self.verbose:
                    print(f"    sips error: {result.stderr.strip()}")
                return None
            return jpeg_path
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            if self.verbose:
                print(f"    HEIC conversion error: {e}")
            return None
