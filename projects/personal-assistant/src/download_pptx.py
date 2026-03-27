#!/usr/bin/env python3
"""
Download PowerPoint to User's Downloads Folder

Copies the working presentation to the user's Downloads folder
with a clean filename, ready for use.

Usage:
    python download_pptx.py --input .tmp/interview_prep_company.pptx
    python download_pptx.py --input .tmp/interview_prep_company.pptx --format pdf
    python download_pptx.py --input .tmp/interview_prep_company.pptx --name "My Interview Prep"
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def get_downloads_folder() -> Path:
    """Get the user's Downloads folder."""
    return Path.home() / "Downloads"


def sanitize_filename(name: str) -> str:
    """Remove invalid characters from filename."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '')
    return name.strip()


def copy_to_downloads(input_path: str, custom_name: str = None) -> dict:
    """Copy the PPTX file to Downloads folder."""
    src = Path(input_path)
    if not src.exists():
        return {"success": False, "error": f"File not found: {input_path}"}

    downloads = get_downloads_folder()

    # Generate filename
    if custom_name:
        filename = sanitize_filename(custom_name)
        if not filename.endswith('.pptx'):
            filename += '.pptx'
    else:
        # Use original name with timestamp
        base_name = src.stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{base_name}_{timestamp}.pptx"

    dest = downloads / filename

    # Handle existing file
    if dest.exists():
        counter = 1
        while dest.exists():
            name_part = filename.rsplit('.', 1)[0]
            dest = downloads / f"{name_part}_{counter}.pptx"
            counter += 1

    try:
        shutil.copy(src, dest)
        return {
            "success": True,
            "source": str(src),
            "destination": str(dest),
            "filename": dest.name
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def export_to_pdf(input_path: str, custom_name: str = None) -> dict:
    """
    Export PowerPoint to PDF.
    Uses LibreOffice if available, otherwise instructs user.
    """
    src = Path(input_path)
    if not src.exists():
        return {"success": False, "error": f"File not found: {input_path}"}

    downloads = get_downloads_folder()

    # Generate filename
    if custom_name:
        filename = sanitize_filename(custom_name)
        if not filename.endswith('.pdf'):
            filename += '.pdf'
    else:
        base_name = src.stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{base_name}_{timestamp}.pdf"

    dest = downloads / filename

    # Try using LibreOffice for conversion
    try:
        result = subprocess.run(
            ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', str(downloads), str(src)],
            capture_output=True,
            timeout=60
        )

        # LibreOffice outputs with original filename, rename if needed
        converted = downloads / f"{src.stem}.pdf"
        if converted.exists() and converted != dest:
            shutil.move(converted, dest)

        if dest.exists():
            return {
                "success": True,
                "source": str(src),
                "destination": str(dest),
                "filename": dest.name,
                "method": "libreoffice"
            }
    except FileNotFoundError:
        pass  # LibreOffice not installed
    except subprocess.TimeoutExpired:
        pass  # Conversion took too long

    # Fallback: Copy PPTX and provide instructions
    pptx_result = copy_to_downloads(input_path, custom_name)
    if pptx_result["success"]:
        return {
            "success": True,
            "source": str(src),
            "destination": pptx_result["destination"],
            "filename": pptx_result["filename"],
            "method": "pptx_copy",
            "note": "PDF conversion requires LibreOffice or opening in PowerPoint and exporting manually"
        }

    return {"success": False, "error": "Could not export to PDF"}


def main():
    parser = argparse.ArgumentParser(
        description="Download PowerPoint to Downloads folder"
    )
    parser.add_argument("--input", "-i", required=True, help="Input PowerPoint file")
    parser.add_argument("--name", "-n", help="Custom filename (without extension)")
    parser.add_argument("--format", "-f", choices=["pptx", "pdf"], default="pptx",
                        help="Output format (default: pptx)")
    parser.add_argument("--open", action="store_true", help="Open file after download")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"Downloading Presentation")
    print(f"{'='*60}\n")

    if args.format == "pdf":
        result = export_to_pdf(args.input, args.name)
    else:
        result = copy_to_downloads(args.input, args.name)

    if result.get("success"):
        print(f"✅ Downloaded successfully!")
        print(f"   📁 Location: {result['destination']}")
        print(f"   📄 Filename: {result['filename']}")

        if result.get("note"):
            print(f"\n💡 Note: {result['note']}")

        if args.open:
            subprocess.run(["open", result["destination"]], check=False)
            print(f"\n📂 Opened in default application")
    else:
        print(f"❌ Error: {result.get('error')}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
