<!-- Original SOP as it appeared in CLAUDE.md (4,402 lines) before 2026-02-09 restructuring -->

### SOP 31: AI Assistant Deployment

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
├── upwork-proposal-generator/           # ✅ Separate git repo
├── website-builder/                     # ✅ Separate git repo
├── md-to-pdf/                           # ✅ Separate git repo
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

---

## Build Taxonomy (Canonical Definitions)

> **Why this exists**: We use many terms — project, tool, skill, assistant, workflow, utility, product, service, MCP, automation. These overlap in everyday language ("my tool is someone else's skill"). This section defines exactly what each term means **in our system** so SOP 32 routing, folder placement, and deployment decisions are consistent.

### The 3 Layers

Everything we build falls into one of three layers. These layers define the **vocabulary** (what we call things). SOP 32's 10 routing destinations use this vocabulary — each destination maps to one or more layers.

| Layer | What It Is | Contains | Example |
|-------|-----------|----------|---------|
| **Documentation** | Written knowledge (no code) | Procedures, frameworks, decisions | Workflow, Method, SOP |
| **Code** | Software that runs | Scripts, servers, APIs | Utility, Project, MCP Server |
| **Deployment** | How code reaches users | Packaging + distribution | Skill, AI Assistant, MCP Package |

**How this relates to SOP 32**: SOP 32 routes you to a *destination* (e.g., "Company Project"). This taxonomy tells you what that destination *is* (Code layer, Project type). A single destination can span layers — e.g., "Business Ops" is Documentation + Code.

**Key insight**: A single codebase can have multiple deployment targets. A "Company Project" (code) can be deployed as both a "Skill" (for dev-sandbox Claude) AND an "AI Assistant" (for fresh Claude). The *code* and the *deployment* are separate concepts.

### Documentation Layer (No Code)

| Term | Definition | Location | Key Test |
|------|-----------|----------|----------|
| **Workflow** | A step-by-step procedure documented in markdown. Tells someone (human or AI) how to complete a specific task. Not code — just instructions. | `[project]/workflows/[name].md` | "Can I follow these steps manually?" → Yes = Workflow |
| **Method** | An internal operational framework, decision matrix, or classification system. Broader than a workflow — defines *how to think about* a category of problems. | `methods/[name]/` | "Does this define a repeatable decision-making process?" → Yes = Method |
| **SOP** | A Standard Operating Procedure. A formalized, numbered, version-controlled process in CLAUDE.md. SOPs are the most rigid documentation — they define how our *system itself* operates. | `CLAUDE.md` (inline) | "Should every session follow this the same way?" → Yes = SOP |
| **Directive** | High-level instructions for a capability area. Defines what a project/system does and how to orchestrate it. The "what" layer of DOE. | `directives/[name].md` | "Does this tell Claude what to do, not how?" → Yes = Directive |

### Code Layer (Software That Runs)

| Term | Definition | Location | Key Test |
|------|-----------|----------|---------|
| **Utility** | A single Python file (<200 lines) used by 2+ projects. Small, focused, stable. No folder structure — just one script in the shared execution directory. | `execution/[name].py` | "Is it one file, used by multiple projects, and rarely changes?" → Yes = Utility |
| **Project** | A multi-file codebase with its own folder structure (`src/`, `workflows/`, `VERSION`, `README.md`). The general-purpose container for any software effort that needs more than one file. Projects always live under `projects/`. | `projects/[location]/[name]/` | "Does it need its own folder with multiple files?" → Yes = Project |
| **MCP Server** | A Model Context Protocol server — a specific technical format that exposes tools to Claude via stdio transport. An MCP Server is a *type of code*, not a deployment target. | `projects/[location]/[name]/src/[name]_mcp/` | "Does it implement the MCP protocol with tool definitions?" → Yes = MCP Server |
| **Automation** | Code that runs on a schedule or trigger without human initiation. Usually an n8n workflow, cron job, or webhook handler. Automations *do things* on their own. | n8n (EC2) or `execution/[name].py` with cron | "Does it run by itself on a timer or trigger?" → Yes = Automation |
| **Website** | A web presence (HTML/CSS/JS) deployed to hosting. Not a web *app* — a website is primarily content, not functionality. | `projects/[co]/website/` (submodule) | "Is the primary output a public web page?" → Yes = Website |

