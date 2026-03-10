# SOP 32: Project Routing & Classification

**When**: FIRST step for ANY new idea, project, tool, assistant, or skill -- before SOP 0, SOP 17, or anything else

**Purpose**: Classify what you're building and where it belongs using a 5-question decision tree. Prevents inconsistent placement and ensures correct deployment routing from day one.

**Agent**: Any agent. Claude Code (primary). Clawdbot (can run for simple routing). Ralph: N/A.

**Skip if**: Continuing work on an already-classified project.

**5-Question Decision Tree**:

```
Q1: Is this SOFTWARE you will build?
├── NO → Internal Method (methods/) | Business Ops (projects/[co]/) | Research
│        NEXT: SOP 20 (methods) or just create folder with workflows/
└── YES → Q2

Q2: Who is this for?
├── CLIENT (someone paying you)
│   ├── Website build → projects/marceau-solutions/digital/clients/[name]/
│   └── Custom tool   → ~/upwork-projects/clients/[name]/
│   NEXT: Client workspace procedures
└── OWN USE or PRODUCT → Q3

Q3: Will 2+ companies/projects use this?
├── YES + small utility (<200 lines) → execution/[name].py (just build it)
├── YES + multi-file project → projects/shared/[name]/ → SOP 0
└── NO or UNSURE → Q4

Q4: Will this be sold, packaged, or used by a fresh Claude?
├── YES → AI Assistant
│   DEV: projects/[company]/[name]/
│   DEPLOY: ~/ai-assistants/[name]/ (SOP 31)
│   NEXT: SOP 0
└── NO (internal/personal use only) → Q5

Q5: Exploration/POC or committed real project?
├── POC / "Let me try this" → projects/marceau-solutions/labs/[name]/
│   NEXT: SOP 17 (if commercial) or just experiment
└── REAL PROJECT → Q6

Q6: Which tower does this belong to? (by customer/market)
├── Fitness clients (coaching, training, health) → projects/marceau-solutions/fitness/[name]/
├── Business clients (websites, digital services) → projects/marceau-solutions/digital/[name]/
├── Content/audience (social, influencer, media) → projects/marceau-solutions/media/[name]/
└── R&D/experiments (new ventures, tools) → projects/marceau-solutions/labs/[name]/
    NEXT: SOP 0
```

**Routing Output Template** (fill out after running the tree):

```markdown
## Project Routing Result
| Field | Value |
|-------|-------|
| **Type** | [See 10 types below] |
| **Location** | [Exact path] |
| **Deploy To** | [Target or None] |
| **Next SOP** | [SOP number] |
| **Skip SOPs** | [SOPs that don't apply] |
```

**10 Routing Destinations** (see Build Taxonomy in CLAUDE.md archive for full definitions):

| Destination | Layer | Location | Deploy To | Next SOP |
|-------------|-------|----------|-----------|----------|
| Method | Documentation | `methods/[name]/` | None (integrate into SOPs) | SOP 20 |
| Business Ops | Documentation + Code | `projects/[company]/[name]/` | None | Create workflows/ |
| Client Website | Code (Website) | `projects/marceau-solutions/digital/clients/[name]/` | GitHub Pages | Client procedures |
| Client Freelance | Code (Project) | `~/upwork-projects/clients/[name]/` | Client Deliverable | Client procedures |
| Utility | Code | `execution/[name].py` | None (used in-place) | Just build it |
| Shared Tool | Code (Project subtype) | `projects/shared/[name]/` | Skill (`~/production/`) | SOP 0 → SOP 1 |
| AI Assistant | Code → Deployment | `projects/[co]/[name]/` → `~/ai-assistants/[name]/` | AI Assistant | SOP 0 → SOP 31 |
| Product Idea / R&D | Code (Project subtype) | `projects/marceau-solutions/labs/[name]/` | None (graduate if viable) | SOP 17 |
| Fitness Project | Code (Project subtype) | `projects/marceau-solutions/fitness/[name]/` | Varies (SOP 0 decides) | SOP 0 → SOP 1 |
| Digital Project | Code (Project subtype) | `projects/marceau-solutions/digital/[name]/` | Varies (SOP 0 decides) | SOP 0 → SOP 1 |
| Media Project | Code (Project subtype) | `projects/marceau-solutions/media/[name]/` | Varies (SOP 0 decides) | SOP 0 → SOP 1 |
| Website | Code (Website) | `projects/marceau-solutions/digital/website/` | GitHub Pages | Website setup |

**Success Criteria**:
- [ ] Routing Result filled out with Type, Location, Deploy To, Next SOP
- [ ] Location path is unambiguous
- [ ] Correct next SOP identified (skip unnecessary ones)

**References**: `docs/FOLDER-STRUCTURE-GUIDE.md` (detailed folder placement), `docs/app-type-decision-guide.md` (app type within software projects)
