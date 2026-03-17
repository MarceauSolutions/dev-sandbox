#!/bin/bash
# Restructure Client Folders - Move out of dev-sandbox
# Created: 2026-01-19
# Purpose: Separate client work from tools/products

set -e  # Exit on error

echo "=================================================="
echo "FOLDER RESTRUCTURING - Client Work Separation"
echo "=================================================="
echo ""
echo "Goal: Move client folders OUT of dev-sandbox"
echo "Structure:"
echo "  - dev-sandbox/ = Tools, products, fun ideas"
echo "  - swflorida-comfort-hvac/ = Client POC #1"
echo "  - square-foot-shipping/ = Client POC #2"
echo ""

# Parent directory
PARENT_DIR="/Users/williammarceaujr."

# Check if we're in dev-sandbox
if [[ "$PWD" != "$PARENT_DIR/dev-sandbox" ]]; then
    echo "⚠️  Please run this script from dev-sandbox directory"
    echo "Current directory: $PWD"
    echo "Expected: $PARENT_DIR/dev-sandbox"
    exit 1
fi

echo "✅ Running from correct directory: $PWD"
echo ""

# Function to create client repo
create_client_repo() {
    local client_name=$1
    local client_dir="$PARENT_DIR/$client_name"

    echo "=================================================="
    echo "Creating: $client_name"
    echo "=================================================="

    # Create directory
    if [ -d "$client_dir" ]; then
        echo "⚠️  Directory already exists: $client_dir"
        read -p "Overwrite? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Skipped $client_name"
            return
        fi
        rm -rf "$client_dir"
    fi

    mkdir -p "$client_dir"
    echo "✅ Created directory: $client_dir"

    # Initialize git repo
    cd "$client_dir"
    git init
    echo "✅ Initialized git repo"

    # Create .gitignore
    cat > .gitignore <<EOF
# Environment variables
.env
*.env

# Credentials
credentials.json
token.json
*.pem
*.key

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
.venv/
venv/

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# Temporary files
.tmp/
temp/
EOF
    echo "✅ Created .gitignore"

    cd "$PARENT_DIR/dev-sandbox"
}

