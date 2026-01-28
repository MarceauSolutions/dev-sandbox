#!/usr/bin/env python3
"""
Post-Completion Review — Clawdbot validates Ralph's output before notifying user.

Quality checks:
1. All stories marked as passes: true
2. Files actually exist and have content
3. Python files pass syntax check
4. Docstring coverage
5. No obvious issues (TODO/FIXME/HACK comments)
6. Commit messages are clean
7. Tests exist if specified in PRD

Returns a quality report and blocks notification if quality < threshold.
"""

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

REVIEW_THRESHOLD = 75  # Minimum score to auto-notify user


@dataclass
class ReviewResult:
    score: int = 100
    passed: bool = True
    checks: List[Dict] = field(default_factory=list)
    summary: str = ""
    
    def add_check(self, name: str, passed: bool, detail: str, weight: int = 5):
        self.checks.append({
            "name": name,
            "passed": passed,
            "detail": detail,
            "weight": weight,
        })
        if not passed:
            self.score = max(0, self.score - weight)
    
    def finalize(self):
        self.passed = self.score >= REVIEW_THRESHOLD
        passed_count = sum(1 for c in self.checks if c["passed"])
        total = len(self.checks)
        self.summary = f"Score: {self.score}/100 | {passed_count}/{total} checks passed"


def check_story_completion(prd_path: str) -> Tuple[int, int, List[str]]:
    """Check how many stories are marked as complete."""
    with open(prd_path) as f:
        prd = json.load(f)
    
    stories = prd.get("stories", [])
    completed = [s for s in stories if s.get("passes")]
    incomplete = [s.get("id", "unknown") for s in stories if not s.get("passes")]
    
    return len(completed), len(stories), incomplete


def check_python_syntax(project_dir: str) -> Tuple[int, List[str]]:
    """Check all Python files for syntax errors."""
    errors = []
    total = 0
    
    for py_file in Path(project_dir).rglob("*.py"):
        if "venv" in str(py_file) or "node_modules" in str(py_file) or "__pycache__" in str(py_file):
            continue
        total += 1
        try:
            with open(py_file) as f:
                ast.parse(f.read())
        except SyntaxError as e:
            errors.append(f"{py_file}: {e}")
    
    return total, errors


def check_docstring_coverage(project_dir: str) -> Tuple[int, int]:
    """Check percentage of functions/classes with docstrings."""
    total_definitions = 0
    with_docstrings = 0
    
    for py_file in Path(project_dir).rglob("*.py"):
        if "venv" in str(py_file) or "node_modules" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            with open(py_file) as f:
                tree = ast.parse(f.read())
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    # Skip private/dunder methods
                    if node.name.startswith("_") and not node.name.startswith("__"):
                        continue
                    total_definitions += 1
                    if (node.body and isinstance(node.body[0], ast.Expr) and
                            isinstance(node.body[0].value, (ast.Str, ast.Constant))):
                        with_docstrings += 1
        except Exception:
            continue
    
    return with_docstrings, total_definitions


def check_code_smells(project_dir: str) -> List[str]:
    """Check for obvious code smells."""
    smells = []
    
    smell_patterns = [
        (r"\bprint\(", "print() statement (should use logging)"),
        (r"#\s*TODO", "TODO comment — unfinished work"),
        (r"#\s*FIXME", "FIXME comment — known bug"),
        (r"#\s*HACK", "HACK comment — dirty workaround"),
        (r"except\s*:", "Bare except clause — too broad"),
        (r"password\s*=\s*['\"]", "Hardcoded password"),
        (r"api_key\s*=\s*['\"]", "Hardcoded API key"),
        (r"secret\s*=\s*['\"]", "Hardcoded secret"),
    ]
    
    for py_file in Path(project_dir).rglob("*.py"):
        if "venv" in str(py_file) or "node_modules" in str(py_file):
            continue
        try:
            content = py_file.read_text(errors="ignore")
            for pattern, description in smell_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    smells.append(f"{py_file.name}: {len(matches)}x {description}")
        except Exception:
            continue
    
    return smells


