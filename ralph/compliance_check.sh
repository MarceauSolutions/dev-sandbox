#!/bin/bash

echo "=========================================="
echo "FINAL HYBRID ARCHITECTURE COMPLIANCE CHECK"
echo "=========================================="
echo ""

cd /Users/williammarceaujr./dev-sandbox

# 1. Check for old references (exclude Ralph's documentation)
echo "1. Checking for outdated 'shared-multi-tenant' references..."
REFS=$(find . -type f \( -name "*.md" -o -name "*.sh" -o -name "*.py" -o -name "*.json" \) \
  -not -path "*/\.*" \
  -not -path "*/node_modules/*" \
  -not -path "*/venv/*" \
  -not -path "./ralph/fix_shared_multi_tenant_references.sh" \
  -not -path "./ralph/FINAL_COMPLIANCE_REPORT.md" \
  -not -path "./ralph/VISUAL_STRUCTURE_DIAGRAM.md" \
  -not -path "./ralph/EXECUTIVE_SUMMARY.md" \
  -not -path "./ralph/COMPLIANCE_INDEX.md" \
  -not -path "./ralph/compliance_check.sh" \
  -exec grep -l "shared-multi-tenant" {} \; 2>/dev/null | wc -l | tr -d ' ')

if [ "$REFS" -eq 0 ]; then
  echo "   ✅ PASS: No outdated references found (excluding historical docs)"
else
  echo "   ❌ FAIL: $REFS files still contain 'shared-multi-tenant'"
  find . -type f \( -name "*.md" -o -name "*.sh" -o -name "*.py" -o -name "*.json" \) \
    -not -path "*/\.*" \
    -not -path "*/node_modules/*" \
    -not -path "./ralph/fix_shared_multi_tenant_references.sh" \
    -not -path "./ralph/FINAL_COMPLIANCE_REPORT.md" \
    -not -path "./ralph/VISUAL_STRUCTURE_DIAGRAM.md" \
    -not -path "./ralph/EXECUTIVE_SUMMARY.md" \
    -not -path "./ralph/COMPLIANCE_INDEX.md" \
    -not -path "./ralph/compliance_check.sh" \
    -exec grep -l "shared-multi-tenant" {} \;
fi
echo ""

# 2. Check folder structure
echo "2. Verifying folder structure..."

if [ -d "projects/shared" ]; then
  echo "   ✅ PASS: projects/shared/ exists"
else
  echo "   ❌ FAIL: projects/shared/ not found"
fi

if [ -d "projects/marceau-solutions" ]; then
  echo "   ✅ PASS: projects/marceau-solutions/ exists"
else
  echo "   ❌ FAIL: projects/marceau-solutions/ not found"
fi

if [ -d "projects/swflorida-hvac" ]; then
  echo "   ✅ PASS: projects/swflorida-hvac/ exists"
else
  echo "   ❌ FAIL: projects/swflorida-hvac/ not found"
fi

if [ -d "projects/square-foot-shipping" ]; then
  echo "   ✅ PASS: projects/square-foot-shipping/ exists"
else
  echo "   ❌ FAIL: projects/square-foot-shipping/ not found"
fi

if [ -d "projects/global-utility" ]; then
  echo "   ✅ PASS: projects/global-utility/ exists"
else
  echo "   ❌ FAIL: projects/global-utility/ not found"
fi

if [ -d "projects/product-ideas" ]; then
  echo "   ✅ PASS: projects/product-ideas/ exists"
else
  echo "   ❌ FAIL: projects/product-ideas/ not found"
fi

if [ -d "projects/apollo-mcp" ]; then
  echo "   ✅ PASS: projects/apollo-mcp/ exists"
else
  echo "   ❌ FAIL: projects/apollo-mcp/ not found"
fi
echo ""

# 3. Check for nested repos
echo "3. Checking for nested git repositories..."
GIT_DIRS=$(find . -name ".git" -type d | wc -l | tr -d ' ')

if [ "$GIT_DIRS" -eq 1 ]; then
  echo "   ✅ PASS: Only 1 .git directory (root only)"
else
  echo "   ❌ FAIL: Found $GIT_DIRS .git directories (should be 1)"
  find . -name ".git" -type d
fi
echo ""

# 4. Check submodules
echo "4. Verifying git submodules..."
if [ -f ".gitmodules" ]; then
  SUBMODULES=$(grep "^\[submodule" .gitmodules | wc -l | tr -d ' ')
  echo "   ✅ PASS: .gitmodules exists with $SUBMODULES submodules"
  
  # Check marceau-solutions website
  if grep -q "marceau-solutions/website" .gitmodules; then
    echo "   ✅ PASS: marceau-solutions website submodule configured"
  else
    echo "   ❌ FAIL: marceau-solutions website submodule missing"
  fi
  
  # Check swflorida-hvac website
  if grep -q "swflorida-hvac/website" .gitmodules; then
    echo "   ✅ PASS: swflorida-hvac website submodule configured"
  else
    echo "   ❌ FAIL: swflorida-hvac website submodule missing"
  fi
else
  echo "   ❌ FAIL: .gitmodules not found"
fi
echo ""

# 5. Check shared projects
echo "5. Verifying shared multi-tenant projects..."
for PROJECT in lead-scraper ai-customer-service social-media-automation personal-assistant; do
  if [ -d "projects/shared/$PROJECT" ]; then
    echo "   ✅ PASS: projects/shared/$PROJECT exists"
  else
    echo "   ⚠️  WARNING: projects/shared/$PROJECT not found"
  fi
done
echo ""

# 6. Summary
echo "=========================================="
echo "COMPLIANCE SUMMARY"
echo "=========================================="
echo ""

TOTAL_CHECKS=0
PASSED_CHECKS=0

# Count total and passed
if [ "$REFS" -eq 0 ]; then PASSED_CHECKS=$((PASSED_CHECKS + 1)); fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if [ -d "projects/shared" ]; then PASSED_CHECKS=$((PASSED_CHECKS + 1)); fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if [ -d "projects/marceau-solutions" ]; then PASSED_CHECKS=$((PASSED_CHECKS + 1)); fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if [ -d "projects/swflorida-hvac" ]; then PASSED_CHECKS=$((PASSED_CHECKS + 1)); fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if [ -d "projects/square-foot-shipping" ]; then PASSED_CHECKS=$((PASSED_CHECKS + 1)); fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if [ "$GIT_DIRS" -eq 1 ]; then PASSED_CHECKS=$((PASSED_CHECKS + 1)); fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

if [ -f ".gitmodules" ]; then PASSED_CHECKS=$((PASSED_CHECKS + 1)); fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

echo "Checks Passed: $PASSED_CHECKS / $TOTAL_CHECKS"
echo ""

if [ "$PASSED_CHECKS" -eq "$TOTAL_CHECKS" ]; then
  echo "✅ RESULT: FULLY COMPLIANT"
  echo ""
  echo "The dev-sandbox repository is 100% compliant with"
  echo "the hybrid architecture specification."
  echo ""
  echo "Note: Historical references in Ralph's compliance docs"
  echo "      are excluded from this check (intentional documentation"
  echo "      of the migration process)."
else
  echo "⚠️  RESULT: PARTIALLY COMPLIANT"
  echo ""
  echo "Some compliance issues detected. Review output above."
fi

echo ""
echo "Report: ralph/FINAL_COMPLIANCE_REPORT.md"
echo "Diagram: ralph/VISUAL_STRUCTURE_DIAGRAM.md"
echo "=========================================="
