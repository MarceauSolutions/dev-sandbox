#!/usr/bin/env python3
"""
Security Scanner
================

Automated vulnerability detection for the dev-sandbox codebase.
Scans for common security issues and generates actionable reports.

Scans For:
- Command injection vulnerabilities (subprocess, os.system, shell=True)
- Hardcoded credentials and secrets
- SQL injection patterns
- Path traversal vulnerabilities
- Insecure deserialization (pickle, yaml.load)
- Debug mode enabled
- Missing input validation
- Overly permissive file permissions

Usage:
    python security_scanner.py                    # Full scan
    python security_scanner.py --quick            # Quick scan (critical only)
    python security_scanner.py --path projects/   # Scan specific path
    python security_scanner.py --output report.md # Save report to file
    python security_scanner.py --json             # JSON output for automation

Version: 1.0.0
Created: 2026-01-29
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime

__version__ = "1.0.0"

# Default paths to scan
DEFAULT_SCAN_PATH = Path("/Users/williammarceaujr./dev-sandbox")
EXCLUDE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "env", ".eggs", "*.egg-info", "dist", "build", ".tmp",
    ".archive", "archived"
}
SCAN_EXTENSIONS = {".py", ".js", ".ts", ".sh", ".yaml", ".yml", ".json", ".env"}


@dataclass
class Finding:
    """Security finding."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str
    title: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    remediation: str
    cwe_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class SecurityScanner:
    """
    Comprehensive security scanner for Python/JS codebases.
    """

    # Vulnerability patterns
    PATTERNS = {
        # Command Injection (CWE-78)
        "cmd_injection_shell_true": {
            "pattern": r"subprocess\.[^\(]+\([^)]*shell\s*=\s*True",
            "severity": "CRITICAL",
            "category": "Command Injection",
            "title": "subprocess with shell=True",
            "description": "Using shell=True with subprocess allows shell injection attacks",
            "remediation": "Use subprocess with a list of arguments instead of shell=True",
            "cwe_id": "CWE-78"
        },
        "cmd_injection_os_system": {
            "pattern": r"os\.system\s*\(",
            "severity": "CRITICAL",
            "category": "Command Injection",
            "title": "os.system() usage",
            "description": "os.system() passes commands to the shell, enabling injection",
            "remediation": "Use subprocess.run() with a list of arguments",
            "cwe_id": "CWE-78"
        },
        "cmd_injection_popen_shell": {
            "pattern": r"os\.popen\s*\(",
            "severity": "HIGH",
            "category": "Command Injection",
            "title": "os.popen() usage",
            "description": "os.popen() is vulnerable to command injection",
            "remediation": "Use subprocess.run() with a list of arguments",
            "cwe_id": "CWE-78"
        },
        "cmd_injection_eval": {
            "pattern": r"\beval\s*\(",
            "severity": "CRITICAL",
            "category": "Code Injection",
            "title": "eval() usage",
            "description": "eval() executes arbitrary code, extremely dangerous",
            "remediation": "Use ast.literal_eval() for safe evaluation or avoid eval entirely",
            "cwe_id": "CWE-95"
        },
        "cmd_injection_exec": {
            "pattern": r"\bexec\s*\(",
            "severity": "CRITICAL",
            "category": "Code Injection",
            "title": "exec() usage",
            "description": "exec() executes arbitrary code",
            "remediation": "Avoid exec() or carefully validate all inputs",
            "cwe_id": "CWE-95"
        },

        # Hardcoded Credentials (CWE-798)
        "hardcoded_password": {
            "pattern": r"(?:password|passwd|pwd)\s*=\s*['\"][^'\"]{4,}['\"]",
            "severity": "HIGH",
            "category": "Hardcoded Credentials",
            "title": "Hardcoded password",
            "description": "Password hardcoded in source code",
            "remediation": "Use environment variables or secrets manager",
            "cwe_id": "CWE-798"
        },
        "hardcoded_api_key": {
            "pattern": r"(?:api[_-]?key|apikey|secret[_-]?key)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
            "severity": "HIGH",
            "category": "Hardcoded Credentials",
            "title": "Hardcoded API key",
            "description": "API key hardcoded in source code",
            "remediation": "Use environment variables or secrets manager",
            "cwe_id": "CWE-798"
        },
        "hardcoded_token": {
            "pattern": r"(?:token|bearer|auth)\s*=\s*['\"][A-Za-z0-9_\-\.]{20,}['\"]",
            "severity": "HIGH",
            "category": "Hardcoded Credentials",
            "title": "Hardcoded token",
            "description": "Authentication token hardcoded in source code",
            "remediation": "Use environment variables or secrets manager",
            "cwe_id": "CWE-798"
        },
        "aws_access_key": {
            "pattern": r"AKIA[0-9A-Z]{16}",
            "severity": "CRITICAL",
            "category": "Hardcoded Credentials",
            "title": "AWS Access Key ID",
            "description": "AWS Access Key ID found in code",
            "remediation": "Remove immediately, rotate key, use IAM roles",
            "cwe_id": "CWE-798"
        },

        # SQL Injection (CWE-89)
        "sql_injection_format": {
            "pattern": r"(?:execute|cursor\.execute)\s*\([^)]*%[sd]",
            "severity": "HIGH",
            "category": "SQL Injection",
            "title": "SQL query with string formatting",
            "description": "SQL query built with string formatting is vulnerable to injection",
            "remediation": "Use parameterized queries with ? or %s placeholders",
            "cwe_id": "CWE-89"
        },
        "sql_injection_fstring": {
            "pattern": r"(?:execute|cursor\.execute)\s*\(\s*f['\"]",
            "severity": "HIGH",
            "category": "SQL Injection",
            "title": "SQL query with f-string",
            "description": "SQL query built with f-string is vulnerable to injection",
            "remediation": "Use parameterized queries",
            "cwe_id": "CWE-89"
        },

        # Insecure Deserialization (CWE-502)
        "pickle_load": {
            "pattern": r"pickle\.loads?\s*\(",
            "severity": "HIGH",
            "category": "Insecure Deserialization",
            "title": "pickle.load() usage",
            "description": "pickle can execute arbitrary code during deserialization",
            "remediation": "Use JSON or other safe formats, or validate pickle sources",
            "cwe_id": "CWE-502"
        },
        "yaml_load_unsafe": {
            "pattern": r"yaml\.load\s*\([^)]*(?!Loader\s*=)",
            "severity": "MEDIUM",
            "category": "Insecure Deserialization",
            "title": "Unsafe YAML load",
            "description": "yaml.load() without safe Loader can execute code",
            "remediation": "Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader)",
            "cwe_id": "CWE-502"
        },

        # Path Traversal (CWE-22)
        "path_traversal_open": {
            "pattern": r"open\s*\([^)]*(?:request|input|param|arg|data)\.",
            "severity": "MEDIUM",
            "category": "Path Traversal",
            "title": "Potential path traversal in file open",
            "description": "User input used directly in file path",
            "remediation": "Validate and sanitize file paths, use os.path.basename()",
            "cwe_id": "CWE-22"
        },

        # Debug Mode (CWE-489)
        "debug_mode_flask": {
            "pattern": r"app\.run\s*\([^)]*debug\s*=\s*True",
            "severity": "MEDIUM",
            "category": "Debug Mode",
            "title": "Flask debug mode enabled",
            "description": "Debug mode should never be enabled in production",
            "remediation": "Set debug=False or use environment variable",
            "cwe_id": "CWE-489"
        },
        "debug_mode_django": {
            "pattern": r"DEBUG\s*=\s*True",
            "severity": "MEDIUM",
            "category": "Debug Mode",
            "title": "Django DEBUG enabled",
            "description": "DEBUG should be False in production",
            "remediation": "Set DEBUG = False in production settings",
            "cwe_id": "CWE-489"
        },

        # Weak Cryptography (CWE-327)
        "weak_crypto_md5": {
            "pattern": r"hashlib\.md5\s*\(",
            "severity": "MEDIUM",
            "category": "Weak Cryptography",
            "title": "MD5 hash usage",
            "description": "MD5 is cryptographically broken",
            "remediation": "Use SHA-256 or stronger hash functions",
            "cwe_id": "CWE-327"
        },
        "weak_crypto_sha1": {
            "pattern": r"hashlib\.sha1\s*\(",
            "severity": "LOW",
            "category": "Weak Cryptography",
            "title": "SHA1 hash usage",
            "description": "SHA1 is deprecated for security purposes",
            "remediation": "Use SHA-256 or stronger hash functions",
            "cwe_id": "CWE-327"
        },

        # Information Disclosure
        "stack_trace_exposure": {
            "pattern": r"traceback\.print_exc\s*\(\)",
            "severity": "LOW",
            "category": "Information Disclosure",
            "title": "Stack trace printed",
            "description": "Stack traces may leak sensitive information",
            "remediation": "Log to file instead of printing, sanitize error messages",
            "cwe_id": "CWE-209"
        },

        # SSRF (CWE-918)
        "ssrf_requests": {
            "pattern": r"requests\.(?:get|post|put|delete)\s*\([^)]*(?:input|param|arg|url_param)",
            "severity": "MEDIUM",
            "category": "SSRF",
            "title": "Potential SSRF vulnerability",
            "description": "User input used in HTTP request URL",
            "remediation": "Validate and allowlist URLs, don't allow arbitrary redirects",
            "cwe_id": "CWE-918"
        },
    }

    def __init__(self, scan_path: Path = DEFAULT_SCAN_PATH):
        self.scan_path = scan_path
        self.findings: List[Finding] = []
        self.files_scanned = 0
        self.lines_scanned = 0

    def should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded from scanning."""
        for part in path.parts:
            if part in EXCLUDE_DIRS or part.startswith("."):
                return True
        return False

    def scan_file(self, file_path: Path) -> List[Finding]:
        """Scan a single file for vulnerabilities."""
        findings = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            self.lines_scanned += len(lines)

            for pattern_name, pattern_info in self.PATTERNS.items():
                regex = re.compile(pattern_info["pattern"], re.IGNORECASE)

                for line_num, line in enumerate(lines, 1):
                    if regex.search(line):
                        # Skip if in comment
                        stripped = line.strip()
                        if stripped.startswith("#") or stripped.startswith("//"):
                            continue

                        # Skip if this is a pattern definition (in security scanner itself)
                        if '"title":' in stripped or '"description":' in stripped:
                            continue

                        # Skip if this is clearly a string literal explanation
                        if stripped.startswith('"') and stripped.endswith('",'):
                            continue

                        finding = Finding(
                            severity=pattern_info["severity"],
                            category=pattern_info["category"],
                            title=pattern_info["title"],
                            description=pattern_info["description"],
                            file_path=str(file_path.relative_to(self.scan_path)),
                            line_number=line_num,
                            code_snippet=line.strip()[:100],
                            remediation=pattern_info["remediation"],
                            cwe_id=pattern_info.get("cwe_id")
                        )
                        findings.append(finding)

        except Exception as e:
            pass  # Skip unreadable files

        return findings

    def scan(self, quick: bool = False) -> List[Finding]:
        """
        Scan the codebase for vulnerabilities.

        Args:
            quick: If True, only scan for CRITICAL vulnerabilities

        Returns:
            List of findings
        """
        self.findings = []
        self.files_scanned = 0
        self.lines_scanned = 0

        # Determine which patterns to use
        patterns_to_use = self.PATTERNS
        if quick:
            patterns_to_use = {
                k: v for k, v in self.PATTERNS.items()
                if v["severity"] == "CRITICAL"
            }
            # Temporarily replace patterns
            original_patterns = self.PATTERNS.copy()
            self.PATTERNS = patterns_to_use

        # Walk the directory tree
        for root, dirs, files in os.walk(self.scan_path):
            root_path = Path(root)

            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            if self.should_exclude(root_path):
                continue

            for file in files:
                file_path = root_path / file

                if file_path.suffix not in SCAN_EXTENSIONS:
                    continue

                self.files_scanned += 1
                findings = self.scan_file(file_path)
                self.findings.extend(findings)

        # Restore patterns if quick scan
        if quick:
            self.PATTERNS = original_patterns

        return self.findings

    def generate_report(self, format: str = "markdown") -> str:
        """Generate a formatted report of findings."""
        if format == "json":
            return json.dumps({
                "scan_time": datetime.now().isoformat(),
                "scan_path": str(self.scan_path),
                "files_scanned": self.files_scanned,
                "lines_scanned": self.lines_scanned,
                "findings_count": len(self.findings),
                "findings_by_severity": self._count_by_severity(),
                "findings": [f.to_dict() for f in self.findings]
            }, indent=2)
        else:
            return self._generate_markdown_report()

    def _count_by_severity(self) -> Dict[str, int]:
        """Count findings by severity."""
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for finding in self.findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts

    def _generate_markdown_report(self) -> str:
        """Generate markdown formatted report."""
        counts = self._count_by_severity()
        total = len(self.findings)

        report = f"""# Security Scan Report