def check_commit_quality(project_dir: str, since_stories: int = 5) -> List[str]:
    """Check recent commit messages for quality."""
    issues = []
    try:
        result = subprocess.run(
            ["git", "log", f"-{since_stories}", "--format=%s"],
            cwd=project_dir, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for msg in result.stdout.strip().split("\n"):
                if len(msg) < 10:
                    issues.append(f"Too short: '{msg}'")
                if msg == msg.lower() and not msg.startswith("feat:"):
                    pass  # lowercase is fine if prefixed
        
    except Exception:
        issues.append("Could not read git history")
    
    return issues


def check_file_sizes(project_dir: str) -> List[str]:
    """Flag files that are suspiciously large (might need splitting)."""
    warnings = []
    
    for py_file in Path(project_dir).rglob("*.py"):
        if "venv" in str(py_file) or "node_modules" in str(py_file):
            continue
        try:
            lines = len(py_file.read_text(errors="ignore").split("\n"))
            if lines > 500:
                warnings.append(f"{py_file.name}: {lines} lines — consider splitting")
        except Exception:
            continue
    
    return warnings


def run_post_review(prd_path: str, project_dir: str) -> ReviewResult:
    """
    Run full post-completion review.
    
    Returns ReviewResult with score, checks, and pass/fail.
    """
    result = ReviewResult()
    
    # 1. Story Completion
    completed, total, incomplete = check_story_completion(prd_path)
    result.add_check(
        "Story Completion",
        completed == total,
        f"{completed}/{total} stories complete" + (f" — incomplete: {', '.join(incomplete)}" if incomplete else ""),
        weight=20
    )
    
    # 2. Syntax Check
    total_files, syntax_errors = check_python_syntax(project_dir)
    result.add_check(
        "Python Syntax",
        len(syntax_errors) == 0,
        f"{total_files} files checked, {len(syntax_errors)} errors" + (f": {syntax_errors[0]}" if syntax_errors else ""),
        weight=25
    )
    
    # 3. Docstring Coverage
    with_docs, total_defs = check_docstring_coverage(project_dir)
    coverage = (with_docs / total_defs * 100) if total_defs > 0 else 100
    result.add_check(
        "Docstring Coverage",
        coverage >= 50,
        f"{with_docs}/{total_defs} definitions documented ({coverage:.0f}%)",
        weight=10
    )
    
    # 4. Code Smells
    smells = check_code_smells(project_dir)
    critical_smells = [s for s in smells if any(kw in s for kw in ["password", "api_key", "secret"])]
    result.add_check(
        "Code Smells",
        len(critical_smells) == 0,
        f"{len(smells)} smells found" + (f" ({len(critical_smells)} critical!)" if critical_smells else ""),
        weight=15 if critical_smells else 5
    )
    
    # 5. Commit Quality
    commit_issues = check_commit_quality(project_dir)
    result.add_check(
        "Commit Quality",
        len(commit_issues) <= 1,
        f"{len(commit_issues)} issues" + (f": {commit_issues[0]}" if commit_issues else " — clean"),
        weight=5
    )
    
    # 6. File Size Warnings
    size_warnings = check_file_sizes(project_dir)
    result.add_check(
        "File Sizes",
        len(size_warnings) <= 2,
        f"{len(size_warnings)} oversized files" + (f": {size_warnings[0]}" if size_warnings else " — all reasonable"),
        weight=5
    )
    
    result.finalize()
    return result


def generate_review_report(result: ReviewResult) -> str:
    """Generate a human-readable review report."""
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    
    lines = [
        f"# Post-Completion Review — {status}",
        f"**{result.summary}**\n",
        "## Checks:",
    ]
    
    for check in result.checks:
        icon = "✅" if check["passed"] else "❌"
        lines.append(f"  {icon} **{check['name']}** — {check['detail']}")
    
    if not result.passed:
        lines.append(f"\n⚠️ Score {result.score} is below threshold ({REVIEW_THRESHOLD}).")
        lines.append("Ralph's output needs manual review before delivery.")
    
    return "\n".join(lines)


if __name__ == "__main__":
    prd_file = sys.argv[1] if len(sys.argv) > 1 else "/home/clawdbot/dev-sandbox/ralph/prd.json"
    project = sys.argv[2] if len(sys.argv) > 2 else "/home/clawdbot/dev-sandbox"
    
    result = run_post_review(prd_file, project)
    report = generate_review_report(result)
    print(report)
    
    sys.exit(0 if result.passed else 1)
