#!/usr/bin/env python3
"""
Markdown to PDF Converter
Converts markdown files to professional PDFs with interactive table of contents.
"""

import argparse
import glob
import os
import re
import sys
from pathlib import Path

try:
    import markdown2
    from weasyprint import HTML, CSS
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print("\nPlease install dependencies:")
    print("  pip install markdown2 weasyprint pygments")
    sys.exit(1)


DEFAULT_CSS = """
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: 'Arial', 'Helvetica', sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}

h1 {
    font-size: 24pt;
    color: #2c3e50;
    margin-top: 0;
    page-break-before: avoid;
}

h2 {
    font-size: 18pt;
    color: #34495e;
    margin-top: 1.5em;
    page-break-after: avoid;
}

h3 {
    font-size: 14pt;
    color: #7f8c8d;
    margin-top: 1em;
}

h4, h5, h6 {
    font-size: 12pt;
    color: #95a5a6;
}

.toc {
    page-break-after: always;
    margin-bottom: 2em;
}

.toc h1 {
    text-align: center;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.5em;
}

.toc ul {
    list-style-type: none;
    padding-left: 0;
}

.toc li {
    margin: 0.5em 0;
    padding-left: 1em;
}

.toc li li {
    padding-left: 2em;
}

.toc li li li {
    padding-left: 3em;
}

.toc a {
    color: #3498db;
    text-decoration: none;
}

.toc a:hover {
    text-decoration: underline;
}

p {
    margin: 0.75em 0;
    text-align: justify;
}

code {
    background-color: #f4f4f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
}

pre {
    background-color: #2d2d2d;
    color: #f8f8f2;
    padding: 1em;
    border-radius: 5px;
    overflow-x: auto;
    margin: 1em 0;
}

pre code {
    background-color: transparent;
    padding: 0;
    color: inherit;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
}

th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

th {
    background-color: #34495e;
    color: white;
    font-weight: bold;
}

tr:nth-child(even) {
    background-color: #f9f9f9;
}

blockquote {
    border-left: 4px solid #3498db;
    padding-left: 1em;
    margin-left: 0;
    font-style: italic;
    color: #555;
}

ul, ol {
    margin: 0.75em 0;
    padding-left: 2em;
}

li {
    margin: 0.25em 0;
}

a {
    color: #3498db;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
}

hr {
    border: none;
    border-top: 2px solid #ecf0f1;
    margin: 2em 0;
}
"""


