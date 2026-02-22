#!/usr/bin/env python3
"""
Parse all Miko's Lab PDFs and create a master knowledge base.
"""

import os
import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent.parent
PDFS_DIR = PROJECT_DIR / "pdfs"
OUTPUT_FILE = PROJECT_DIR / "KNOWLEDGE_BASE.md"

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        return f"[Error extracting: {e}]"

def clean_filename(filename: str) -> str:
    """Clean filename for use as section title."""
    # Remove extension and clean up
    name = filename.replace(".pdf", "")
    name = name.replace("_", " ").replace("(1)", "").replace("(2)", "")
    name = name.replace("  ", " ").strip()
    return name

def main():
    print("Parsing Miko's Lab PDFs...")
    
    pdf_files = list(PDFS_DIR.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDFs")
    
    # Build knowledge base
    kb = f"# Miko's Lab Master Knowledge Base\n\n"
    kb += f"*Auto-generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    kb += f"**Source:** {len(pdf_files)} PDFs from Miko's Lab Telegram\n\n"
    kb += "---\n\n"
    kb += "## Table of Contents\n\n"
    
    # Create TOC
    sections = []
    for pdf_file in sorted(pdf_files):
        title = clean_filename(pdf_file.name)
        anchor = title.lower().replace(" ", "-").replace("'", "").replace(":", "")
        kb += f"- [{title}](#{anchor})\n"
        sections.append((pdf_file, title, anchor))
    
    kb += "\n---\n\n"
    
    # Extract content from each PDF
    for pdf_file, title, anchor in sections:
        print(f"Processing: {pdf_file.name}")
        
        kb += f"## {title}\n\n"
        kb += f"*Source: {pdf_file.name}*\n\n"
        
        text = extract_text_from_pdf(pdf_file)
        
        if text and not text.startswith("[Error"):
            # Clean up the text
            lines = text.split("\n")
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if line and len(line) > 2:  # Skip very short lines
                    cleaned_lines.append(line)
            
            # Join and limit length per section
            content = "\n".join(cleaned_lines)
            
            # Truncate if too long but keep key info
            if len(content) > 15000:
                content = content[:15000] + "\n\n*[Content truncated - see original PDF for full text]*"
            
            kb += content
        else:
            kb += f"*{text}*"
        
        kb += "\n\n---\n\n"
    
    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(kb)
    
    print(f"\nKnowledge base saved to: {OUTPUT_FILE}")
    print(f"Total size: {len(kb):,} characters")

if __name__ == "__main__":
    main()