### Deployment Layer (How Code Reaches Users)

| Term | Definition | Location | Key Test |
|------|-----------|----------|---------|
| **Skill** | Code deployed for THIS dev-sandbox Claude to use. A Skill is a *deployment target*, not a type of code. Any Project can become a Skill by deploying via SOP 3. | `~/production/[name]-prod/` | "Will dev-sandbox Claude use this directly?" → Yes = deploy as Skill |
| **AI Assistant** | A self-contained tool with its own CLAUDE.md, deployable to a fresh Claude instance or sellable to buyers. Must work in isolation — no reference to dev-sandbox. A deployment target (can ALSO be deployed as a Skill for dev-sandbox Claude via SOP 3). | `~/ai-assistants/[name]/` | "Can a fresh Claude use this with zero context?" → Yes = deploy as AI Assistant |
| **MCP Package** | An MCP Server published to PyPI and the Claude MCP Registry. This is a *distribution channel*, not a type of code. Any MCP Server can become an MCP Package via SOPs 11-14. | PyPI + MCP Registry | "Is it installable via pip and discoverable in Claude?" → Yes = MCP Package |
| **Client Deliverable** | Code or website delivered to a paying client. A *delivery mechanism*, not a type of code. | `~/upwork-projects/` or `~/website-projects/` | "Is a client paying for this?" → Yes = Client Deliverable |

### Project Subtypes (When Primary Type = Project)

Since "Project" is the broadest category, these subtypes distinguish *who it's for* and *how it's used*:

| Subtype | Definition | Location | Key Distinguisher |
|---------|-----------|----------|-------------------|
| **Company Project** | A project specific to one company (usually marceau-solutions). Used internally by that company. | `projects/[company]/[name]/` | Single-company, internal use |
| **Shared Tool** | A project used by 2+ companies. Multi-tenant by design. | `projects/shared/[name]/` | Multi-company, shared use |
| **Product Idea** | An experimental or proof-of-concept project. Not committed to — exploring whether it's worth building. | `projects/product-ideas/[name]/` | Experimental, may be abandoned |
| **Business Ops** | A project that's primarily workflows/documentation with minimal or no code. Operational procedures for a company. | `projects/[company]/[name]/` (workflows-only) | Mostly docs, little/no code |

### Common Confusions Resolved

| Confusion | Resolution |
|-----------|-----------|
| "Is this a Tool or a Project?" | If it's one file in `execution/` → **Utility**. If it has its own folder with multiple files → **Project**. "Tool" is informal — avoid using it; say Utility or Project instead. |
| "Is this a Skill or an AI Assistant?" | Both are *deployment targets*, not code types. **Skill** = for dev-sandbox Claude (SOP 3). **AI Assistant** = for fresh Claude or buyers (SOP 31). Same code can be deployed as both. |
| "Is this a Project or an MCP?" | **MCP Server** is a code format. **Project** is a folder structure. An MCP Server lives *inside* a Project. Publishing it makes it an **MCP Package**. |
| "Is this a Workflow or an Automation?" | **Workflow** = documented steps (markdown, human follows). **Automation** = code that runs by itself (n8n, cron). A Workflow can *describe* how to use an Automation. |
| "Is this a Product or a Project?" | **Product** is a business concept (generates revenue). **Project** is a technical container. A Project *becomes* a Product when you sell/monetize it. Use the subtype "Product Idea" for early exploration. |
| "Is this a Service or a Project?" | **Service** is informal for "backend API that runs continuously." In our system, it's still a **Project** (or **Automation** if triggered). Avoid "service" as a formal category. |

### Terminology Rules

1. **Prefer specific terms** over generic ones: "Utility" not "tool", "Company Project" not "project"
2. **Separate code from deployment**: "We built a Company Project and deployed it as a Skill and an AI Assistant"
3. **Avoid these ambiguous terms** in formal contexts: "tool" (use Utility or Project), "service" (use Project or Automation), "script" (use Utility), "product" (use Product Idea subtype or just say "revenue-generating")
4. **Layer your descriptions**: "[Code Type] deployed as [Deployment Type]" — e.g., "MCP Server deployed as an MCP Package" or "Company Project deployed as a Skill"

