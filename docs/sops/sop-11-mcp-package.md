# SOP 11: MCP Package Structure

**When**: Converting a project to MCP (Model Context Protocol) format for distribution via PyPI and the Claude MCP Registry

**Purpose**: Create a properly structured Python package that can be installed via `pip` and registered on Claude's MCP marketplace

**Agent**: Claude Code (REQUIRED - Mac keychain for publishing). Clawdbot/Ralph: N/A.

**Prerequisites**:
- ✅ Project has working `src/` code with MCP server implementation
- ✅ Project has been tested (SOP 2/3 complete)
- ✅ README.md exists with project description

**Directory Structure** (before → after):
```
projects/[project]/
├── src/
│   ├── server.py              # Original MCP server
│   └── module.py              # Supporting modules
├── README.md
├── VERSION
└── CHANGELOG.md

↓ After SOP 11 ↓

projects/[project]/
├── src/
│   ├── [project]_mcp/         # NEW: Package directory
│   │   ├── __init__.py        # Package init with version
│   │   ├── server.py          # MCP server (imports fixed)
│   │   └── module.py          # Supporting modules (copied)
│   └── (original files)
├── pyproject.toml             # NEW: Build configuration
├── server.json                # NEW: MCP Registry manifest
├── README.md                  # UPDATED: Add mcp-name line
├── VERSION
└── CHANGELOG.md
```

**Steps**:

**1. Create Package Directory**
```bash
mkdir -p projects/[project]/src/[project]_mcp/
```

**2. Create `__init__.py`**
```python
# projects/[project]/src/[project]_mcp/__init__.py
__version__ = "1.0.0"

from .server import mcp  # or main entry point
```

**3. Copy and Fix Server Code**
```bash
# Copy server and modules to package directory
cp projects/[project]/src/server.py projects/[project]/src/[project]_mcp/
cp projects/[project]/src/module.py projects/[project]/src/[project]_mcp/
```

Then fix imports in `server.py`:
```python
# BEFORE (absolute imports)
from module import SomeClass

# AFTER (relative imports for package)
from .module import SomeClass
```

Also remove any `sys.path` manipulation:
```python
# DELETE these lines if present
import sys
sys.path.insert(0, str(Path(__file__).parent))
```

**4. Create `pyproject.toml`**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "[project]-mcp"
version = "1.0.0"
description = "Short description under 100 characters"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [
    {name = "Your Name", email = "your@email.com"}
]
keywords = ["mcp", "claude", "ai", "[domain-keywords]"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "mcp>=1.0.0",
    # Add other dependencies from requirements.txt
]

[project.urls]
Homepage = "https://github.com/[username]/[repo]"
Repository = "https://github.com/[username]/[repo]"

[project.scripts]
[project]-mcp = "[project]_mcp.server:main"

[tool.hatch.build.targets.wheel]
packages = ["src/[project]_mcp"]
```

**5. Create `server.json`** (MCP Registry manifest)
```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
  "name": "io.github.[username]/[project]",
  "description": "Short description under 100 characters",
  "repository": {
    "url": "https://github.com/[username]/[repo]",
    "source": "github",
    "subfolder": "projects/[project]"
  },
  "version": "1.0.0",
  "packages": [
    {
      "registryType": "pypi",
      "identifier": "[project]-mcp",
      "version": "1.0.0",
      "transport": {
        "type": "stdio"
      },
      "runtime": "python",
      "environmentVariables": [
        {
          "name": "API_KEY",
          "description": "Description of required API key"
        }
      ]
    }
  ]
}
```

**6. Update README.md** (add ownership verification line)
```markdown
# Project Name

mcp-name: io.github.[username]/[project]

Rest of README...
```

**Important**: The `mcp-name:` line MUST be near the top of README for MCP Registry ownership verification.

**7. Verify Package Structure**
```bash
# Check all files exist
ls -la projects/[project]/src/[project]_mcp/
# Should show: __init__.py, server.py, and modules

# Test imports work
cd projects/[project]
python -c "from src.[project]_mcp import mcp"
```

**Naming Conventions**:
| Item | Format | Example |
|------|--------|---------|
| PyPI package name | `[project]-mcp` | `fitness-influencer-mcp` |
| Package directory | `[project]_mcp` | `fitness_influencer_mcp` |
| MCP Registry name | `io.github.[user]/[project]` | `io.github.wmarceau/fitness-influencer` |

**Common Mistakes**:
| Mistake | Fix |
|---------|-----|
| Using hyphens in package dir | Use underscores: `fitness_influencer_mcp` not `fitness-influencer-mcp` |
| Absolute imports in package | Change to relative: `from .module import X` |
| sys.path manipulation | Remove it - package imports handle this |
| Description > 100 chars | Shorten it for MCP Registry |
| Missing `mcp-name:` in README | Add it near top for ownership verification |

**Success Criteria**:
- ✅ Package directory created with `__init__.py`
- ✅ All imports use relative syntax (`.module`)
- ✅ `pyproject.toml` has correct package path
- ✅ `server.json` has valid schema
- ✅ README has `mcp-name:` line
- ✅ `python -c "from src.[project]_mcp import ..."` works

**Next Step**: SOP 12 (PyPI Publishing)

**References**:
- `projects/shared/md-to-pdf/` - Working example
- `projects/marceau-solutions/amazon-seller/` - Working example
- `projects/marceau-solutions/fitness-influencer-mcp/` - Working example
