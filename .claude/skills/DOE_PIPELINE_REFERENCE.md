# DOE Pipeline Reference

## What is DOE?

**DOE** stands for **Directive, Orchestration, Execution** - the 3-layer architecture used for developing Claude Code Skills and automation workflows in this project.

## The DOE Pipeline

This is the methodology we use to develop all skills and automation workflows:

### Layer 1: Directive (What to do)
- **Location:** `directives/*.md`
- **Purpose:** Standard Operating Procedures written in Markdown
- **Contains:** Goals, inputs, tools/scripts to use, outputs, edge cases
- **Format:** Natural language instructions, like you'd give a mid-level employee
- **Examples:**
  - `directives/generate_naples_weather_report.md`
  - `directives/onboard_client.md`

### Layer 2: Orchestration (Decision making)
- **Who:** Claude (AI agent)
- **Purpose:** Intelligent routing and decision-making
- **Responsibilities:**
  - Read directives
  - Call execution tools in the right order
  - Handle errors
  - Ask for clarification when needed
  - Update directives with learnings
- **Role:** The glue between intent and execution

### Layer 3: Execution (Doing the work)
- **Location:** `execution/*.py`
- **Purpose:** Deterministic Python scripts that do the actual work
- **Contains:**
  - API calls
  - Data processing
  - File operations
  - Database interactions
- **Characteristics:** Reliable, testable, fast, consistent
- **Environment:** Variables and tokens stored in `.env`
- **Examples:**
  - `execution/fetch_naples_weather.py`
  - `execution/generate_weather_report.py`

## Why DOE Works

**Problem:** LLMs are probabilistic, but business logic requires deterministic consistency.

**Solution:** Separate concerns across three layers.

- 90% accuracy per step = 59% success over 5 steps (compounding errors)
- DOE pushes complexity into deterministic code
- Claude focuses only on decision-making, not implementation

## Developing with DOE Pipeline

### Standard Workflow

1. **Define the Directive** (Layer 1)
   - Write clear SOP in `directives/`
   - Document: goal, inputs, tools, outputs, edge cases

2. **Build Execution Tools** (Layer 3)
   - Create Python scripts in `execution/`
   - Make them deterministic and testable
   - Handle environment variables

3. **Enable Orchestration** (Layer 2)
   - Claude reads directive
   - Claude calls execution scripts
   - Claude handles errors and updates

### Deploying to Claude Skills

Once DOE pipeline is working:

1. Create skill directory: `.claude/skills/skill-name/`
2. Write `SKILL.md` with:
   - Description (for automatic triggering)
   - Instructions referencing the directive
   - Tool permissions (`allowed-tools`)
3. Reference existing execution scripts
4. Skill is now available automatically

## File Organization

```
dev-sandbox/
├── .claude/
│   └── skills/              # Claude Code Skills (DOE deployed here)
│       └── skill-name/
│           └── SKILL.md
├── directives/              # Layer 1: What to do
│   └── *.md
├── execution/               # Layer 3: Python scripts that do work
│   └── *.py
├── .tmp/                    # Intermediate files (never commit)
└── .env                     # Environment variables
```

## Key Principle

**Directives are living documents.** When you discover:
- API constraints
- Better approaches
- Common errors
- Timing expectations

→ Update the directive so the system learns and improves.

## Self-Annealing Loop

When something breaks:
1. Read error message and stack trace
2. Fix the script and test
3. Update the directive with learnings
4. System is now stronger

This is how the DOE pipeline continuously improves.

## Reference

See [CLAUDE.md](../../CLAUDE.md) for complete architecture documentation.
