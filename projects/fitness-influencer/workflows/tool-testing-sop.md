# SOP: Education Scenario Testing for Fitness Tools

*Last Updated: 2026-01-15*
*Version: 1.0.0*

## Purpose

Validate each fitness landing page tool works correctly with realistic fitness influencer scenarios before exposing to end users. This prevents embarrassing failures when real users interact with tools via marceausolutions.com/fitness.

## Tool Inventory

| # | Tool | Module | Test Status | Dependencies |
|---|------|--------|-------------|--------------|
| 1 | `generate_workout_plan` | workout_plan_generator.py | ✅ READY | None (FREE) |
| 2 | `categorize_comments` | comment_categorizer.py | ✅ READY | None (FREE) |
| 3 | `optimize_for_platforms` | cross_platform_optimizer.py | ✅ READY | None (FREE) |
| 4 | `generate_content_calendar` | content_calendar.py | ✅ READY | None (FREE) |
| 5 | `generate_video_blueprint` | video_template_framework.py | ✅ READY | None (FREE) |
| 6 | `get_cogs_report` | cogs_tracker.py | ✅ READY | None (FREE) |
| 7 | `log_api_usage` | cogs_tracker.py | ✅ READY | None (FREE) |
| 8 | `generate_fitness_image` | grok_image_gen.py | ⚠️ NEEDS KEY | XAI_API_KEY |
| 9 | `get_revenue_report` | revenue_analytics.py | ⚠️ NEEDS CREDS | Google Sheets API |
| 10 | `create_jump_cut_video` | video_jumpcut.py | ✅ READY | moviepy (installed) |
| 11 | `add_video_branding` | video_jumpcut.py | ✅ READY | moviepy (installed) |
| 12 | `analyze_content_engagement` | (placeholder) | ℹ️ STUB | Future integration |

## Test Categories

### Category 1: FREE Tools (No Dependencies)
**Test immediately** - no API keys required
- generate_workout_plan
- categorize_comments
- optimize_for_platforms
- generate_content_calendar
- generate_video_blueprint
- get_cogs_report / log_api_usage

### Category 2: API-Dependent Tools
**Require valid credentials in .env**
- generate_fitness_image (XAI_API_KEY)
- get_revenue_report (Google Sheets credentials)

### Category 3: Video Processing Tools
**Require sample video files**
- create_jump_cut_video
- add_video_branding

### Category 4: Placeholder Tools
**Not fully implemented**
- analyze_content_engagement (future work)

---

## Per-Tool Test Protocol

For each tool, run the following:

### Test Template

```markdown
### Tool: [Tool Name]
**Category:** [1-4]
**Dependencies:** [List]

**Test Command:**
```bash
[Exact command to test]
```

**Education Scenario:**
- **Persona:** [Who is using this]
- **Goal:** [What they're trying to accomplish]
- **Input:** [Realistic test data]
- **Expected Output:** [What success looks like]
- **Edge Cases:** [What could go wrong]

**Pass Criteria:**
- [ ] Returns valid output
- [ ] Handles invalid input gracefully
- [ ] Performance is acceptable (<5 seconds for simple, <30s for video)
- [ ] Output is useful for the persona
```

---

## Quick Test Commands

### Test Directory
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer
```

### Category 1: FREE Tools

```bash
# 1. Workout Plan Generator
python -c "
from src.workout_plan_generator import WorkoutPlanGenerator
gen = WorkoutPlanGenerator()
plan = gen.generate_plan('muscle_gain', 'intermediate', 4, 'full_gym')
print('SUCCESS' if plan else 'FAILED')
print(f'Days: {len(plan.get(\"days\", []))}')
"

# 2. Comment Categorizer
python -c "
from src.fitness_influencer_mcp.comment_categorizer import CommentCategorizer
cat = CommentCategorizer()
result = cat.categorize_batch(['Love this workout!', 'SPAM BUY NOW!!!', 'Can we collab?'])
print('SUCCESS' if result else 'FAILED')
for r in result: print(f'{r[\"category\"]}: {r[\"text\"][:30]}')
"

# 3. Cross-Platform Optimizer
python -c "
from src.fitness_influencer_mcp.cross_platform_optimizer import CrossPlatformOptimizer
opt = CrossPlatformOptimizer()
result = opt.optimize_for_all_platforms('video', 'Check out my new workout routine!', video_duration=60)
print('SUCCESS' if result else 'FAILED')
print(f'Platforms optimized: {len(result.get(\"platforms\", {}))}')
"

