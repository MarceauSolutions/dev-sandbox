#!/usr/bin/env python3
"""
Markdown to PDF Converter
Converts markdown files to professionally formatted PDF documents.

Features:
- Professional styling with custom CSS
- Table of contents generation
- Syntax highlighting for code blocks
- Page numbers and metadata
- Batch conversion support

Usage:
    # Single file
    python markdown_to_pdf.py --input file.md --output file.pdf

    # With custom title
    python markdown_to_pdf.py --input file.md --output file.pdf --title "My Document"

    # Batch conversion
    python markdown_to_pdf.py --batch "docs/sessions/*.md" --output-dir pdfs/

    # Without table of contents
    python markdown_to_pdf.py --input file.md --output file.pdf --no-toc

Requirements:
    pip install markdown-pdf markdown pygments
"""

import argparse
import os
import sys
import glob
from pathlib import Path
from datetime import datetime

try:
    from markdown_pdf import MarkdownPdf, Section
    import markdown
except ImportError:
    print("ERROR: Required libraries not installed")
    print("Install with: pip install markdown-pdf markdown pygments")
    sys.exit(1)


class MarkdownToPDF:
    """
    Markdown to PDF converter with professional styling.
    """

    def __init__(self, css_file=None, author="Marceau Solutions"):
        """
        Initialize converter.

        Args:
            css_file: Path to custom CSS file (uses default if None)
            author: Document author name
        """
        self.author = author
        self.css = self._load_css(css_file)

    def _load_css(self, css_file=None):
        """
        Load CSS stylesheet.

        Args:
            css_file: Path to custom CSS file

        Returns:
            CSS string
        """
        if css_file and os.path.exists(css_file):
            # Load custom CSS
            with open(css_file, 'r') as f:
                return f.read()
        else:
            # Load default CSS
            default_css = Path(__file__).parent / 'styles' / 'default_pdf.css'
            if default_css.exists():
                with open(default_css, 'r') as f:
                    return f.read()
            else:
                # Fallback to basic CSS if default doesn't exist
                return self._get_fallback_css()

    def _get_fallback_css(self):
        """Return basic fallback CSS if no stylesheet found."""
        return """
        body { font-family: Georgia, serif; font-size: 11pt; line-height: 1.6; color: #333; }
        h1 { font-size: 24pt; font-weight: bold; color: #2c3e50; margin-top: 20pt; }
        h2 { font-size: 20pt; font-weight: bold; color: #34495e; margin-top: 16pt; }
        h3 { font-size: 16pt; font-weight: bold; color: #34495e; margin-top: 12pt; }
        code { font-family: monospace; background-color: #f4f4f4; padding: 2pt 4pt; }
        pre { background-color: #f8f8f8; border: 1px solid #ddd; padding: 10pt; }
        table { border-collapse: collapse; width: 100%; }
        th { background-color: #3498db; color: white; padding: 8pt; }
        td { padding: 6pt 8pt; border: 1px solid #ccc; }
        blockquote { border-left: 4px solid #3498db; padding-left: 15pt; color: #555; }
        """

    def _extract_title_from_markdown(self, markdown_content):
        """
        Extract title from first H1 header in markdown.

        Args:
            markdown_content: Markdown text

        Returns:
            Title string or None
        """
        for line in markdown_content.split('\n'):
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return None

    def _remove_front_matter(self, markdown_content):
        """
        Remove YAML front matter from markdown if present.

        Args:
            markdown_content: Markdown text

        Returns:
            Markdown without front matter
        """
        lines = markdown_content.split('\n')
        if lines and lines[0].strip() == '---':
            # Find end of front matter
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    # Return content after front matter
                    return '\n'.join(lines[i+1:])
        return markdown_content

    def convert(self, input_file, output_file, title=None, include_toc=True, page_numbers=True):
        """
        Convert a markdown file to PDF.

        Args:
            input_file: Path to input markdown file
            output_file: Path to output PDF file
            title: Document title (auto-detected from H1 if None)
            include_toc: Include table of contents
            page_numbers: Include page numbers

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\n→ Converting {input_file} to PDF...")

            # Read markdown file
            with open(input_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # Remove front matter if present
            markdown_content = self._remove_front_matter(markdown_content)

            # Extract title if not provided
            if not title:
                title = self._extract_title_from_markdown(markdown_content)
                if not title:
                    # Use filename as title
                    title = Path(input_file).stem.replace('-', ' ').replace('_', ' ').title()

            print(f"  Title: {title}")

            # Create PDF generator
            pdf = MarkdownPdf(toc_level=2 if include_toc else 0)

            # Set metadata
            pdf.meta = {
                'title': title,
                'author': self.author,
                'subject': f'Generated from {Path(input_file).name}',
                'creator': 'Marceau Solutions PDF Generator',
            }

            # Add content section
            pdf.add_section(
                Section(markdown_content, toc=include_toc),
                user_css=self.css
            )

            # Ensure output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save PDF
            pdf.save(str(output_path))

            print(f"  ✓ PDF created: {output_file}")
            return True

        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            return False

    def batch_convert(self, pattern, output_dir, include_toc=True):
        """
        Batch convert multiple markdown files.

        Args:
            pattern: Glob pattern for markdown files (e.g., "docs/*.md")
            output_dir: Directory for output PDFs
            include_toc: Include table of contents

        Returns:
            Number of files successfully converted
        """
        # Find all matching files
        files = glob.glob(pattern)

        if not files:
            print(f"No files found matching pattern: {pattern}")
            return 0

        print(f"\n→ Found {len(files)} markdown files to convert")

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Convert each file
        success_count = 0
        for input_file in files:
            # Generate output filename
            filename = Path(input_file).stem + '.pdf'
            output_file = Path(output_dir) / filename

            # Convert
            if self.convert(input_file, str(output_file), include_toc=include_toc):
                success_count += 1

        print(f"\n✓ Successfully converted {success_count} of {len(files)} files")
        return success_count


def main():
    """CLI for markdown to PDF conversion."""
    parser = argparse.ArgumentParser(
        description='Convert markdown files to professionally formatted PDFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file
  python markdown_to_pdf.py --input README.md --output README.pdf

  # With custom title and author
  python markdown_to_pdf.py --input docs/setup.md --output setup.pdf \\
    --title "Setup Guide" --author "William Marceau"

  # Batch convert all session notes
  python markdown_to_pdf.py --batch "docs/sessions/*.md" \\
    --output-dir docs/sessions/pdfs/

  # Without table of contents
  python markdown_to_pdf.py --input file.md --output file.pdf --no-toc

  # Custom CSS styling
  python markdown_to_pdf.py --input file.md --output file.pdf \\
    --css custom_styles.css
        """
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', '-i', help='Input markdown file')
    input_group.add_argument('--batch', '-b', help='Batch convert using glob pattern (e.g., "docs/*.md")')

    # Output options
    parser.add_argument('--output', '-o', help='Output PDF file (required for single file conversion)')
    parser.add_argument('--output-dir', '-d', help='Output directory (required for batch conversion)')

    # Metadata options
    parser.add_argument('--title', '-t', help='Document title (auto-detected if not provided)')
    parser.add_argument('--author', '-a', default='Marceau Solutions', help='Document author (default: Marceau Solutions)')

    # Formatting options
    parser.add_argument('--css', help='Custom CSS file for styling')
    parser.add_argument('--no-toc', action='store_true', help='Disable table of contents')
    parser.add_argument('--no-page-numbers', action='store_true', help='Disable page numbers')

    args = parser.parse_args()

    # Validate arguments
    if args.input and not args.output:
        parser.error("--output is required when using --input")
    if args.batch and not args.output_dir:
        parser.error("--output-dir is required when using --batch")

    # Create converter
    converter = MarkdownToPDF(css_file=args.css, author=args.author)

    # Convert
    if args.input:
        # Single file conversion
        success = converter.convert(
            input_file=args.input,
            output_file=args.output,
            title=args.title,
            include_toc=not args.no_toc,
            page_numbers=not args.no_page_numbers
        )
        sys.exit(0 if success else 1)
    else:
        # Batch conversion
        count = converter.batch_convert(
            pattern=args.batch,
            output_dir=args.output_dir,
            include_toc=not args.no_toc
        )
        sys.exit(0 if count > 0 else 1)


if __name__ == '__main__':
    main()