def extract_headers(md_content):
    """
    Extract headers from markdown content for TOC generation.

    Args:
        md_content (str): Markdown content

    Returns:
        list: List of dicts with 'level', 'text', and 'anchor' keys
    """
    headers = []
    header_pattern = r'^(#{1,6})\s+(.+)$'

    for line in md_content.split('\n'):
        match = re.match(header_pattern, line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()

            # Create anchor ID (lowercase, replace spaces with hyphens, remove special chars)
            anchor_id = text.lower()
            anchor_id = re.sub(r'[^\w\s-]', '', anchor_id)
            anchor_id = re.sub(r'[-\s]+', '-', anchor_id)

            headers.append({
                'level': level,
                'text': text,
                'anchor': anchor_id
            })

    return headers


def generate_toc(headers):
    """
    Generate HTML table of contents from headers.

    Args:
        headers (list): List of header dicts from extract_headers()

    Returns:
        str: HTML table of contents
    """
    if not headers:
        return ""

    toc_html = '<div class="toc">\n<h1>Table of Contents</h1>\n<ul>\n'

    for header in headers:
        # Indent based on header level
        indent = '  ' * (header['level'] - 1)
        link = f'<a href="#{header["anchor"]}">{header["text"]}</a>'
        toc_html += f'{indent}<li>{link}</li>\n'

    toc_html += '</ul>\n</div>\n'

    return toc_html


def markdown_to_html(md_content, headers):
    """
    Convert markdown to HTML with anchor tags for headers.

    Args:
        md_content (str): Markdown content
        headers (list): List of header dicts from extract_headers()

    Returns:
        str: HTML content
    """
    # Add anchor IDs to headers in markdown
    for header in headers:
        # Match the header line
        pattern = f"^({'#' * header['level']})\s+{re.escape(header['text'])}$"
        # Replace with header + anchor
        replacement = f"{'#' * header['level']} <a id='{header['anchor']}'></a>{header['text']}"
        md_content = re.sub(pattern, replacement, md_content, flags=re.MULTILINE)

    # Convert markdown to HTML
    html_content = markdown2.markdown(
        md_content,
        extras=[
            'fenced-code-blocks',
            'tables',
            'code-friendly',
            'cuddled-lists',
            'header-ids',
            'break-on-newline',
            'strike'
        ]
    )

    return html_content


def generate_pdf(md_content, output_path, css_content=None, include_toc=True):
    """
    Generate PDF from markdown content.

    Args:
        md_content (str): Markdown content
        output_path (str): Output PDF file path
        css_content (str): Optional CSS styling
        include_toc (bool): Whether to include table of contents
    """
    # Extract headers
    headers = extract_headers(md_content)

    # Generate TOC if requested
    toc_html = generate_toc(headers) if include_toc and headers else ""

    # Convert markdown to HTML
    content_html = markdown_to_html(md_content, headers)

    # Combine TOC + content
    full_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Document</title>
    </head>
    <body>
        {toc_html}
        {content_html}
    </body>
    </html>
    '''

    # Use provided CSS or default
    css = css_content if css_content else DEFAULT_CSS

    # Generate PDF
    try:
        html_obj = HTML(string=full_html)
        css_obj = CSS(string=css)

        html_obj.write_pdf(
            output_path,
            stylesheets=[css_obj],
            presentational_hints=True
        )

        print(f"✓ Generated: {output_path}")
        return True

    except Exception as e:
        print(f"✗ Error generating PDF: {e}", file=sys.stderr)
        return False


def batch_convert(input_pattern, output_dir, css_path=None, include_toc=True):
    """
    Convert multiple markdown files to PDF.

    Args:
        input_pattern (str): Glob pattern for input files
        output_dir (str): Output directory for PDFs
        css_path (str): Optional path to CSS file
        include_toc (bool): Whether to include table of contents
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load CSS if provided
    css_content = None
    if css_path:
        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
        except Exception as e:
            print(f"Warning: Could not load CSS file: {e}")

    # Find all markdown files
    md_files = glob.glob(input_pattern)

    if not md_files:
        print(f"No markdown files found matching: {input_pattern}")
        return 0

    success_count = 0

    for md_file in md_files:
        try:
            # Read markdown
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()

            # Generate output filename
            base_name = os.path.basename(md_file).replace('.md', '.pdf')
            output_path = os.path.join(output_dir, base_name)

            # Convert to PDF
            if generate_pdf(md_content, output_path, css_content, include_toc):
                success_count += 1

        except Exception as e:
            print(f"✗ Error processing {md_file}: {e}", file=sys.stderr)

    print(f"\n✓ Converted {success_count}/{len(md_files)} files to {output_dir}/")
    return success_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Convert markdown files to interactive PDFs with table of contents.'
    )

    parser.add_argument(
        'input',
        help='Input markdown file or glob pattern (e.g., "docs/*.md")'
    )

    parser.add_argument(
        'output',
        nargs='?',
        help='Output PDF file (for single file) or directory (for batch)'
    )

    parser.add_argument(
        '--css',
        help='Path to custom CSS file for styling'
    )

    parser.add_argument(
        '--no-toc',
        action='store_true',
        help='Disable table of contents generation'
    )

    parser.add_argument(
        '--output-dir',
        help='Output directory for batch conversion (alternative to positional output)'
    )

    args = parser.parse_args()

    # Determine if batch or single conversion
    is_batch = '*' in args.input or '?' in args.input

    # Load CSS if provided
    css_content = None
    if args.css:
        try:
            with open(args.css, 'r', encoding='utf-8') as f:
                css_content = f.read()
        except Exception as e:
            print(f"Error loading CSS: {e}", file=sys.stderr)
            sys.exit(1)

    if is_batch:
        # Batch conversion
        output_dir = args.output_dir or args.output or 'output'
        batch_convert(args.input, output_dir, args.css, not args.no_toc)

    else:
        # Single file conversion
        if not args.output:
            # Auto-generate output filename
            args.output = args.input.replace('.md', '.pdf')

        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                md_content = f.read()

            generate_pdf(md_content, args.output, css_content, not args.no_toc)

        except FileNotFoundError:
            print(f"Error: File not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
