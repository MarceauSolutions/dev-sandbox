#!/usr/bin/env python3
"""
Memory Consolidation System
Scans, audits, and maintains Claude Code memory files.

Usage:
    python execution/memory_consolidator.py [--report|--fix|--compact]

Flags:
    --report   (default) Analyze memory health without changes
    --fix      Auto-fix orphans and broken links
    --compact  Rewrite MEMORY.md to save space (remove extra blank lines)
"""

import os
import re
import sys
from collections import defaultdict
from datetime import datetime, date
from pathlib import Path

MEMORY_DIR = Path(
    os.path.expanduser(
        "~/.claude/projects/-Users-williammarceaujr--dev-sandbox/memory"
    )
)
MEMORY_MD = MEMORY_DIR / "MEMORY.md"
LINE_LIMIT = 200


def parse_frontmatter(filepath: Path) -> dict:
    """Extract frontmatter (---/---) from a memory file."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return {}
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    meta = {}
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()
    return meta


def categorize_file(filename: str, meta: dict) -> str:
    """Categorize a memory file by its type or prefix."""
    ftype = meta.get("type", "").lower()
    if ftype:
        category_map = {
            "user": "user",
            "feedback": "feedback",
            "project": "project",
            "reference": "reference",
        }
        return category_map.get(ftype, ftype)
    # Fall back to prefix
    for prefix in ("user_", "feedback_", "project_"):
        if filename.startswith(prefix):
            return prefix.rstrip("_")
    return "unknown"


def extract_links_from_memory_md(text: str) -> set:
    """Find all .md file links in MEMORY.md (both [text](file.md) and `memory/file.md`)."""
    links = set()
    # Markdown links: [text](file.md) — relative links in the memory dir
    for match in re.finditer(r"\[([^\]]*)\]\(([^)]+\.md)\)", text):
        target = match.group(2)
        # Skip external/absolute links
        if target.startswith("http") or target.startswith("/"):
            continue
        # Strip any path prefix like memory/ since MEMORY.md is in the memory dir
        basename = os.path.basename(target)
        links.add(basename)
    # Also catch backtick references like `memory/file.md`
    for match in re.finditer(r"`memory/([^`]+\.md)`", text):
        links.add(match.group(1))
    return links


def significant_words(text: str) -> set:
    """Extract significant words from text for duplicate detection."""
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "both", "each", "few", "more", "most", "other",
        "some", "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "just", "because", "but", "and", "or", "if",
        "while", "this", "that", "these", "those", "it", "its", "he", "she",
        "they", "them", "his", "her", "we", "you", "i", "me", "my", "your",
        "our", "their", "what", "which", "who", "whom",
        # Common markdown/code words
        "md", "see", "use", "run", "set", "get", "new", "add", "also",
        "must", "never", "always", "every", "file", "check",
    }
    words = set(re.findall(r"[a-z]{3,}", text.lower()))
    return words - stopwords


def extract_dates(text: str) -> list:
    """Extract dates from text in common formats."""
    dates = []
    # Match patterns like "April 6, 2026" or "March 23 - April 5"
    for match in re.finditer(
        r"(January|February|March|April|May|June|July|August|September|"
        r"October|November|December)\s+(\d{1,2}),?\s+(\d{4})", text
    ):
        month_str, day, year = match.group(1), int(match.group(2)), int(match.group(3))
        months = {
            "January": 1, "February": 2, "March": 3, "April": 4,
            "May": 5, "June": 6, "July": 7, "August": 8,
            "September": 9, "October": 10, "November": 11, "December": 12,
        }
        try:
            dates.append(date(year, months[month_str], day))
        except ValueError:
            pass
    # Match YYYY-MM-DD
    for match in re.finditer(r"(\d{4})-(\d{2})-(\d{2})", text):
        try:
            dates.append(date(int(match.group(1)), int(match.group(2)), int(match.group(3))))
        except ValueError:
            pass
    # Match "Mar 23" style with year context
    for match in re.finditer(
        r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})", text
    ):
        abbrevs = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
        }
        # Try to find a year nearby in the text
        year_match = re.search(r"20\d{2}", text)
        if year_match:
            try:
                dates.append(
                    date(int(year_match.group()), abbrevs[match.group(1)], int(match.group(2)))
                )
            except ValueError:
                pass
    return dates


def check_staleness(filepath: Path, today: date) -> bool:
    """Check if a project memory file references dates that have all passed."""
    if not filepath.name.startswith("project_"):
        return False
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return False
    dates = extract_dates(text)
    if not dates:
        return False
    # Stale if ALL referenced dates are in the past
    return all(d < today for d in dates)


def find_duplicates(file_words: dict) -> list:
    """Find pairs of files with 50%+ significant word overlap."""
    duplicates = []
    files = list(file_words.keys())
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            f1, f2 = files[i], files[j]
            w1, w2 = file_words[f1], file_words[f2]
            if not w1 or not w2:
                continue
            overlap = w1 & w2
            smaller = min(len(w1), len(w2))
            if smaller > 0 and len(overlap) / smaller >= 0.50:
                duplicates.append((f1, f2, overlap))
    return duplicates


def compact_memory_md(text: str) -> str:
    """Remove excessive blank lines and trailing whitespace to save space."""
    lines = text.split("\n")
    result = []
    prev_blank = False
    for line in lines:
        stripped = line.rstrip()
        is_blank = stripped == ""
        # Collapse multiple blank lines into one
        if is_blank and prev_blank:
            continue
        result.append(stripped)
        prev_blank = is_blank
    # Remove trailing blank line
    while result and result[-1] == "":
        result.pop()
    return "\n".join(result) + "\n"


def add_orphans_to_memory_md(text: str, orphans: list, file_meta: dict) -> str:
    """Add orphaned files to MEMORY.md at the end."""
    if not orphans:
        return text
    additions = ["\n## Unlinked Memory Files (auto-added)"]
    for orphan in sorted(orphans):
        meta = file_meta.get(orphan, {})
        desc = meta.get("description", "No description")
        ftype = meta.get("type", "unknown")
        additions.append(f"- [{orphan}]({orphan}) — ({ftype}) {desc}")
    return text.rstrip("\n") + "\n" + "\n".join(additions) + "\n"


def remove_broken_links(text: str, broken: set) -> str:
    """Remove lines containing broken links from MEMORY.md."""
    if not broken:
        return text
    lines = text.split("\n")
    result = []
    removed = 0
    for line in lines:
        has_broken = False
        for b in broken:
            if f"]({b})" in line or f"({b})" in line:
                has_broken = True
                break
        if has_broken:
            removed += 1
        else:
            result.append(line)
    print(f"  Removed {removed} lines with broken links")
    return "\n".join(result)


def run_report(fix: bool = False, compact: bool = False):
    """Main analysis and optional fix logic."""
    if not MEMORY_MD.exists():
        print(f"ERROR: MEMORY.md not found at {MEMORY_MD}")
        sys.exit(1)

    memory_text = MEMORY_MD.read_text(encoding="utf-8")
    memory_lines = memory_text.split("\n")
    line_count = len(memory_lines)
    # Don't count trailing empty line
    if memory_lines and memory_lines[-1] == "":
        line_count -= 1

    capacity_pct = round(line_count / LINE_LIMIT * 100)

    # Scan all .md files in the memory directory (excluding MEMORY.md itself)
    all_files = sorted(
        f.name for f in MEMORY_DIR.iterdir()
        if f.suffix == ".md" and f.name != "MEMORY.md"
    )

    # Parse frontmatter for each file
    file_meta = {}
    file_words = {}
    for fname in all_files:
        fpath = MEMORY_DIR / fname
        file_meta[fname] = parse_frontmatter(fpath)
        try:
            content = fpath.read_text(encoding="utf-8")
            file_words[fname] = significant_words(content)
        except Exception:
            file_words[fname] = set()

    # Categorize files
    categories = defaultdict(list)
    for fname in all_files:
        cat = categorize_file(fname, file_meta.get(fname, {}))
        categories[cat].append(fname)

    # Find links in MEMORY.md
    linked_files = extract_links_from_memory_md(memory_text)

    # Orphans: files that exist but aren't linked
    orphans = [f for f in all_files if f not in linked_files]

    # Broken links: referenced but don't exist
    broken_links = {f for f in linked_files if f not in all_files and f != "MEMORY.md"}

    # Duplicates
    duplicates = find_duplicates(file_words)

    # Stale project files
    today = date.today()
    stale_files = [f for f in all_files if check_staleness(MEMORY_DIR / f, today)]

    # === Print Report ===
    print("=" * 50)
    print("  Memory Consolidation Report")
    print("=" * 50)
    print()
    print(f"MEMORY.md: {line_count}/{LINE_LIMIT} lines ({capacity_pct}% capacity)")
    print()

    print(f"Memory Files ({len(all_files)} total):")
    for cat in sorted(categories.keys()):
        files = categories[cat]
        print(f"  {cat + '/':12s}: {len(files)} files")
    print()

    issues = []

    for sf in stale_files:
        issues.append(f"  STALE: {sf} -- references dates that have passed")

    for f1, f2, overlap in duplicates:
        shared = ", ".join(sorted(overlap)[:5])
        issues.append(f"  DUPLICATE: {f1} and {f2} share significant overlap ({shared}...)")

    for orphan in orphans:
        issues.append(f"  ORPHAN: {orphan} -- not linked in MEMORY.md")

    for broken in sorted(broken_links):
        issues.append(f"  BROKEN LINK: MEMORY.md references \"{broken}\" but file doesn't exist")

    if capacity_pct >= 80:
        issues.append(f"  CAPACITY: MEMORY.md at {capacity_pct}% -- consider consolidating entries")

    if issues:
        print("Potential Issues:")
        for issue in issues:
            print(issue)
        print()
    else:
        print("No issues found. Memory system is healthy.")
        print()

    # Recommendations
    recs = []
    if duplicates:
        for f1, f2, _ in duplicates:
            recs.append(f"Merge {f1} + {f2}")
    if stale_files:
        for sf in stale_files:
            recs.append(f"Review {sf} for staleness (dates have passed)")
    if orphans:
        recs.append(f"Add {len(orphans)} orphan file(s) to MEMORY.md or delete if irrelevant")
    if broken_links:
        recs.append(f"Remove {len(broken_links)} broken link(s) from MEMORY.md")
    if capacity_pct >= 90:
        recs.append("MEMORY.md near limit -- compact or consolidate sections")

    if recs:
        print("Recommendations:")
        for i, rec in enumerate(recs, 1):
            print(f"  {i}. {rec}")
        print()

    print("=" * 50)

    # === Fix Mode ===
    if fix:
        print()
        print("Applying fixes...")
        modified = memory_text

        if orphans:
            print(f"  Adding {len(orphans)} orphan(s) to MEMORY.md")
            modified = add_orphans_to_memory_md(modified, orphans, file_meta)

        if broken_links:
            print(f"  Removing {len(broken_links)} broken link(s) from MEMORY.md")
            modified = remove_broken_links(modified, broken_links)

        if modified != memory_text:
            MEMORY_MD.write_text(modified, encoding="utf-8")
            new_count = len(modified.split("\n"))
            if modified.endswith("\n"):
                new_count -= 1
            print(f"  MEMORY.md updated: {line_count} -> {new_count} lines")
        else:
            print("  No fixable issues found.")

        if duplicates:
            print()
            print("  NOTE: Duplicate merges require human judgment -- not auto-applied.")
            for f1, f2, _ in duplicates:
                print(f"    Review: {f1} + {f2}")

    # === Compact Mode ===
    if compact:
        print()
        print("Compacting MEMORY.md...")
        source = MEMORY_MD.read_text(encoding="utf-8")
        compacted = compact_memory_md(source)
        old_lines = len(source.split("\n"))
        new_lines = len(compacted.split("\n"))
        if source.endswith("\n"):
            old_lines -= 1
        if compacted.endswith("\n"):
            new_lines -= 1
        if old_lines != new_lines:
            MEMORY_MD.write_text(compacted, encoding="utf-8")
            print(f"  Compacted: {old_lines} -> {new_lines} lines (saved {old_lines - new_lines})")
        else:
            print("  Already compact -- no changes needed.")


def main():
    args = sys.argv[1:]
    fix = "--fix" in args
    compact = "--compact" in args

    if not args or "--report" in args:
        # Report is always shown
        pass

    run_report(fix=fix, compact=compact)


if __name__ == "__main__":
    main()
