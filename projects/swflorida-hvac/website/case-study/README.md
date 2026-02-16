# SW Florida Comfort HVAC - Voice AI POC Call Tracking

## Overview

This directory contains call tracking data for the 45-day Proof of Concept (POC) with SW Florida Comfort HVAC. The goal is to demonstrate that Voice AI can handle 90%+ of inbound calls and generate $8K-20K in new revenue.

## Success Metrics

**Primary Goals:**
- **Answer Rate**: 90%+ of calls answered by AI (vs current 40-60% human answer rate)
- **Appointments Booked**: 15+ qualified appointments during POC period
- **Revenue Generated**: $8,000 - $20,000 in new business
- **Cost Efficiency**: Eliminate need for receptionist ($15/hr = $2,600/month saved)

**Secondary Metrics:**
- Customer satisfaction (qualitative feedback)
- Average handling time per call
- Transfer rate to Bill (should be <20% for qualified issues only)
- After-hours coverage (currently 0%, target 100%)

## Daily Tracking Instructions

### How to Log a Call

1. Open `call-tracking.csv` in Excel, Numbers, or any spreadsheet app
2. Add a new row with the following information:

| Column | What to Enter | Examples |
|--------|---------------|----------|
| **Date** | Date of call (YYYY-MM-DD) | 2026-01-20 |
| **Time** | Time of call (HH:MM 24hr) | 09:15, 14:30, 18:45 |
| **Caller_Phone** | Phone number with area code | +1-239-555-0100 |
| **Call_Type** | New_Customer, Existing_Customer, Emergency, Vendor, Spam | New_Customer |
| **AI_Handled** | Yes, No, Partial | Yes |
| **Appointment_Booked** | Yes, No | Yes |
| **Appointment_DateTime** | When scheduled (YYYY-MM-DD HH:MM) | 2026-01-22 14:00 |
| **Estimated_Value** | Estimated job value | $2500, $500, $8000 |
| **Transferred_to_Bill** | Yes, No | No |
| **Notes** | Brief description of call | AC repair - unit not cooling |

### Call Type Definitions

- **New_Customer**: First-time caller, potential new customer
- **Existing_Customer**: Previous customer calling for service/maintenance
- **Emergency**: Urgent service request (no AC in summer, heat in winter)
- **Vendor**: Supplier, parts vendor, or business call
- **Spam**: Telemarketer, robocall, wrong number

### AI_Handled Values

- **Yes**: AI successfully handled entire call, customer satisfied
- **No**: AI failed or call went to voicemail (count as missed)
- **Partial**: AI started call but transferred to Bill

### Estimated_Value Guidelines

Use these estimates based on service type:
- **Diagnostic/Service Call**: $150-300
- **Repair (minor)**: $300-800
- **Repair (major)**: $800-2,500
- **System Replacement**: $5,000-15,000
- **Maintenance Contract**: $200-500/year
- **Emergency Service**: Add 50% premium

If uncertain, use conservative estimate. Update after job completion.

## Weekly Review Process

Every Friday, review the week's data:

1. **Calculate Metrics**:
   ```
   Answer Rate = (AI_Handled Yes + Partial) / Total Calls
   Appointment Rate = Appointments Booked / Total Calls
   Transfer Rate = Transferred_to_Bill Yes / Total Calls
   Total Pipeline = Sum of Estimated_Value where Appointment_Booked = Yes
   ```

2. **Identify Patterns**:
   - What time of day do most calls come in?
   - What types of calls does AI handle best?
   - When does AI transfer to Bill? (Look for patterns to improve)
   - What's the conversion rate from appointment to revenue?

3. **Update Bill**:
   - Share weekly summary with Bill
   - Discuss any AI performance issues
   - Celebrate wins (appointments booked, revenue generated)

## End-of-POC Analysis (Day 45)

At the end of 45 days, calculate final metrics:

```
Total Calls Received: _____
AI Answer Rate: _____%
Appointments Booked: _____
Total Revenue Generated: $_____
Cost Savings (vs receptionist): $_____
ROI: _____%
```

**Decision Criteria for Full Rollout:**
- If answer rate >90% AND revenue >$8K → Strong YES
- If answer rate 80-90% OR revenue $5K-8K → Qualified YES (negotiate pricing)
- If answer rate <80% OR revenue <$5K → Needs improvement

## Files in This Directory

- `call-tracking.csv` - Main call log (update daily)
- `README.md` - This file (instructions)
- `weekly-summaries/` - Weekly performance reports (create as needed)
- `customer-feedback.md` - Qualitative feedback from callers (optional)

## Tips for Success

1. **Track Every Call**: Even spam/vendor calls help us understand volume
2. **Be Honest About AI Performance**: If AI messed up, mark it. We can only improve what we measure.
3. **Update Estimates**: When job completes, update Estimated_Value with actual revenue
4. **Note Edge Cases**: If AI struggled with something specific, note it. We can train for it.
5. **Celebrate Wins**: Every appointment booked is revenue that would've been missed!

## Questions or Issues?

Contact William:
- For tracking questions: Reference this README
- For AI performance issues: Note in CSV Notes column
- For urgent AI failures: Contact immediately + log in CSV

---

**POC Start Date**: 2026-01-20
**POC End Date**: 2026-03-06 (45 days)
**Current Status**: Active
