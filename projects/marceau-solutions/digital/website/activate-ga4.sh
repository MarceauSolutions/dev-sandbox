#!/bin/bash
# Activate Google Analytics GA4
# Usage: ./activate-ga4.sh G-XXXXXXXXXX

set -e  # Exit on error

if [ -z "$1" ]; then
    echo "❌ Error: Measurement ID required"
    echo ""
    echo "Usage: ./activate-ga4.sh G-XXXXXXXXXX"
    echo ""
    echo "Get your Measurement ID from: https://analytics.google.com"
    echo "  Admin → Data Streams → Your Stream → Measurement ID"
    echo ""
    exit 1
fi

MEASUREMENT_ID=$1

# Validate format
if [[ ! "$MEASUREMENT_ID" =~ ^G-[A-Z0-9]{10}$ ]]; then
    echo "❌ Error: Invalid Measurement ID format"
    echo "Expected format: G-XXXXXXXXXX (G- followed by 10 characters)"
    echo "Example: G-ABCDE12345"
    exit 1
fi

echo "🚀 Activating GA4 with Measurement ID: $MEASUREMENT_ID"
echo ""

# Check if we're in the right directory
if [ ! -f "index.html" ]; then
    echo "❌ Error: index.html not found. Are you in the marceausolutions.com directory?"
    exit 1
fi

# Backup files before modifying
BACKUP_DIR=".ga4-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "📦 Creating backup in $BACKUP_DIR..."
for file in index.html contact.html pricing.html terms.html privacy.html; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/"
        echo "  ✓ Backed up $file"
    fi
done
echo ""

# Process each HTML file
FILES_UPDATED=0
for file in index.html contact.html pricing.html terms.html privacy.html; do
    if [ ! -f "$file" ]; then
        echo "⚠️  Warning: $file not found, skipping..."
        continue
    fi

    echo "Processing $file..."

    # Create temporary file
    TMP_FILE="${file}.tmp"

    # Remove comment markers and replace placeholder
    # This handles the multi-line comment block
    awk -v mid="$MEASUREMENT_ID" '
    BEGIN { in_ga_comment = 0; skip_line = 0 }

    # Detect start of GA4 comment block
    /<!-- Google Analytics GA4 -->/ {
        print "    <!-- Google Analytics GA4 -->"
        in_ga_comment = 1
        next
    }

    # Skip TODO comment line
    in_ga_comment && /<!-- TODO:/ {
        next
    }

    # Skip activation instruction line
    in_ga_comment && /<!-- To activate:/ {
        next
    }

    # Remove opening comment marker
    in_ga_comment && /^[[:space:]]*<!--[[:space:]]*$/ {
        next
    }

    # Remove closing comment marker and exit comment block
    in_ga_comment && /^[[:space:]]*-->[[:space:]]*$/ {
        in_ga_comment = 0
        next
    }

    # Process lines inside GA4 block
    in_ga_comment {
        # Replace placeholder with real Measurement ID
        gsub(/G-XXXXXXXXXX/, mid)
        print
        next
    }

    # Print all other lines as-is
    { print }
    ' "$file" > "$TMP_FILE"

    # Replace original file
    mv "$TMP_FILE" "$file"

    echo "  ✅ GA4 activated in $file"
    FILES_UPDATED=$((FILES_UPDATED + 1))
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Google Analytics GA4 activated successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Summary:"
echo "  • Files updated: $FILES_UPDATED"
echo "  • Measurement ID: $MEASUREMENT_ID"
echo "  • Backup location: $BACKUP_DIR/"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Review changes:"
echo "   git diff"
echo ""
echo "2. Test locally:"
echo "   open index.html"
echo "   (Check browser console for GA4 initialization)"
echo ""
echo "3. Commit changes:"
echo "   git add -A"
echo "   git commit -m 'feat: Activate GA4 tracking ($MEASUREMENT_ID)'"
echo ""
echo "4. Push to production:"
echo "   git push"
echo ""
echo "5. Verify tracking (wait 30-60 seconds after deployment):"
echo "   • Visit https://marceausolutions.com"
echo "   • Open GA4 Real-time report"
echo "   • You should see your visit appear within seconds"
echo ""
echo "📚 Testing Guide:"
echo "   See GA4-ACTIVATION-GUIDE.md for detailed verification steps"
echo ""
echo "🔄 Rollback (if needed):"
echo "   cp $BACKUP_DIR/*.html ."
echo ""