**Scan Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Scan Path**: `{self.scan_path}`
**Files Scanned**: {self.files_scanned:,}
**Lines Scanned**: {self.lines_scanned:,}

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | {counts['CRITICAL']} |
| HIGH | {counts['HIGH']} |
| MEDIUM | {counts['MEDIUM']} |
| LOW | {counts['LOW']} |
| **TOTAL** | **{total}** |

"""

        if not self.findings:
            report += "\n## Results\n\nNo vulnerabilities found.\n"
            return report

        # Group findings by severity
        report += "## Findings\n\n"

        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            severity_findings = [f for f in self.findings if f.severity == severity]
            if not severity_findings:
                continue

            report += f"### {severity} ({len(severity_findings)})\n\n"

            for i, finding in enumerate(severity_findings, 1):
                cwe = f" ({finding.cwe_id})" if finding.cwe_id else ""
                report += f"""#### {i}. {finding.title}{cwe}

**File**: `{finding.file_path}:{finding.line_number}`
**Category**: {finding.category}

**Description**: {finding.description}

**Code**:
```
{finding.code_snippet}
```

**Remediation**: {finding.remediation}

---

"""

        # Add recommendations section
        report += """## Recommendations

### Immediate Actions (CRITICAL)

1. **Fix all CRITICAL findings immediately** - These represent active vulnerabilities
2. **Rotate any exposed credentials** - If hardcoded secrets found
3. **Review subprocess/os.system calls** - Ensure no user input reaches shell

