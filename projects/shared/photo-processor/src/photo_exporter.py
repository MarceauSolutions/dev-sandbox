"""Photos.app integration — export photos via osxphotos (primary) or AppleScript (fallback)."""

import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    import osxphotos

    OSXPHOTOS_AVAILABLE = True
except ImportError:
    OSXPHOTOS_AVAILABLE = False

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tiff", ".bmp", ".gif", ".webp"}


@dataclass
class PhotoInfo:
    """Metadata for a photo from Photos.app."""

    uuid: str
    filename: str
    original_path: Optional[Path]
    date: Optional[datetime]
    is_heic: bool
    album: Optional[str] = None


class PhotoExporter:
    """Export photos from macOS Photos.app library."""

    def __init__(self, verbose: bool = False):
        self._verbose = verbose
        if not OSXPHOTOS_AVAILABLE:
            print(
                "Warning: osxphotos not installed. Using AppleScript-only mode.\n"
                "  Install for faster, more reliable access: pip install osxphotos"
            )

    def list_albums(self) -> List[str]:
        """Return all album names from Photos.app."""
        if OSXPHOTOS_AVAILABLE:
            return self._list_albums_osxphotos()
        return self._list_albums_applescript()

    def get_photos_by_album(self, album_name: str) -> List[PhotoInfo]:
        """Get all photos in a named album."""
        if OSXPHOTOS_AVAILABLE:
            return self._get_album_osxphotos(album_name)
        return self._get_album_applescript(album_name)

    def get_recent_photos(self, count: int) -> List[PhotoInfo]:
        """Get the N most recent photos by date."""
        if OSXPHOTOS_AVAILABLE:
            return self._get_recent_osxphotos(count)
        return self._get_recent_applescript(count)

    def pick_album_interactive(self) -> Optional[str]:
        """Show a native macOS dialog to pick an album. Returns album name or None."""
        albums = self.list_albums()
        if not albums:
            print("No albums found in Photos.app.")
            return None

        # Try native macOS dialog first
        try:
            return self._pick_album_applescript_dialog(albums)
        except Exception:
            # Fall back to terminal menu
            return self._pick_album_terminal(albums)

    def browse_and_pick(self, album_name: Optional[str] = None, recent: int = 50) -> List[PhotoInfo]:
        """Show photos in terminal and let user pick by number. Returns selected PhotoInfo list.

        If album_name is provided, shows photos from that album.
        Otherwise shows the most recent N photos.
        """
        if album_name:
            photos = self.get_photos_by_album(album_name)
            label = f'album "{album_name}"'
        else:
            photos = self.get_recent_photos(recent)
            label = f"most recent {recent}"

        if not photos:
            print(f"No photos found in {label}.")
            return []

        print(f"\nPhotos from {label}:\n")
        for i, p in enumerate(photos, 1):
            date_str = p.date.strftime("%Y-%m-%d %H:%M") if p.date else "unknown"
            heic_tag = " [HEIC]" if p.is_heic else ""
            print(f"  {i:3d}. {p.filename}{heic_tag}  ({date_str})")

        print(f"\nEnter photo numbers to export (e.g., 1,3,5-8 or 'all'):")
        try:
            choice = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            return []

        if choice.lower() == "all":
            return photos

        # Parse selection like "1,3,5-8,12"
        selected_indices: set[int] = set()
        for part in choice.split(","):
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

        result = []
        for idx in sorted(selected_indices):
            if 1 <= idx <= len(photos):
                result.append(photos[idx - 1])

        return result

    def export_photo(self, photo: PhotoInfo, dest_dir: Path) -> Optional[Path]:
        """Export a single photo to dest_dir. Returns path to exported file or None."""
        dest_dir.mkdir(parents=True, exist_ok=True)

        # If we have a direct path from osxphotos, just copy/link
        if photo.original_path and photo.original_path.exists():
            import shutil

            dest_path = dest_dir / photo.filename
            # Handle filename collisions
            dest_path = self._unique_path(dest_path)
            shutil.copy2(photo.original_path, dest_path)
            return dest_path

        # Fallback: AppleScript export
        return self._export_single_applescript(photo, dest_dir)

    # ── osxphotos methods ──────────────────────────────────────────────

    def _list_albums_osxphotos(self) -> List[str]:
        try:
            photosdb = osxphotos.PhotosDB()
            albums = photosdb.album_info
            return sorted([a.title for a in albums if a.title])
        except Exception as e:
            if self._verbose:
                print(f"  osxphotos error listing albums: {e}")
            return self._list_albums_applescript()

    def _get_album_osxphotos(self, album_name: str) -> List[PhotoInfo]:
        try:
            photosdb = osxphotos.PhotosDB()
            photos = photosdb.photos(albums=[album_name])
            results = []
            for p in photos:
                if not p.ismissing and p.original_filename:
                    ext = Path(p.original_filename).suffix.lower()
                    if ext in PHOTO_EXTENSIONS:
                        results.append(
                            PhotoInfo(
                                uuid=p.uuid,
                                filename=p.original_filename,
                                original_path=Path(p.path) if p.path else None,
                                date=p.date,
                                is_heic=ext in {".heic", ".heif"},
                                album=album_name,
                            )
                        )
            return sorted(results, key=lambda x: x.date or datetime.min, reverse=True)
        except Exception as e:
            if self._verbose:
                print(f"  osxphotos error: {e}")
            return self._get_album_applescript(album_name)

    def _get_recent_osxphotos(self, count: int) -> List[PhotoInfo]:
        try:
            photosdb = osxphotos.PhotosDB()
            all_photos = photosdb.photos()
            # Filter to actual photos (not videos), sort by date desc
            photo_list = []
            for p in all_photos:
                if p.ismissing or not p.original_filename:
                    continue
                ext = Path(p.original_filename).suffix.lower()
                if ext not in PHOTO_EXTENSIONS:
                    continue
                photo_list.append(
                    PhotoInfo(
                        uuid=p.uuid,
                        filename=p.original_filename,
                        original_path=Path(p.path) if p.path else None,
                        date=p.date,
                        is_heic=ext in {".heic", ".heif"},
                    )
                )
            photo_list.sort(key=lambda x: x.date or datetime.min, reverse=True)
            return photo_list[:count]
        except Exception as e:
            if self._verbose:
                print(f"  osxphotos error: {e}")
            return self._get_recent_applescript(count)

    # ── AppleScript methods ────────────────────────────────────────────

    def _list_albums_applescript(self) -> List[str]:
        script = 'tell application "Photos" to get name of albums'
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return []
            names = [n.strip() for n in result.stdout.strip().split(",") if n.strip()]
            return sorted(names)
        except Exception:
            return []

    def _get_album_applescript(self, album_name: str) -> List[PhotoInfo]:
        script = f'''
        tell application "Photos"
            set theAlbum to album "{album_name}"
            set thePhotos to media items of theAlbum
            set output to ""
            repeat with p in thePhotos
                set fname to filename of p
                set pid to id of p
                set d to date of p
                set output to output & pid & "|||" & fname & "|||" & (d as string) & linefeed
            end repeat
            return output
        end tell
        '''
        return self._parse_applescript_photo_list(script, album_name)

    def _get_recent_applescript(self, count: int) -> List[PhotoInfo]:
        # AppleScript: get last N photos by date
        script = f'''
        tell application "Photos"
            set allPhotos to media items
            set photoCount to count of allPhotos
            set startIdx to photoCount - {count} + 1
            if startIdx < 1 then set startIdx to 1
            set output to ""
            repeat with i from startIdx to photoCount
                set p to item i of allPhotos
                set fname to filename of p
                set pid to id of p
                set d to date of p
                set output to output & pid & "|||" & fname & "|||" & (d as string) & linefeed
            end repeat
            return output
        end tell
        '''
        return self._parse_applescript_photo_list(script)

    def _parse_applescript_photo_list(
        self, script: str, album: Optional[str] = None
    ) -> List[PhotoInfo]:
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                if self._verbose:
                    print(f"  AppleScript error: {result.stderr.strip()}")
                return []

            photos = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if not line or "|||" not in line:
                    continue
                parts = line.split("|||")
                if len(parts) < 2:
                    continue
                uuid = parts[0].strip()
                filename = parts[1].strip()
                ext = Path(filename).suffix.lower()
                if ext not in PHOTO_EXTENSIONS:
                    continue

                date_val = None
                if len(parts) >= 3:
                    try:
                        date_val = datetime.strptime(parts[2].strip(), "%A, %B %d, %Y at %I:%M:%S %p")
                    except ValueError:
                        pass

                photos.append(
                    PhotoInfo(
                        uuid=uuid,
                        filename=filename,
                        original_path=None,  # AppleScript doesn't give direct paths
                        date=date_val,
                        is_heic=ext in {".heic", ".heif"},
                        album=album,
                    )
                )
            return photos
        except Exception as e:
            if self._verbose:
                print(f"  AppleScript error: {e}")
            return []

    def _export_single_applescript(self, photo: PhotoInfo, dest_dir: Path) -> Optional[Path]:
        """Export a single photo via AppleScript (used when osxphotos path is unavailable)."""
        script = f'''
        tell application "Photos"
            set destFolder to POSIX file "{dest_dir}" as alias
            set thePhoto to media item id "{photo.uuid}"
            export {{thePhoto}} to destFolder
        end tell
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                if self._verbose:
                    print(f"  AppleScript export error: {result.stderr.strip()}")
                return None
            # Find the exported file
            exported = list(dest_dir.glob(f"{photo.filename}*"))
            if not exported:
                exported = list(dest_dir.glob(f"{Path(photo.filename).stem}*"))
            return exported[0] if exported else None
        except Exception as e:
            if self._verbose:
                print(f"  Export error: {e}")
            return None

    # ── Interactive picker ─────────────────────────────────────────────

    def _pick_album_applescript_dialog(self, albums: List[str]) -> Optional[str]:
        album_list = ", ".join(f'"{a}"' for a in albums)
        default = f'"{albums[0]}"' if albums else ""
        script = f'''
        choose from list {{{album_list}}} with title "Photo Processor" \
            with prompt "Select an album to export:" default items {{{default}}}
        '''
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0 or result.stdout.strip() == "false":
            return None
        return result.stdout.strip()

    def _pick_album_terminal(self, albums: List[str]) -> Optional[str]:
        print("\nAvailable albums:")
        for i, name in enumerate(albums, 1):
            print(f"  {i}. {name}")
        print()

        try:
            choice = input("Enter album number (or 'q' to cancel): ").strip()
            if choice.lower() == "q":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(albums):
                return albums[idx]
            print("Invalid selection.")
            return None
        except (ValueError, EOFError, KeyboardInterrupt):
            return None

    # ── Utilities ──────────────────────────────────────────────────────

    @staticmethod
    def _unique_path(path: Path) -> Path:
        """If path exists, append a counter to make it unique."""
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