# 4. Content Calendar Generator
python -c "
from src.fitness_influencer_mcp.content_calendar import ContentCalendarGenerator
gen = ContentCalendarGenerator()
cal = gen.generate_calendar(days=7, posts_per_day=2)
print('SUCCESS' if cal else 'FAILED')
print(f'Days planned: {len(cal.get(\"days\", []))}')
"

# 5. Video Blueprint Generator
python -c "
from src.video_template_framework import VideoTemplateGenerator
gen = VideoTemplateGenerator()
template = gen.generate_template('5 ab exercises for beginners', 'educational', 60, 'instagram_reels')
print('SUCCESS' if template else 'FAILED')
print(f'Segments: {len(template.get(\"segments\", []))}')
"

# 6. COGS Tracker
python -c "
from src.cogs_tracker import COGSTracker
tracker = COGSTracker()
report = tracker.get_daily_report()
print('SUCCESS' if report else 'FAILED')
print(f'Transactions today: {report.get(\"transaction_count\", 0)}')
"
```

### Category 2: API-Dependent Tools

```bash
# 8. Image Generation (requires XAI_API_KEY)
python -c "
import os
from src.grok_image_gen import GrokImageGenerator
if not os.getenv('XAI_API_KEY'):
    print('SKIPPED: XAI_API_KEY not set')
else:
    gen = GrokImageGenerator()
    # Dry run - don't actually generate
    print('API key present - ready for testing')
"

# 9. Revenue Report (requires Google credentials)
python -c "
from src.revenue_analytics import RevenueAnalytics
analytics = RevenueAnalytics(sheet_id='test')
service = analytics.authenticate()
print('SUCCESS' if service else 'NEEDS CREDENTIALS')
"
```

### Category 3: Video Tools

```bash
# 10-11. Video Jump Cut (requires sample video)
python -c "
from src.video_jumpcut import VideoJumpCutter
editor = VideoJumpCutter()
print('VideoJumpCutter initialized successfully')
print('Methods available:', [m for m in dir(editor) if not m.startswith('_')])
"
```

---

## Education Scenario Files

Detailed scenarios are in:
- `workflows/education-scenarios/workout-plan-scenarios.md`
- `workflows/education-scenarios/video-blueprint-scenarios.md`
- `workflows/education-scenarios/content-calendar-scenarios.md`
- `workflows/education-scenarios/platform-optimizer-scenarios.md`
- `workflows/education-scenarios/image-generation-scenarios.md`
- `workflows/education-scenarios/revenue-analytics-scenarios.md`
- `workflows/education-scenarios/video-editing-scenarios.md`
- `workflows/education-scenarios/comment-categorizer-scenarios.md`

---

## Test Results Location

Save test results to:
```
workflows/test-results/YYYY-MM-DD-test-run.md
```

---

## Pass/Fail Criteria

### Tool Must Pass
- [ ] Returns valid output for happy path
- [ ] Returns helpful error for invalid input
- [ ] Does not crash on edge cases
- [ ] Output is useful for fitness influencer persona
- [ ] Performance under 5 seconds (simple) / 30 seconds (video)

### Blocking Issues
If any tool fails:
1. Document the failure in test results
2. DO NOT allow traffic to landing page
3. Fix the issue before proceeding
4. Re-run all tests

---

## Integration with Landing Page

**Landing Page Tools Map:**

| Landing Page Modal | Backend Tool | Status |
|-------------------|--------------|--------|
| Workout Plan Generator | `generate_workout_plan` | Category 1 |
| Video Blueprint | `generate_video_blueprint` | Category 1 |
| Content Calendar | `generate_content_calendar` | Category 1 |
| Platform Optimizer | `optimize_for_platforms` | Category 1 |
| AI Image Generation | `generate_fitness_image` | Category 2 |
| Revenue Analytics | `get_revenue_report` | Category 2 |
| Video Jump Cuts | `create_jump_cut_video` | Category 3 |
| Comment Manager | `categorize_comments` | Category 1 |

---

## Next Steps After Testing

1. **All Category 1 tools pass** → Safe for basic landing page use
2. **Category 2 tools need keys** → Add API key setup instructions to landing page
3. **Category 3 tools pass** → Enable video upload features
4. **Category 4 stubs** → Show "Coming Soon" on landing page

---

## References

- [Fitness Influencer MCP Server](../src/fitness_influencer_mcp/server.py)
- [Landing Page](https://marceausolutions.com/fitness)
- [X Campaign SOP](../../social-media-automation/workflows/x-campaign-sop.md)
