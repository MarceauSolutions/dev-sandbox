# AI Services — Client Onboarding Email Template

**Send when**: Client payment is received
**Send from**: wmarceau@marceausolutions.com
**Subject**: Welcome to Marceau Solutions — Let's Get You Automated

---

Hi {{client_name}},

Welcome aboard — I'm excited to get started on {{service_name}} for {{business_name}}.

Here's exactly what happens next:

**This Week:**
1. **Complete the onboarding questionnaire** (5 minutes) — this gives me everything I need to build your system: {{questionnaire_link}}
2. **Book your kickoff call** — we'll do a 30-minute walkthrough of the plan and I'll collect any access credentials needed: {{calendly_kickoff_link}}

**Days 2-5:**
3. I build and test your complete system — you don't need to do anything during this phase
4. You'll get a progress update on Day 3

**Day 6:**
5. We do a live review walkthrough together — I'll show you everything and make any adjustments

**Day 7:**
6. Your system goes live. I monitor it closely for the first 2 weeks to ensure everything runs perfectly.

**Ongoing:**
- Monthly performance report delivered to your inbox
- Dedicated support via email or phone — (239) 398-5676
- System optimization based on real data (included in your monthly plan)

**Your Access Credentials:**
Once the system is live, you'll receive a separate email with:
- Dashboard login URL and credentials
- Reporting dashboard access
- Support contact information

**One Important Note:**
My guarantee stands — {{guarantee_statement}}. I'm personally invested in making this work for {{business_name}}.

If you have any questions before the kickoff call, reply to this email or call me directly at (239) 398-5676.

Let's build something great.

William Marceau
Marceau Solutions
wmarceau@marceausolutions.com | marceausolutions.com | (239) 398-5676

---

## Template Variables

| Variable | Description | Example |
|---|---|---|
| `{{client_name}}` | Client's first name | "Sarah" |
| `{{business_name}}` | Business name | "Naples Family Dental" |
| `{{service_name}}` | Service purchased | "AI Receptionist" |
| `{{questionnaire_link}}` | Jotform/Typeform link | TBD — create intake form |
| `{{calendly_kickoff_link}}` | Calendly for 30-min kickoff | TBD — create Calendly event type |
| `{{guarantee_statement}}` | The guarantee for their tier | "10 qualified leads in 30 days or I work free until it does" |

## Automation Notes

- This email should be triggered automatically when a Stripe payment is received
- Can be set up as an n8n workflow: Stripe webhook → template merge → Gmail send
- Follow-up reminder if questionnaire not completed within 48 hours
