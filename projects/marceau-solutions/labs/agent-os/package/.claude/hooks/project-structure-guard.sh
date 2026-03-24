#!/usr/bin/env bash
# AgentOS Hook: Project Structure Guard
# Warns when creating files outside the proper project structure.
# Informational — warns but does not block.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null || true)

if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Skip config files
if [[ "$FILE_PATH" =~ \.(json|yaml|yml|toml|cfg|ini|env)$ ]]; then
    exit 0
fi
if [[ "$FILE_PATH" =~ /\.claude/ || "$FILE_PATH" =~ /node_modules/ ]]; then
    exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"

# Warn if writing code to Desktop
if [[ "$FILE_PATH" =~ ^$HOME/Desktop/ ]]; then
    if [[ "$FILE_PATH" =~ \.(py|js|ts|swift|go|rs|html|css)$ ]]; then
        echo "" >&2
        echo "=== PROJECT STRUCTURE WARNING ===" >&2
        echo "Writing code to ~/Desktop/." >&2
        echo "Project code should live in projects/[name]/src/" >&2
        echo "" >&2
    fi
fi

# Warn if writing code directly in project root
if [[ "$FILE_PATH" =~ ^$REPO_ROOT/[^/]+\.(py|js|ts|swift|go|rs)$ ]]; then
    echo "" >&2
    echo "=== PROJECT STRUCTURE WARNING ===" >&2
    echo "Writing code files directly in project root." >&2
    echo "Files should be inside: projects/[name]/src/ or execution/" >&2
    echo "" >&2
fi

exit 0
