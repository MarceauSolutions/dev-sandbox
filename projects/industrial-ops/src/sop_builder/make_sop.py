#!/usr/bin/env python3
"""
make_sop.py — End-to-end SOP creation wrapper.

Pipeline: Drive folder → OCR → Claude structuring → PDF → deliver to Telegram.

Designed to be invoked by `claude -p` on EC2 (Panacea) when William asks via Telegram:
    "Make me an SOP from the Front Desk Notes folder, number it WW-SOP-001"

Usage:
    python3 projects/industrial-ops/src/sop_builder/make_sop.py \\
        --gdrive-folder "SOP-Front-Desk-Notes" \\
        --sop-number WW-SOP-001 \\
        --title "Front Desk Agent Daily Procedures" \\
        --deliver

If --deliver is set, the PDF is sent to William's Telegram chat after generation.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--gdrive-folder", required=True, help="Drive folder name with scanned notes")
    parser.add_argument("--sop-number", required=True, help="SOP number (e.g. WW-SOP-001)")
    parser.add_argument("--title", required=True, help="SOP title")
    parser.add_argument("--department", default="Wastewater Operations")
    parser.add_argument("--prepared-by", default="William Marceau, I&E Technician")
    parser.add_argument("--approved-by", default="[Supervisor Name]")
    parser.add_argument("--output-dir", default=str(REPO_ROOT / "projects/industrial-ops/data/output"))
    parser.add_argument("--deliver", action="store_true", help="Send the generated PDF to William's Telegram chat")
    parser.add_argument("--chat-id", help="Override Telegram chat ID (default: William)")
    args = parser.parse_args()

    sop_generator = REPO_ROOT / "projects/industrial-ops/src/sop_builder/sop_generator.py"
    telegram_send = REPO_ROOT / "execution/telegram_send_file.py"
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Run the SOP generator with --gdrive-folder mode
    cmd = [
        sys.executable, str(sop_generator),
        "--gdrive-folder", args.gdrive_folder,
        "--sop-number", args.sop_number,
        "--title", args.title,
        "--department", args.department,
        "--prepared-by", args.prepared_by,
        "--approved-by", args.approved_by,
        "--output-dir", str(output_dir),
    ]
    print(f"→ Generating SOP: {' '.join(cmd[1:])}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    if result.returncode != 0:
        sys.exit(f"\nERROR: sop_generator failed (exit {result.returncode}).")

    # Step 2: Find the produced PDF
    pdf_path = None
    for line in result.stdout.splitlines():
        if line.strip().startswith("PDF:"):
            pdf_path = Path(line.split(":", 1)[1].strip())
            break
    if not pdf_path or not pdf_path.exists():
        sys.exit("ERROR: Could not locate produced PDF path.")

    print(f"\n✓ SOP generated: {pdf_path}")

    # Step 3: Deliver via Telegram if requested
    if args.deliver:
        send_cmd = [
            sys.executable, str(telegram_send),
            "--file", str(pdf_path),
            "--caption", f"{args.sop_number} — {args.title}",
        ]
        if args.chat_id:
            send_cmd.extend(["--chat-id", args.chat_id])
        print(f"→ Sending to Telegram...")
        send_result = subprocess.run(send_cmd, capture_output=True, text=True)
        sys.stdout.write(send_result.stdout)
        sys.stderr.write(send_result.stderr)
        if send_result.returncode != 0:
            sys.exit(f"ERROR: telegram_send_file failed (exit {send_result.returncode}).")


if __name__ == "__main__":
    main()
