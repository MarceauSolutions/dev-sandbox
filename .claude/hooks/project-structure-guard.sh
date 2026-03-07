#!/bin/bash
# Claude Code PreToolUse Hook: Project Structure Guard
#
# Prevents creating project files outside the proper folder structure.
# Catches files written to:
#   - ~/Desktop/ (should be in projects/)
#   - projects/product-ideas/ (for company projects that belong in projects/marceau-solutions/)
#   - projects/<name>/ at root level (should be projects/marceau-solutions/<name>/ or projects/shared/<name>/)
#
# Informational warning — does not block (exit 0), but loudly reminds.
# The goal: enforce SOP 32 → SOP 0 → SOP 1 project routing before creating files.

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Skip non-project files (configs, docs, scripts, hooks, etc.)
if [[ "$FILE_PATH" =~ \.(json|yaml|yml|toml|cfg|ini|env)$ ]]; then
    exit 0
fi
if [[ "$FILE_PATH" =~ /\.claude/ || "$FILE_PATH" =~ /node_modules/ ]]; then
    exit 0
fi

SANDBOX="/Users/williammarceaujr./dev-sandbox"
WARNED=0

# 1. Files on Desktop that look like project code
if [[ "$FILE_PATH" =~ ^/Users/williammarceaujr\./Desktop/ ]]; then
    if [[ "$FILE_PATH" =~ \.(swift|py|js|ts|html|css)$ ]]; then
        echo "" >&2
        echo "=== PROJECT STRUCTURE WARNING ===" >&2
        echo "Writing project code to ~/Desktop/." >&2
        echo "Project code should live in projects/marceau-solutions/<name>/ or projects/shared/<name>/." >&2
        echo "" >&2
        echo "Did you run SOP 32 (Project Routing) and SOP 0 (Kickoff) first?" >&2
        echo "Run: ./scripts/add-company-project.sh marceau-solutions <project-name> project" >&2
        echo "" >&2
        WARNED=1
    fi
fi

# 2. Files in product-ideas/ that should be in marceau-solutions/
if [[ "$FILE_PATH" =~ $SANDBOX/projects/product-ideas/ ]]; then
    if [[ "$FILE_PATH" =~ \.(swift|py|js|ts|html|css)$ ]] || [[ "$FILE_PATH" =~ /src/ ]]; then
        echo "" >&2
        echo "=== PROJECT STRUCTURE WARNING ===" >&2
        echo "Writing production code to projects/product-ideas/." >&2
        echo "product-ideas/ is for exploration/research only." >&2
        echo "" >&2
        echo "If this is a real project, route it properly:" >&2
        echo "  Company project → projects/marceau-solutions/<name>/" >&2
        echo "  Client project  → projects/<client-name>/" >&2
        echo "  Shared tool     → projects/shared/<name>/" >&2
        echo "" >&2
        echo "Run SOP 32 → SOP 0 → SOP 1 first." >&2
        echo "" >&2
        WARNED=1
    fi
fi

# 3. New top-level project folders (not under marceau-solutions/, shared/, or known clients)
KNOWN_PARENTS="marceau-solutions|shared|product-ideas|swflorida-hvac|boabfit|flames-of-passion|square-foot-shipping"
if [[ "$FILE_PATH" =~ $SANDBOX/projects/([^/]+)/ ]]; then
    PARENT="${BASH_REMATCH[1]}"
    if [[ ! "$PARENT" =~ ^($KNOWN_PARENTS)$ ]]; then
        echo "" >&2
        echo "=== PROJECT STRUCTURE WARNING ===" >&2
        echo "Creating files under new project folder: projects/$PARENT/" >&2
        echo "This folder is not in the known project structure." >&2
        echo "" >&2
        echo "If this is a new project, run SOP 32 (Project Routing) first:" >&2
        echo "  Company project → projects/marceau-solutions/$PARENT/" >&2
        echo "  New client       → Add to known clients in project-structure-guard.sh" >&2
        echo "" >&2
        WARNED=1
    fi
fi

# 4. Source code files directly in projects/ root (not in a subfolder)
if [[ "$FILE_PATH" =~ ^$SANDBOX/projects/[^/]+\.(swift|py|js|ts|html|css)$ ]]; then
    echo "" >&2
    echo "=== PROJECT STRUCTURE WARNING ===" >&2
    echo "Writing code files directly in projects/ root." >&2
    echo "Files should be inside a project folder: projects/<category>/<project-name>/src/" >&2
    echo "" >&2
    WARNED=1
fi

exit 0