### Short-term Actions (HIGH)

1. **Implement input validation** - Sanitize all user inputs
2. **Use parameterized queries** - Prevent SQL injection
3. **Move secrets to environment variables** - Remove from code

### Long-term Actions (MEDIUM/LOW)

1. **Integrate security scanning into CI/CD** - Run on every commit
2. **Conduct regular security reviews** - Monthly at minimum
3. **Implement security training** - Ensure team awareness

---

*Generated by Security Scanner v{__version__}*
"""

        return report


def main():
    parser = argparse.ArgumentParser(
        description="Security scanner for dev-sandbox",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_SCAN_PATH,
        help="Path to scan (default: dev-sandbox)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick scan (CRITICAL vulnerabilities only)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save report to file"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show summary"
    )

    args = parser.parse_args()

    # Run scan
    print(f"Scanning {args.path}...", file=sys.stderr)
    scanner = SecurityScanner(args.path)
    findings = scanner.scan(quick=args.quick)

    # Generate report
    format_type = "json" if args.json else "markdown"
    report = scanner.generate_report(format=format_type)

    # Output
    if args.output:
        args.output.write_text(report)
        print(f"Report saved to: {args.output}", file=sys.stderr)
    elif args.quiet:
        counts = scanner._count_by_severity()
        print(f"CRITICAL: {counts['CRITICAL']}, HIGH: {counts['HIGH']}, "
              f"MEDIUM: {counts['MEDIUM']}, LOW: {counts['LOW']}")
    else:
        print(report)

    # Exit with error code if critical findings
    counts = scanner._count_by_severity()
    if counts["CRITICAL"] > 0:
        sys.exit(2)
    elif counts["HIGH"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
