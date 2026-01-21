#!/bin/bash

# Fix all "shared-multi-tenant" references to use "shared" instead
# Part of final hybrid architecture compliance check

set -e

echo "================================================"
echo "Fixing shared-multi-tenant → shared references"
echo "================================================"
echo ""

# Counter
FIXED_COUNT=0

# List of files with shared-multi-tenant references
FILES_TO_FIX=(
  "./DOCKET.md"
  "./methods/r-and-d-department/apollo-io-prospect-alerts.md"
  "./projects/apollo-mcp/PROJECT-SUMMARY.md"
  "./projects/shared/lead-scraper/IMPLEMENT-PREVENTION-STRATEGIES.md"
  "./projects/shared/lead-scraper/AGENT4-FINDINGS.md"
  "./projects/shared/lead-scraper/AGENT-5-SUMMARY.md"
  "./projects/shared/lead-scraper/input/apollo/README.md"
  "./projects/shared/lead-scraper/AGENT2-FINDINGS.md"
  "./projects/shared/lead-scraper/MONITORING-CHEAT-SHEET.md"
  "./projects/shared/lead-scraper/AGENT2-README.md"
  "./projects/shared/lead-scraper/output/CAMPAIGN-STATUS-SUMMARY-2026-01-21.md"
  "./projects/shared/lead-scraper/output/campaigns/CAMPAIGN_LAUNCH_SUMMARY.md"
  "./projects/shared/lead-scraper/output/campaigns/DAILY_OPERATIONS_GUIDE.md"
  "./projects/shared/lead-scraper/workflows/monitoring-quick-start.md"
  "./projects/shared/lead-scraper/workflows/campaign-auto-launch-sop.md"
  "./projects/shared/lead-scraper/workflows/outreach-monitoring-sop.md"
  "./projects/shared/lead-scraper/workflows/apollo-credit-efficient-workflow.md"
  "./projects/shared/lead-scraper/QUICK-START.md"
  "./projects/shared/lead-scraper/BILLING-MONITOR-QUICK-START.md"
  "./projects/shared/lead-scraper/EXECUTIVE-SUMMARY.md"
  "./projects/shared/lead-scraper/OPTIMIZATION-PLAYBOOK.md"
  "./projects/shared/lead-scraper/ROOT-CAUSE-ANALYSIS-FOLLOW-UP-FAILURE.md"
  "./projects/shared/lead-scraper/COMPREHENSIVE-SESSION-SUMMARY.md"
  "./projects/shared/lead-scraper/IMMEDIATE-FIXES-IMPLEMENTATION-PLAN.md"
  "./projects/shared/lead-scraper/agent2/COMPLETION-SUMMARY.md"
  "./projects/shared/lead-scraper/AGENT-5-CAMPAIGN-AUTOMATION-PLAN.md"
  "./projects/shared/lead-scraper/AGENT-5-README.md"
  "./projects/shared/social-media-automation/TROUBLESHOOTING.md"
  "./projects/shared/social-media-automation/SCHEMA_FIX_SUMMARY.md"
  "./projects/shared/social-media-automation/HVAC-CAMPAIGN-IMPLEMENTATION.md"
  "./ralph/PROJECT_CATEGORIZATION.md"
  "./ralph/migrate_to_company_structure.py"
  "./ralph/CHECKPOINT_STORY_003.md"
  "./ralph/MIGRATION_SUMMARY.md"
  "./ralph/STORY_003_SUMMARY.md"
  "./ralph/MIGRATION_IMPACT_ANALYSIS.md"
  "./ralph/WORKSPACE_BEST_PRACTICES.md"
  "./ralph/MIGRATION_READINESS_SUMMARY.md"
  "./ralph/MIGRATION_PLAN.md"
  "./ralph/PRE_MIGRATION_CHECKLIST.md"
  "./ralph/create_vscode_workspaces.py"
  "./ralph/EXECUTION_STATUS.md"
  "./ralph/multi-company-folder-structure-prd.json"
  "./ralph/rollback_migration.py"
  "./docs/GOOGLE-CLOUD-BILLING-ALERTS-SETUP.md"
  "./docs/session-reports/GOOGLE-ANALYTICS-SETUP.md"
  "./docs/session-reports/2026-01-21-COMPLETE-RESTRUCTURE-SESSION.md"
  "./docs/restructuring/RESTRUCTURE-PROPOSAL-WITH-SAFEGUARDS.md"
  "./docs/restructuring/COMPANY-ASSET-DISTRIBUTION-ANALYSIS.md"
  "./docs/restructuring/CLICKUP-MIGRATION-NEEDED.md"
  "./docs/restructuring/FOLDER-STRUCTURE-APPENDIX.md"
  "./docs/restructuring/REORGANIZATION-COMPLETE.md"
  "./docs/restructuring/COMPREHENSIVE-RESTRUCTURE-PLAN.md"
  "./docs/restructuring/MIGRATION-EXECUTION-SUMMARY.md"
  "./docs/restructuring/FOLDER-RESTRUCTURE-DECISION-LOG.md"
  "./docs/restructuring/FOLDER-STRUCTURE.md"
  "./docs/restructuring/MIGRATION-COMPLETE-SUMMARY.md"
  "./docs/BILLING-ALERTS-SUMMARY.md"
  "./docs/GOOGLE-CLOUD-ACTION-PLAN.md"
  "./docs/GOOGLE-CLOUD-COST-ANALYSIS.md"
  "./scripts/verify-automation-tools.sh"
  "./scripts/migrate_company_centric_autonomous.py"
)

