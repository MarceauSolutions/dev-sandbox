# MCP Conversion Plan: Existing Projects → Registry

> **Goal**: Convert existing projects to registry-ready MCPs as fast as possible to capture market share while the registry is still early (~2,000 servers).

## Executive Summary

| Project | Suitability | Effort | Impact | Priority | Decision |
|---------|-------------|--------|--------|----------|----------|
| **md-to-pdf** | 9/10 | Done | LOW | Done | ✅ CONVERTED |
| **Rideshare** | 10/10 | Done | HIGH | Done | ✅ REGISTERED |
| **HVAC** | 10/10 | Done | MEDIUM | Done | ✅ REGISTERED |
| **Amazon Seller** | 7/10 | Done | HIGH | Done | ✅ CONVERTED |
| **Fitness Influencer** | 6/10 | Done | HIGH | Done | ✅ CONVERTED |
| **Naples Weather** | 5/10 | 6-8 hrs | LOW | 4 | DEFER |
| **Interview Prep** | 2/10 | N/A | - | - | SKIP (web-based) |
| **Email Analyzer** | 1/10 | N/A | - | - | SKIP (workflow) |
| **Personal Assistant** | 0/10 | N/A | - | - | SKIP (meta-tool) |

---

## Detailed Assessments

### 1. Markdown to PDF ✅ CONVERT NOW

**Location**: `projects/md-to-pdf/`

**Why First**:
- Simplest conversion (no API keys)
- Already has testing infrastructure
- Clear single tool: `convert_md_to_pdf()`
- No external dependencies
- Fast path to first additional registry listing

**Technical Readiness**:
- [x] Has working code (`src/md_to_pdf.py`)
- [x] Code runs without errors
- [x] Has testing framework (`testing/`)
- [ ] Missing: MCP server wrapper

**Suitability Score**: 9/10
- Standalone execution: +3
- Clear tool boundaries: +2
- No API keys: +2
- Stateless: +2
- Single-purpose: +1
- No negatives

**Effort**: 3-4 hours
- Create `md_to_pdf_mcp.py` (2 hrs)
- Test with MCP client (1 hr)
- Registry submission (0.5 hr)
- Documentation (0.5 hr)

**Impact**: LOW (utility tool, many alternatives exist)

**Priority Score**: (1×3) + (9×2) - (4/4) = 3 + 18 - 1 = **20**

**Namespace**: `io.github.williammarceaujr/md-to-pdf`

---

### 2. Amazon Seller Operations ✅ CONVERT NEXT

**Location**: `projects/amazon-seller/`

**Why Second**:
- High business value (e-commerce is huge)
- Unique capability (SP-API integration is complex)
- Working code exists (9 Python files)
- Missing just structure (VERSION, CHANGELOG)

**Technical Readiness**:
- [x] Has working code (9 files in `src/`)
- [x] Code appears functional
- [ ] Missing: VERSION file
- [ ] Missing: CHANGELOG
- [ ] Missing: MCP server wrapper

**Suitability Score**: 7/10
- Standalone execution: +3
- Clear tool boundaries: +2
- Stateless operations: +2
- Complex auth flow: -1 (SP-API OAuth)
- Requires API setup: -1

**Effort**: 8-10 hours
- Add VERSION/CHANGELOG (1 hr)
- Create MCP server wrapper (4 hrs)
- Handle SP-API authentication (2 hrs)
- Test with MCP client (2 hrs)
- Registry submission (1 hr)

**Impact**: HIGH
- E-commerce is massive market
- SP-API integration is hard (moat)
- Clear revenue potential (sellers pay for tools)

**Priority Score**: (3×3) + (7×2) - (10/4) = 9 + 14 - 2.5 = **20.5**

**Namespace**: `io.github.williammarceaujr/amazon-seller`

**Tools to Expose**:
```python
# From amazon_sp_api.py
- get_inventory_summary()
- update_listing()
- get_orders()

# From amazon_fee_calculator.py
- calculate_fba_fees()
- estimate_profit_margin()

# From amazon_inventory_optimizer.py
- suggest_restock_quantities()
- analyze_sell_through_rate()
```

---

### 3. Fitness Influencer Operations ⚠️ CONVERT WEEK 2

**Location**: `projects/fitness-influencer/`

**Why Third**:
- Most impressive feature set (demonstrates platform power)
- Complex orchestration (hard to replicate = moat)
- Multiple API integrations (Grok, Shotstack, etc.)
- Requires more setup time

**Technical Readiness**:
- [x] Has working code (18 files in `src/`)
- [x] Has VERSION (1.0.0)
- [x] Has CHANGELOG
- [ ] Missing: MCP server wrapper
- [ ] Missing: API key management layer

**Suitability Score**: 6/10
- Standalone execution: +3
- Clear tool boundaries: +2
- Heavy orchestration: -2 (multiple AI calls)
- Complex API setup: -1 (xAI, Shotstack, etc.)

**Effort**: 12-16 hours
- Design MCP tool interface (2 hrs)
- Create MCP server wrapper (6 hrs)
- Handle multiple API keys (4 hrs)
- Test orchestration flows (3 hrs)
- Registry submission (1 hr)

**Impact**: HIGH
- Content creation is hot market
- AI + video automation is cutting edge
- Clear monetization (influencers pay)

**Priority Score**: (3×3) + (6×2) - (14/4) = 9 + 12 - 3.5 = **17.5**

**Namespace**: `io.github.williammarceaujr/fitness-influencer`

