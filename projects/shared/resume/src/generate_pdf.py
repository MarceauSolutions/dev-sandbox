#!/usr/bin/env python3
"""
Generate PDF from Markdown resume/cover letter.
Uses markdown2 + weasyprint for conversion.
"""

import sys
import argparse
from pathlib import Path
import markdown2
from weasyprint import HTML, CSS

# Professional resume styling
RESUME_CSS = """
@page {
    margin: 0.75in;
    size: letter;
}

body {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.4;
    color: #333;
}

h1 {
    font-size: 22pt;
    margin-bottom: 5px;
    color: #1a1a1a;
    border-bottom: 2px solid #2c5282;
    padding-bottom: 5px;
}

h2 {
    font-size: 13pt;
    color: #2c5282;
    margin-top: 15px;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 3px;
}

h3 {
    font-size: 11pt;
    margin-top: 10px;
    margin-bottom: 3px;
    color: #1a1a1a;
}

p {
    margin: 5px 0;
}

ul {
    margin: 5px 0;
    padding-left: 20px;
}

li {
    margin-bottom: 3px;
}

strong {
    color: #1a1a1a;
}

hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 10px 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
}

th, td {
    padding: 5px 10px;
    text-align: left;
    border-bottom: 1px solid #e2e8f0;
}

a {
    color: #2c5282;
    text-decoration: none;
}
"""

COVER_LETTER_CSS = """
@page {
    margin: 1in;
    size: letter;
}

body {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}

h1 {
    font-size: 18pt;
    margin-bottom: 20px;
    color: #1a1a1a;
}

p {
    margin: 12px 0;
}

strong {
    color: #1a1a1a;
}

hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 15px 0;
}

ul {
    margin: 10px 0;
    padding-left: 25px;
}

li {
    margin-bottom: 5px;
}
"""


def markdown_to_pdf(input_path: str, output_path: str = None, doc_type: str = "resume"):
    """Convert markdown file to PDF."""
    input_file = Path(input_path)
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Determine output path
    if output_path is None:
        output_path = input_file.with_suffix('.pdf')
    
    # Read markdown
    md_content = input_file.read_text(encoding='utf-8')
    
    # Convert to HTML
    html_content = markdown2.markdown(md_content, extras=['tables', 'fenced-code-blocks'])
    
    # Wrap in full HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Select CSS based on document type
    css = RESUME_CSS if doc_type == "resume" else COVER_LETTER_CSS
    
    # Generate PDF
    HTML(string=full_html).write_pdf(
        output_path,
        stylesheets=[CSS(string=css)]
    )
    
    print(f"Generated: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description='Generate PDF from Markdown resume/cover letter')
    parser.add_argument('input', help='Input markdown file')
    parser.add_argument('-o', '--output', help='Output PDF path (default: same name as input)')
    parser.add_argument('-t', '--type', choices=['resume', 'cover'], default='resume',
                        help='Document type for styling (default: resume)')
    
    args = parser.parse_args()
    markdown_to_pdf(args.input, args.output, args.type)


if __name__ == '__main__':
    main()
