# Square Foot Shipping - POC Lead Tracking

## Purpose

This directory tracks leads and deals for the Square Foot Shipping proof-of-concept (POC). The goal is to validate market demand before building the full product.

## Success Metrics

The POC is considered successful if we achieve:

- **50+ leads** - Demonstrates sufficient market interest
- **10+ quotes delivered** - Shows conversion from interest to action
- **2+ deals closed** - Validates willingness to pay
- **$5,000+ revenue** - Proves economic viability

## Daily Workflow

### 1. Log New Leads

When a lead comes in from any source (referral, cold outreach, website, etc.), add a row to `lead-tracking.csv`:

```csv
2026-01-20,Referral,Acme Industries,John Smith,+1-555-0100,john@acme.com,FALSE,FALSE,,,,"Referred by Mike - needs weekly Naples to Miami shipments"
```

### 2. Track Quote Requests

When a lead requests a quote, update their row:

```csv
2026-01-20,Referral,Acme Industries,John Smith,+1-555-0100,john@acme.com,TRUE,FALSE,,,,"Requested quote for 10 pallets Naples->Miami"
```

### 3. Log Quote Delivery

When you deliver a quote, update:

```csv
2026-01-20,Referral,Acme Industries,John Smith,+1-555-0100,john@acme.com,TRUE,TRUE,850,,,"Quoted $850 for 10 pallets - waiting for decision"
```

### 4. Record Closed Deals

When a deal closes, mark it complete:

```csv
2026-01-20,Referral,Acme Industries,John Smith,+1-555-0100,john@acme.com,TRUE,TRUE,850,TRUE,850,"First shipment scheduled for Jan 25"
```

## Lead Sources

Common lead sources to track:

- **Referral** - From existing network
- **Cold Outreach** - Proactive SMS/email
- **Website** - Organic traffic or ads
- **LinkedIn** - Direct messages
- **Phone** - Inbound calls
- **Event** - Trade shows, networking events

## Calculating Metrics

### Lead Conversion Rate
`(Quotes Requested / Total Leads) * 100`

### Quote-to-Deal Rate
`(Deals Closed / Quotes Delivered) * 100`

### Average Deal Size
`Total Revenue / Deals Closed`

### Revenue per Lead
`Total Revenue / Total Leads`

## Review Cadence

- **Daily**: Add new leads, update quote status
- **Weekly**: Calculate conversion rates, review metrics against goals
- **Monthly**: Full POC assessment - are we on track for success metrics?

## Example Entries

```csv
Date,Lead_Source,Company_Name,Contact_Name,Phone,Email,Quote_Requested,Quote_Delivered,Quote_Amount,Deal_Closed,Revenue,Notes
2026-01-20,Referral,Acme Industries,John Smith,+1-555-0100,john@acme.com,TRUE,TRUE,850,TRUE,850,First shipment scheduled for Jan 25
2026-01-21,Cold Outreach,Naples Furniture Co,Sarah Johnson,+1-555-0101,sarah@naplesfurn.com,TRUE,TRUE,1200,FALSE,,"Quoted $1200 - considering options"
2026-01-21,Website,Coastal Distributors,Mike Davis,+1-555-0102,mike@coastal.com,TRUE,FALSE,,,,"Requested quote for LTL Naples->Orlando"
2026-01-22,LinkedIn,Bay Area Logistics,Amanda Lee,+1-555-0103,amanda@bayarea.com,FALSE,FALSE,,,,"Interested - wants to schedule call"
```

## Files

- `lead-tracking.csv` - Main tracking spreadsheet (update daily)
- `README.md` - This file (documentation)

## Tips

1. **Be consistent**: Update the spreadsheet daily, even if there are no changes
2. **Add context**: Use the Notes field to capture important details
3. **Track everything**: Even leads that don't convert provide valuable data
4. **Be honest**: Don't inflate numbers - accurate data drives good decisions
5. **Celebrate wins**: Each deal closed is validation of the business model

## Questions?

If you're unsure how to categorize something or which metrics to focus on, refer to the success criteria above. The goal is to quickly validate whether this business model works before investing in full development.