# Create HVAC client folder
create_hvac_folder() {
    local client_dir="$PARENT_DIR/swflorida-comfort-hvac"

    create_client_repo "swflorida-comfort-hvac"

    cd "$client_dir"

    # Create folder structure
    mkdir -p voice-ai-config
    mkdir -p case-study
    mkdir -p crm-setup

    # Create README
    cat > README.md <<EOF
# SW Florida Comfort HVAC - Voice AI Implementation

**Client:** SW Florida Comfort HVAC (William Marceau Sr.)
**Project Type:** Proof of Concept (POC #1)
**Duration:** 30 days (Jan 19 - Feb 18, 2026)
**Goal:** Prove Voice AI can recover missed calls and generate revenue

---

## Project Overview

**Problem:**
- Missing 30-40% of calls when technicians on job sites
- Lost revenue estimated at \$50K-\$100K annually
- No after-hours coverage

**Solution:**
- Voice AI on main business line
- 24/7 call answering and appointment booking
- Emergency vs routine call routing

**Expected Results:**
- 90%+ call answer rate
- 15+ appointments booked per month
- \$8K-20K revenue recovered in first 30 days

---

## Folder Structure

\`\`\`
swflorida-comfort-hvac/
├── voice-ai-config/        # Twilio configuration, prompts
├── case-study/             # Tracking data, results, case study writeup
├── crm-setup/              # CRM integration (if needed)
└── README.md               # This file
\`\`\`

---

## Voice AI Configuration

**Phone Number:** [Sr.'s business line]
**Twilio Number:** +1 855 239 9364 (forwarding)

**Call Flow:**
1. Customer calls business line
2. Forwards to Twilio Voice AI
3. AI determines call type (emergency, routine, inquiry)
4. Books appointment or escalates to human

**Prompts:** See \`voice-ai-config/prompts.json\`

---

## Case Study Tracking

**Metrics tracked:**
- Total calls received
- AI answer rate (target: >90%)
- Appointments booked (target: 15+/month)
- Revenue recovered (target: \$8K-20K/month)
- Customer satisfaction

**Tracking file:** \`case-study/call-tracking.csv\`

---

## Timeline

- **Week 1 (Jan 19-25):** Setup Voice AI, begin monitoring
- **Week 2 (Jan 26 - Feb 1):** Monitor results, optimize prompts
- **Week 3 (Feb 2-8):** Continue monitoring, draft case study
- **Week 4 (Feb 9-15):** Finalize case study, make decision

---

## Success Criteria

- ✅ AI answers 90%+ of calls
- ✅ 15+ appointments booked
- ✅ \$8K-20K revenue recovered
- ✅ Sr. reports positive customer feedback
- ✅ Compelling case study for other HVAC companies

---

## Next Steps (After POC)

**If successful:**
- Use case study to target 100 Naples HVAC companies
- Offer: \$15K implementation + \$3K/month retainer
- Goal: 3-4 clients by Month 6

**Repository:** Separate from dev-sandbox tools
**Tools used:** From \`/Users/williammarceaujr./dev-sandbox/projects/ai-customer-service/\`
EOF

    # Create voice-ai-config/README.md
    cat > voice-ai-config/README.md <<EOF
# Voice AI Configuration for SW Florida Comfort HVAC

## Twilio Setup

**Account:** (See .env in dev-sandbox)
**Phone Number:** +1 855 239 9364
**Forwarding From:** Sr.'s business line

## Call Prompts

See \`prompts.json\` for full configuration.

**Prompt Types:**
1. **Greeting:** "Thank you for calling SW Florida Comfort HVAC..."
2. **Emergency routing:** "Is this an emergency? Say yes or no."
3. **Appointment booking:** "I can schedule a technician. What day works best?"
4. **Escalation:** "Let me connect you with a technician now."

## Testing

**Test calls:**
1. Call from external number
2. Verify AI answers within 2 rings
3. Test emergency scenario
4. Test routine appointment booking
5. Verify calendar integration
EOF

    # Create case-study/call-tracking.csv header
    cat > case-study/call-tracking.csv <<EOF
Date,Time,Call Type,AI Handled,Appointment Booked,Estimated Value,Notes
EOF

    # Create initial case study draft
    cat > case-study/CASE-STUDY-DRAFT.md <<EOF
# Case Study: SW Florida Comfort HVAC - Voice AI POC

**Duration:** 30 days (Jan 19 - Feb 18, 2026)
**Status:** In Progress

---

## Week 1 Results (Jan 19-25)

[To be filled in]

## Week 2 Results (Jan 26 - Feb 1)

[To be filled in]

## Week 3 Results (Feb 2-8)

[To be filled in]

## Week 4 Results (Feb 9-15)

[To be filled in]

---

## Final Results (30-Day Summary)

[To be completed end of POC]
EOF

    # Initial commit
    git add .
    git commit -m "Initial POC setup for SW Florida Comfort HVAC"

    echo "✅ HVAC folder structure created"
    echo ""

    cd "$PARENT_DIR/dev-sandbox"
}

# Create Shipping client folder
create_shipping_folder() {
    local client_dir="$PARENT_DIR/square-foot-shipping"

    create_client_repo "square-foot-shipping"

    cd "$client_dir"

    # Create folder structure
    mkdir -p lead-gen
    mkdir -p quote-automation
    mkdir -p case-study

    # Create README
    cat > README.md <<EOF
# Square Foot Shipping - Lead Gen & Quote Automation

**Client:** Square Foot Shipping (William George)
**Project Type:** Proof of Concept (POC #2)
**Duration:** 30 days (Jan 19 - Feb 18, 2026)
**Goal:** Prove lead gen + quote automation saves time and generates revenue

---

## Project Overview

**Problem:**
- Manual lead generation (time-consuming)
- Manual quote preparation (10-20 hours/week)
- No systematic follow-up process

**Solution:**
- Automated lead scraping (e-commerce sellers needing shipping)
- Quote request automation (form or Voice AI)
- Lead tracking and follow-up system

**Expected Results:**
- 50+ qualified leads generated
- 10+ quote requests handled
- 2+ deals closed (\$5K+ revenue)
- 10+ hours/week saved

---

## Folder Structure

\`\`\`
square-foot-shipping/
├── lead-gen/               # Lead scraping, outreach templates
├── quote-automation/       # Quote request form, workflow
├── case-study/             # Tracking data, results
└── README.md               # This file
\`\`\`

---

## Lead Generation

**Target Audience:**
- E-commerce sellers (Shopify, Amazon)
- Shipping volume: 100-1000 packages/month
- Currently using retail shipping (USPS, UPS, FedEx)
- Location: US-based

**Lead Sources:**
- Shopify store directory
- Amazon seller lists
- E-commerce forums/communities

**Outreach:**
- Cold email (Apollo.io sequences)
- LinkedIn outreach
- Quote request form on website

---

## Quote Automation

**Current Process (Manual):**
1. Receive quote request (email/phone)
2. Gather shipment details
3. Check with carriers for rates
4. Prepare quote (30-60 min)
5. Send to customer
6. Follow up if no response

**Automated Process:**
1. Customer fills out form (dimensions, weight, destination, frequency)
2. System generates instant quote OR routes to William George for complex quotes
3. Automated follow-up sequence (Day 1, Day 3, Day 7)

---

## Case Study Tracking

**Metrics tracked:**
- Leads generated (target: 50+)
- Quote requests (target: 10+)
- Quotes delivered (target: 8+)
- Deals closed (target: 2+)
- Revenue generated (target: \$5K+)
- Time saved (target: 10+ hours/week)

**Tracking file:** \`case-study/lead-tracking.csv\`

---

## Timeline

- **Week 1 (Jan 19-25):** Setup lead scraper, create quote form
- **Week 2 (Jan 26 - Feb 1):** Scrape 50 leads, send outreach, track quote requests
- **Week 3 (Feb 2-8):** Scrape 50 more leads (100 total), optimize automation
- **Week 4 (Feb 9-15):** Finalize case study, make decision

---

## Success Criteria

- ✅ 50+ qualified leads generated
- ✅ 10+ quote requests handled
- ✅ 2+ deals closed
- ✅ William George saves 10+ hours/week
- ✅ Compelling case study for other shipping brokers

---

## Next Steps (After POC)

**If successful:**
- Use case study to target 50+ shipping brokers nationwide
- Offer: \$15K implementation + \$3K/month retainer
- Goal: 2-3 shipping clients by Month 6

**Repository:** Separate from dev-sandbox tools
**Tools used:** From \`/Users/williammarceaujr./dev-sandbox/projects/lead-scraper/\`
EOF

    # Create lead-gen/README.md
    cat > lead-gen/README.md <<EOF
# Lead Generation for Square Foot Shipping

## Target Audience

**Ideal Customer Profile (ICP):**
- E-commerce sellers (Shopify, Amazon, WooCommerce)
- Shipping volume: 100-1000 packages/month
- Currently using retail shipping (overpaying)
- Annual shipping spend: \$10K-$100K
- US-based

## Lead Sources

1. **Shopify Store Directory**
   - Scrape public Shopify stores
   - Filter by product categories (physical goods)
   - Estimate shipping volume from product count

2. **Amazon Seller Lists**
   - Scrape FBA sellers (might want FBM option)
   - Look for sellers with 100+ reviews (active)

3. **E-commerce Communities**
   - Reddit: r/ecommerce, r/shopify
   - Facebook groups

## Lead Scraping Script

Use: \`/Users/williammarceaujr./dev-sandbox/projects/lead-scraper/src/scraper.py\`

Example:
\`\`\`bash
python -m src.scraper scrape \\
  --type shopify \\
  --category "apparel" \\
  --limit 50 \\
  --output lead-gen/scraped-leads.json
\`\`\`

## Outreach Templates

See \`outreach-templates.md\`
EOF

    # Create case-study/lead-tracking.csv header
    cat > case-study/lead-tracking.csv <<EOF
Date,Lead Source,Company Name,Contact,Quote Requested,Quote Delivered,Deal Closed,Revenue,Notes
EOF

    # Create initial case study draft
    cat > case-study/CASE-STUDY-DRAFT.md <<EOF
# Case Study: Square Foot Shipping - Lead Gen & Quote Automation POC

**Duration:** 30 days (Jan 19 - Feb 18, 2026)
**Status:** In Progress

---

## Week 1 Results (Jan 19-25)

[To be filled in]

## Week 2 Results (Jan 26 - Feb 1)

[To be filled in]

## Week 3 Results (Feb 2-8)

[To be filled in]

## Week 4 Results (Feb 9-15)

[To be filled in]

---

## Final Results (30-Day Summary)

[To be completed end of POC]
EOF

    # Initial commit
    git add .
    git commit -m "Initial POC setup for Square Foot Shipping"

    echo "✅ Shipping folder structure created"
    echo ""

    cd "$PARENT_DIR/dev-sandbox"
}

# Main execution
echo "Creating client folders outside dev-sandbox..."
echo ""

create_hvac_folder
create_shipping_folder

echo "=================================================="
echo "FOLDER RESTRUCTURING COMPLETE"
echo "=================================================="
echo ""
echo "New structure:"
echo "  /Users/williammarceaujr./"
echo "  ├── dev-sandbox/                  (tools, products, fun ideas)"
echo "  ├── swflorida-comfort-hvac/       (POC #1 - separate repo)"
echo "  └── square-foot-shipping/         (POC #2 - separate repo)"
echo ""
echo "Next steps:"
echo "  1. cd /Users/williammarceaujr./swflorida-comfort-hvac"
echo "  2. Start POC setup (voice AI configuration)"
echo "  3. cd /Users/williammarceaujr./square-foot-shipping"
echo "  4. Start POC setup (lead gen automation)"
echo ""
echo "✅ All client folders created with separate git repos"
echo "✅ No nested repos (clean structure)"
echo ""