echo "Found ${#FILES_TO_FIX[@]} files to fix"
echo ""

for FILE in "${FILES_TO_FIX[@]}"; do
  if [ -f "$FILE" ]; then
    # Count occurrences before fix
    BEFORE_COUNT=$(grep -o "shared-multi-tenant" "$FILE" 2>/dev/null | wc -l | tr -d ' ')

    if [ "$BEFORE_COUNT" -gt 0 ]; then
      echo "Fixing: $FILE ($BEFORE_COUNT occurrences)"

      # Use sed to replace all occurrences
      # macOS requires '' after -i for in-place editing
      sed -i '' 's/shared-multi-tenant/shared/g' "$FILE"

      # Verify fix
      AFTER_COUNT=$(grep -o "shared-multi-tenant" "$FILE" 2>/dev/null | wc -l | tr -d ' ')

      if [ "$AFTER_COUNT" -eq 0 ]; then
        echo "  ✓ Fixed successfully"
        FIXED_COUNT=$((FIXED_COUNT + 1))
      else
        echo "  ⚠️ WARNING: Still has $AFTER_COUNT occurrences"
      fi
    else
      echo "Skipping: $FILE (no occurrences found)"
    fi
  else
    echo "⚠️ WARNING: File not found: $FILE"
  fi
  echo ""
done

echo "================================================"
echo "SUMMARY"
echo "================================================"
echo "Files fixed: $FIXED_COUNT / ${#FILES_TO_FIX[@]}"
echo ""
echo "Verifying fix..."
REMAINING=$(find . -type f \( -name "*.md" -o -name "*.sh" -o -name "*.py" -o -name "*.json" \) -not -path "*/\.*" -not -path "*/node_modules/*" -exec grep -l "shared-multi-tenant" {} \; | wc -l)
echo "Files still containing 'shared-multi-tenant': $REMAINING"

if [ "$REMAINING" -eq 0 ]; then
  echo ""
  echo "✅ SUCCESS: All references fixed!"
else
  echo ""
  echo "⚠️ WARNING: Some references remain. Running comprehensive check..."
  find . -type f \( -name "*.md" -o -name "*.sh" -o -name "*.py" -o -name "*.json" \) -not -path "*/\.*" -not -path "*/node_modules/*" -exec grep -l "shared-multi-tenant" {} \;
fi

echo ""
echo "Done!"
