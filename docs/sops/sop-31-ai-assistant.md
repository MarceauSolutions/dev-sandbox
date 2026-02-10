# SOP 31: AI Assistant Deployment

**When**: Deploying a standalone AI assistant that fresh Claude instances (or buyers) can use without dev-sandbox context

**Purpose**: Deploy AI assistants as self-contained products with Python scripts that can be:
1. Used by fresh Claude Code instances in isolation
2. Packaged and sold to customers
3. Optionally registered as Skills for dev-sandbox Claude

**Key Distinction from SOP 3:**
- **SOP 3 (Skills)**: Deploys to `~/production/[name]-prod/` for dev-sandbox Claude use
- **SOP 31 (AI Assistants)**: Deploys to `~/ai-assistants/[name]/` for standalone/sellable use
- **Both**: A project can be deployed BOTH as a Skill AND an AI Assistant

**Deployment Location:**
```
~/ai-assistants/                         # Container folder (NOT a git repo)
├── upwork-proposal-generator/           # Separate git repo
├── website-builder/                     # Separate git repo
├── md-to-pdf/                           # Separate git repo
└── [future-assistants]/                 # Each is its own repo
```

**Standard AI Assistant Structure:**
```
~/ai-assistants/[name]/
├── CLAUDE.md           # Instructions for LLM usage (self-contained)
├── README.md           # Human documentation, GitHub readme
├── requirements.txt    # Python dependencies
├── VERSION             # Version tracking
├── CHANGELOG.md        # Version history
│
├── src/                # THE PRODUCT (Python scripts - what you sell)
│   ├── __init__.py
│   ├── main.py         # Primary entry point
│   └── utils.py        # Supporting utilities
│
├── templates/          # Data templates and user configuration
│   └── profile.json    # User-specific data (name, skills, etc.)
│
├── output/             # Generated outputs (gitignored)
│
└── workflows/          # Step-by-step procedures (optional)
```

**What Gets Sold (if selling):**
- `src/` - Python scripts (the product)
- `templates/` - Configuration templates
- `README.md` - Usage documentation
- `requirements.txt` - Dependencies

**What's For LLM Usage (not sold):**
- `CLAUDE.md` - Instructions for Claude to orchestrate the .py files

**CLAUDE.md Template for AI Assistants:**
```markdown
# [Assistant Name]

## What This Does
[One paragraph - problem it solves]

## Quick Start
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Commands
- `python src/main.py --option "value"` - [Description]
- `python src/main.py --help` - Show all options

## User Configuration
Edit `templates/profile.json` to customize:
- [Config option 1]
- [Config option 2]

## Examples
[2-3 concrete usage examples with expected output]
```

**Steps:**

1. **Develop in dev-sandbox** (as normal):
   ```bash
   dev-sandbox/projects/[company]/[project]/
   ```

2. **Test thoroughly** (SOP 2/testing-strategy.md)

3. **Create assistant structure**:
   ```bash
   mkdir -p ~/ai-assistants/[name]/{src,templates,output,workflows}
   cd ~/ai-assistants/[name]
   git init
   ```

4. **Copy product files**:
   ```bash
   cp -r dev-sandbox/projects/[company]/[name]/src/* ~/ai-assistants/[name]/src/
   cp dev-sandbox/projects/[company]/[name]/requirements.txt ~/ai-assistants/[name]/
   ```

5. **Create self-contained CLAUDE.md** (fresh Claude needs ONLY this file)

6. **Create profile template**:
   ```bash
   # templates/profile.json - user-editable configuration
   ```

7. **Add .gitignore**:
   ```
   output/
   __pycache__/
   *.pyc
   .env
   ```

8. **Commit and push**:
   ```bash
   git add .
   git commit -m "Initial AI assistant deployment"
   git remote add origin git@github.com:[user]/[name].git
   git push -u origin main
   ```

9. **(Optional) Also deploy as Skill** for dev-sandbox usage:
   ```bash
   python deploy_to_skills.py --project [name] --version X.Y.Z
   ```

**Distribution Options:**

| Target Buyer | Distribution Method | Complexity |
|--------------|---------------------|------------|
| Developers | GitHub repo + `pip install -r requirements.txt` | Low |
| Claude users | MCP package (SOPs 11-14) | Medium |
| Non-technical | Streamlit/Gradio web app | Medium |
| General public | Desktop app (Electron/PyInstaller) | High |

**Verification** (fresh Claude test):
1. Open new Claude Code instance
2. Open ONLY `~/ai-assistants/[name]/`
3. Claude should be able to use the assistant with ONLY the CLAUDE.md
4. No reference to dev-sandbox should be needed

**Communication Patterns**:
- "Deploy as AI assistant" → SOP 31 to `~/ai-assistants/[name]/`
- "Deploy as skill" → SOP 3 to `~/production/[name]-prod/`
- "Deploy as both" → Run SOP 31 then SOP 3
- "Package for sale" → Zip `src/`, `templates/`, `README.md`, `requirements.txt`

**References**: SOP 3 (Skills), SOPs 11-14 (MCP packaging)
