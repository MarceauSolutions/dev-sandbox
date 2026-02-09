# Execution Folder Audit: Shared vs Project-Specific

**Date**: 2026-01-12
**Purpose**: Categorize all scripts in `execution/` as truly shared (2+ projects) or project-specific (1 project only)

---

## Summary

**Total Scripts**: 62 Python files in `/Users/williammarceaujr./dev-sandbox/execution/`

**Categorization**:
- **Shared Utilities** (used by 2+ projects): 6 scripts
- **Project-Specific** (used by 1 project only): 50 scripts
- **Infrastructure** (deployment, not deployed): 6 scripts

**Recommendation**: Move 50 project-specific scripts to `projects/[name]/src/` to match documented architecture.

---

## Category 1: Shared Utilities (Keep in execution/)

These scripts are used by **2 or more projects** and should remain in `execution/` as shared utilities:

| Script | Used By | Purpose |
|--------|---------|---------|
| `gmail_monitor.py` | fitness-influencer, amazon-seller, personal-assistant | Gmail monitoring utility |
| `grok_image_gen.py` | interview-prep, fitness-influencer, personal-assistant | Grok AI image generation |
| `twilio_sms.py` | fitness-influencer, amazon-seller, personal-assistant | SMS notification utility |
| `revenue_analytics.py` | fitness-influencer, amazon-seller | Revenue tracking and analytics |
| `markdown_to_pdf.py` | naples-weather, (potentially md-to-pdf) | Markdown to PDF conversion |
| `pdf_outputs.py` | interview-prep, (potentially other projects) | PDF generation utilities |

**Total**: 6 scripts

**Action**: ✅ Keep these in `execution/` - They are truly shared utilities

---

## Category 2: Interview Prep Project-Specific (Move to projects/interview-prep/src/)

These scripts are used **only by interview-prep**:

| Script | Purpose | Current Location | Target Location |
|--------|---------|-----------------|-----------------|
| `interview_research.py` | Company research | execution/ | projects/interview-prep/src/ |
| `interview_prep_api.py` | API server | execution/ | projects/interview-prep/src/ |
| `pptx_generator.py` | PowerPoint generation | execution/ | projects/interview-prep/src/ |
| `pptx_editor.py` | PowerPoint editing | execution/ | projects/interview-prep/src/ |
| `session_manager.py` | Session management | execution/ | projects/interview-prep/src/ |
| `template_manager.py` | Template handling | execution/ | projects/interview-prep/src/ |
| `live_editor.py` | Live editing | execution/ | projects/interview-prep/src/ |
| `mock_interview.py` | Mock interviews | execution/ | projects/interview-prep/src/ |
| `intent_router.py` | Intent routing | execution/ | projects/interview-prep/src/ |
| `apply_navy_theme.py` | Theme application | execution/ | projects/interview-prep/src/ |
| `download_pptx.py` | Download handler | execution/ | projects/interview-prep/src/ |
| `open_pptx.py` | File opener | execution/ | projects/interview-prep/src/ |
| `enhance_experience_slides.py` | Slide enhancement | execution/ | projects/interview-prep/src/ |
| `reformat_experience_slides.py` | Slide reformatting | execution/ | projects/interview-prep/src/ |
| `standardize_experience_slides.py` | Slide standardization | execution/ | projects/interview-prep/src/ |
| `educational_graphics.py` | Graphics (also fitness, keep if shared) | execution/ | Check usage |

**Total**: 15+ scripts

**Action**: 🔄 Move to `projects/interview-prep/src/`

---

## Category 3: Amazon Seller Project-Specific (Move to projects/amazon-seller/src/)

These scripts are used **only by amazon-seller**:

| Script | Purpose | Current Location | Target Location |
|--------|---------|-----------------|-----------------|
| `amazon_sp_api.py` | SP-API client | execution/ | projects/amazon-seller/src/ |
| `amazon_fee_calculator.py` | Fee calculations | execution/ | projects/amazon-seller/src/ |
| `amazon_inventory_optimizer.py` | Inventory optimization | execution/ | projects/amazon-seller/src/ |
| `amazon_get_refresh_token.py` | OAuth token refresh | execution/ | projects/amazon-seller/src/ |
| `amazon_oauth_server.py` | OAuth server | execution/ | projects/amazon-seller/src/ |
| `refresh_amazon_token.py` | Token refresh | execution/ | projects/amazon-seller/src/ |
| `setup_amazon_auth.py` | Auth setup | execution/ | projects/amazon-seller/src/ |
| `test_amazon_connection.py` | Connection testing | execution/ | projects/amazon-seller/src/ |
| `test_sp_api_simple.py` | API testing | execution/ | projects/amazon-seller/src/ |

**Total**: 9 scripts

**Action**: 🔄 Move to `projects/amazon-seller/src/`

---

## Category 4: Fitness Influencer Project-Specific (Move to projects/fitness-influencer/src/)

These scripts are used **only by fitness-influencer**:

| Script | Purpose | Current Location | Target Location |
|--------|---------|-----------------|-----------------|
| `video_jumpcut.py` | Video jump cut editing | execution/ | projects/fitness-influencer/src/ |
| `workout_plan_generator.py` | Workout plan creation | execution/ | projects/fitness-influencer/src/ |
| `nutrition_guide_generator.py` | Nutrition guide creation | execution/ | projects/fitness-influencer/src/ |
| `fitness_assistant_api.py` | API server | execution/ | projects/fitness-influencer/src/ |
| `video_ads.py` | Video ad creation | execution/ | projects/fitness-influencer/src/ |
| `video_analytics_dashboard.py` | Analytics dashboard | execution/ | projects/fitness-influencer/src/ |
| `moviepy_video_generator.py` | Video generation | execution/ | projects/fitness-influencer/src/ |
| `moviepy_video_generator_old.py` | Old video generator | execution/ | projects/fitness-influencer/src/ (or delete) |
| `moviepy_video_generator_v2.py` | Video generator v2 | execution/ | projects/fitness-influencer/src/ |
| `intelligent_video_router.py` | Video routing | execution/ | projects/fitness-influencer/src/ |
| `shotstack_api.py` | Shotstack integration | execution/ | projects/fitness-influencer/src/ |
| `creatomate_api.py` | Creatomate integration | execution/ | projects/fitness-influencer/src/ |
| `creatomate_api_enhanced.py` | Enhanced Creatomate | execution/ | projects/fitness-influencer/src/ |

**Total**: 13 scripts

**Action**: 🔄 Move to `projects/fitness-influencer/src/`

---

## Category 5: Naples Weather Project-Specific (Move to projects/naples-weather/src/)

These scripts are used **only by naples-weather**:

| Script | Purpose | Current Location | Target Location |
|--------|---------|-----------------|-----------------|
| `fetch_naples_weather.py` | Weather API fetching | execution/ | projects/naples-weather/src/ |
| `generate_weather_report.py` | Report generation | execution/ | projects/naples-weather/src/ |

**Total**: 2 scripts

**Action**: 🔄 Move to `projects/naples-weather/src/`

**Note**: `markdown_to_pdf.py` is shared with other projects, keep in execution/

---

## Category 6: Website Builder Project-Specific (Likely - Need Verification)

These scripts appear to be website-builder specific:

| Script | Purpose | Current Location | Target Location |
|--------|---------|-----------------|-----------------|
| `canva_integration.py` | Canva integration | execution/ | projects/website-builder/src/ (verify) |

**Total**: 1 script

**Action**: ⚠️ Verify usage before moving

---

## Category 7: Sales CRM / Lead Management (Project Unknown - Need Investigation)

These scripts don't match any configured project:

| Script | Purpose | Notes |
|--------|---------|-------|
| `add_lead.py` | Lead addition | No matching project configured |
| `lead_manager.py` | Lead management | No matching project configured |
| `setup_sales_crm.py` | CRM setup | No matching project configured |
| `setup_custom_fields.py` | Custom field setup | No matching project configured |
| `get_custom_fields.py` | Custom field retrieval | No matching project configured |
| `send_onboarding_email.py` | Email onboarding | No matching project configured |