**Tools to Expose**:
```python
# Video Operations
- create_jump_cut_video()
- add_background_music()

# AI Content
- generate_fitness_image()
- write_caption()

# Analytics
- get_revenue_report()
- analyze_engagement()
```

---

### 4. Naples Weather Report ⏸️ DEFER

**Location**: `projects/naples-weather/`

**Why Defer**:
- Too simple (2 Python files)
- Very narrow use case (Naples only)
- Low differentiation (weather APIs are common)
- Better to expand scope first

**Technical Readiness**:
- [x] Has working code (2 files)
- [ ] Missing: VERSION
- [ ] Missing: CHANGELOG
- [ ] Too specialized

**Suitability Score**: 5/10
- Standalone: +3
- Single-purpose: +1
- Stateless: +2
- Niche use case: -1

**Effort**: 6-8 hours
- Add VERSION/CHANGELOG (1 hr)
- Create MCP wrapper (3 hrs)
- Generalize to any location (2-3 hrs) ← recommended
- Test and submit (1 hr)

**Impact**: LOW
- Weather data is commodity
- Many free alternatives
- No clear monetization

**Priority Score**: (1×3) + (5×2) - (7/4) = 3 + 10 - 1.75 = **11.25**

**Recommendation**: Expand to "Weather Report Generator" for any location before converting.

---

### 5. Interview Prep ❌ SKIP (Web-Based)

**Location**: `interview-prep-pptx/`

**Why Skip**:
- Requires web frontend (FastAPI + UI)
- Already deployed to Railway as web app
- Multi-step AI orchestration required
- Not suitable for MCP pattern

**Suitability Score**: 2/10
- Requires web frontend: -3
- Heavy orchestration: -2
- Complex multi-step: -2
- Clear tool concept: +2
- Valuable output: +1

**Decision**: Keep as web application. Not an MCP candidate.

---

### 6. Email Analyzer ❌ SKIP (Workflow-Based)

**Location**: `email-analyzer/`

**Why Skip**:
- No Python execution code
- Workflow-based tool (Claude orchestration)
- Requires AI reasoning, not code execution
- Not suitable for MCP pattern

**Suitability Score**: 1/10
- Workflow-based: -3
- Requires Claude orchestration: -3
- Clear use case: +2

**Decision**: Keep as Claude Skill. Not an MCP candidate.

---

### 7. Personal Assistant ❌ SKIP (Meta-Tool)

**Location**: `projects/personal-assistant/`

**Why Skip**:
- Meta-tool that aggregates other projects
- No independent functionality
- Depends on other projects being complete
- Router pattern, not service pattern

**Suitability Score**: 0/10
- No standalone functionality
- Pure routing/aggregation
- Circular dependency on other projects

**Decision**: Keep as local orchestration layer. Not an MCP candidate.

---

## Implementation Timeline

### Week 1 (Days 1-3): Quick Wins

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | md-to-pdf MCP wrapper | `md_to_pdf_mcp.py` working |
| 1 | Register md-to-pdf | Listed on registry |
| 2 | Amazon Seller structure | VERSION, CHANGELOG added |
| 2-3 | Amazon Seller MCP wrapper | `amazon_seller_mcp.py` working |
| 3 | Register Amazon Seller | Listed on registry |

**End of Week 1**: 4 MCPs on registry (rideshare, hvac, md-to-pdf, amazon-seller)

### Week 2 (Days 4-7): Complex Conversion

| Day | Task | Deliverable |
|-----|------|-------------|
| 4-5 | Fitness Influencer MCP design | Tool interface defined |
| 5-6 | Fitness Influencer wrapper | `fitness_influencer_mcp.py` working |
| 6-7 | Test all orchestration paths | Full test coverage |
| 7 | Register Fitness Influencer | Listed on registry |

**End of Week 2**: 5 MCPs on registry

### Week 3+: Optimization

- Monitor usage metrics on registry
- Optimize latency (caching, pre-warming)
- Improve documentation/examples
- Respond to user feedback
- Consider Naples Weather expansion

---

## Registry Namespace Strategy

All MCPs under consistent namespace:

```
io.github.williammarceaujr/
├── rideshare-comparison     ← Already done
├── hvac-quotes              ← Already done
├── md-to-pdf                ← Week 1
├── amazon-seller            ← Week 1
├── fitness-influencer       ← Week 2
└── [future MCPs]
```

---

## Success Metrics

| Metric | Week 1 Target | Week 2 Target |
|--------|---------------|---------------|
| MCPs on Registry | 4 | 5 |
| Registry Ranking | Top 500 | Top 200 |
| Categories Owned | Transportation, Home Services | + E-commerce, Content |
| Total Development Hours | 15 | 30 |

---

## Bezos Principles Applied

**Things that will ALWAYS matter for MCPs:**

| Principle | How We Optimize |
|-----------|----------------|
| **Fast** | 3-tier caching, pre-warming, efficient code |
| **Reliable** | Error handling, retries, health checks |
| **Accurate** | Validation, testing, source verification |
| **Discoverable** | Rich metadata, keywords, examples |
| **Simple** | Clean APIs, good docs, quick start |

**Apply these to EVERY MCP before registry submission.**

---

## Next Steps

1. **Today**: Start md-to-pdf MCP wrapper
2. **Tomorrow**: Register md-to-pdf, start Amazon Seller
3. **Day 3**: Complete Amazon Seller registration
4. **Week 2**: Fitness Influencer conversion

**Command to start**:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/md-to-pdf
# Create mcp-server/md_to_pdf_mcp.py
```