**Total**: 6 scripts

**Action**: ⚠️ Either:
1. Create new project: `projects/sales-crm/src/` and move there
2. Delete if deprecated/unused
3. Identify which existing project uses them

---

## Category 8: Calendar / Scheduling (Project Unknown - Need Investigation)

| Script | Purpose | Notes |
|--------|---------|-------|
| `calendar_reminders.py` | Calendar reminders | No matching project configured |
| `google_auth_setup.py` | Google OAuth | Could be shared utility |

**Total**: 2 scripts

**Action**: ⚠️ Either:
1. Move to shared utilities if used by multiple projects
2. Move to specific project if single-use
3. Delete if deprecated

---

## Category 9: ClickUp Integration (Project Unknown - Need Investigation)

| Script | Purpose | Notes |
|--------|---------|-------|
| `clickup_api.py` | ClickUp API client | No matching project configured |
| `clickup_oauth.py` | ClickUp OAuth | No matching project configured |

**Total**: 2 scripts

**Action**: ⚠️ Either:
1. Move to shared utilities if used by multiple projects
2. Move to specific project if single-use
3. Delete if deprecated

---

## Category 10: Infrastructure / Meta Scripts (Keep in execution/ or root)

These scripts are for infrastructure, not deployed to skills:

| Script | Purpose | Location |
|--------|---------|----------|
| `deploy_to_skills.py` | Deployment script | execution/ (should be in root) |
| `manage_agent_skills.py` | Skill management | execution/ |
| `monitor_capability_gaps.py` | Gap monitoring | execution/ |
| `setup_wizard.py` | Setup wizard | execution/ |
| `update_skill_docs.py` | Documentation updater | execution/ |

**Total**: 5 scripts

**Action**: ⚠️ These are meta-tools, consider moving to root or `tools/` directory

**Note**: `deploy_to_skills.py` is already in root, duplicate in execution/

---

## Migration Plan

### Phase 1: Move Confirmed Project-Specific Scripts

**Interview Prep** (15 scripts):
```bash
# Create src directory if needed
mkdir -p /Users/williammarceaujr./dev-sandbox/projects/interview-prep/src

# Move scripts
mv execution/interview_research.py projects/interview-prep/src/
mv execution/interview_prep_api.py projects/interview-prep/src/
mv execution/pptx_generator.py projects/interview-prep/src/
mv execution/pptx_editor.py projects/interview-prep/src/
mv execution/session_manager.py projects/interview-prep/src/
mv execution/template_manager.py projects/interview-prep/src/
mv execution/live_editor.py projects/interview-prep/src/
mv execution/mock_interview.py projects/interview-prep/src/
mv execution/intent_router.py projects/interview-prep/src/
mv execution/apply_navy_theme.py projects/interview-prep/src/
mv execution/download_pptx.py projects/interview-prep/src/
mv execution/open_pptx.py projects/interview-prep/src/
mv execution/enhance_experience_slides.py projects/interview-prep/src/
mv execution/reformat_experience_slides.py projects/interview-prep/src/
mv execution/standardize_experience_slides.py projects/interview-prep/src/
```

**Amazon Seller** (9 scripts):
```bash
mkdir -p /Users/williammarceaujr./dev-sandbox/projects/amazon-seller/src

mv execution/amazon_sp_api.py projects/amazon-seller/src/
mv execution/amazon_fee_calculator.py projects/amazon-seller/src/
mv execution/amazon_inventory_optimizer.py projects/amazon-seller/src/
mv execution/amazon_get_refresh_token.py projects/amazon-seller/src/
mv execution/amazon_oauth_server.py projects/amazon-seller/src/
mv execution/refresh_amazon_token.py projects/amazon-seller/src/
mv execution/setup_amazon_auth.py projects/amazon-seller/src/
mv execution/test_amazon_connection.py projects/amazon-seller/src/
mv execution/test_sp_api_simple.py projects/amazon-seller/src/
```

**Fitness Influencer** (13 scripts):
```bash
mkdir -p /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer/src

mv execution/video_jumpcut.py projects/fitness-influencer/src/
mv execution/workout_plan_generator.py projects/fitness-influencer/src/
mv execution/nutrition_guide_generator.py projects/fitness-influencer/src/
mv execution/fitness_assistant_api.py projects/fitness-influencer/src/
mv execution/video_ads.py projects/fitness-influencer/src/
mv execution/video_analytics_dashboard.py projects/fitness-influencer/src/
mv execution/moviepy_video_generator.py projects/fitness-influencer/src/
mv execution/moviepy_video_generator_v2.py projects/fitness-influencer/src/
mv execution/intelligent_video_router.py projects/fitness-influencer/src/
mv execution/shotstack_api.py projects/fitness-influencer/src/
mv execution/creatomate_api.py projects/fitness-influencer/src/
mv execution/creatomate_api_enhanced.py projects/fitness-influencer/src/
# Delete old version
rm execution/moviepy_video_generator_old.py
```

**Naples Weather** (2 scripts):
```bash
mkdir -p /Users/williammarceaujr./dev-sandbox/projects/naples-weather/src

mv execution/fetch_naples_weather.py projects/naples-weather/src/
mv execution/generate_weather_report.py projects/naples-weather/src/
```

### Phase 2: Investigate Unknown Scripts

**Sales CRM** (6 scripts) - Decision needed:
- Create `projects/sales-crm/src/` and move?
- Delete if deprecated?

**Calendar** (2 scripts) - Decision needed:
- Move to shared if used by multiple?
- Move to specific project?

**ClickUp** (2 scripts) - Decision needed:
- Move to shared if used by multiple?
- Move to specific project?

### Phase 3: Clean Up execution/

After migration, execution/ should contain **only**:
- `gmail_monitor.py` (shared)
- `grok_image_gen.py` (shared)
- `twilio_sms.py` (shared)
- `revenue_analytics.py` (shared)
- `markdown_to_pdf.py` (shared)
- `pdf_outputs.py` (shared)

**Total**: 6 shared utilities

---

## Impact on deploy_to_skills.py

**Current behavior**: Copies scripts from `execution/` to skills deployment

**Required changes**:
1. Support copying from `projects/[name]/src/` directly
2. Support copying shared utilities from `execution/`
3. Handle hybrid deployments (project scripts + shared utilities)

**Example new configuration**:
```python
"interview-prep": {
    "src_dir": PROJECTS_DIR / "interview-prep" / "src",  # Changed source
    "shared_utils": ["gmail_monitor.py", "grok_image_gen.py"],  # NEW: Shared deps
    "scripts": [
        "interview_research.py",  # Now in projects/interview-prep/src/
        "pptx_generator.py",
        # ... other scripts
    ]
}
```

---

## Summary Statistics

| Category | Count | Action |
|----------|-------|--------|
| **Shared Utilities** | 6 | ✅ Keep in execution/ |
| **Interview Prep** | 15 | 🔄 Move to projects/interview-prep/src/ |
| **Amazon Seller** | 9 | 🔄 Move to projects/amazon-seller/src/ |
| **Fitness Influencer** | 13 | 🔄 Move to projects/fitness-influencer/src/ |
| **Naples Weather** | 2 | 🔄 Move to projects/naples-weather/src/ |
| **Unknown/Investigation** | 11 | ⚠️ Investigate before moving |
| **Infrastructure** | 5 | ⚠️ Consider moving to root/tools/ |
| **Duplicates** | 1 | 🗑️ Remove (deploy_to_skills.py duplicate) |
| **TOTAL** | 62 | - |

**Net Result**: execution/ goes from 62 scripts → 6 shared utilities (90% reduction)

---

## Next Steps

1. ✅ Review this audit for accuracy
2. ⚠️ Investigate unknown scripts (sales-crm, calendar, clickup)
3. 🔄 Execute Phase 1 migration (move confirmed project-specific scripts)
4. 📝 Update deploy_to_skills.py to support new structure
5. ✅ Test deployment with new structure
6. 📄 Create execution/README.md documenting guidelines

---

**Date Created**: 2026-01-12
**Status**: Audit Complete - Awaiting approval for Phase 1 migration
