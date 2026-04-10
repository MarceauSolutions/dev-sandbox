# Directive: Sales CRM Management

## Goal
Manage sales pipeline in ClickUp, tracking leads from initial contact through closed won/lost.

## Sales Pipeline Stages

1. **Intake** - New leads and initial contact
2. **Qualification** - Qualifying leads and understanding needs
3. **Meeting Booked** - Discovery/kickoff call scheduled
4. **Proposal Sent** - Proposal or quote delivered
5. **Negotiation** - Discussing terms and pricing
6. **Closed Won** - Deal won - contract signed!
7. **Closed Lost** - Deal lost - analyze why

## Common Operations

### Add New Lead
**User says**: "Add new lead [Name] with email [email] phone [phone] for [Project Type] budget [amount]"

**Customer Information to Capture**:
- **Name** (required)
- **Email** (important for outreach)
- **Phone** (for calls)
- **Company** (if applicable)
- **Budget** (helps qualify)
- **Project Description** (what they need)
- **Timeline** (when they need it)
- **Referral Source** (how they found you)
- **Notes** (any additional context)

**Process**:
1. Extract customer information from request
2. Create task in "1. Intake" list using `add_lead.py`
3. Task includes formatted description with all customer data
4. Optionally send onboarding email
5. Return ClickUp task URL

**Example**:
```bash
python execution/add_lead.py \
  --name "Sarah Johnson" \
  --email "sarah@company.com" \
  --phone "555-1234" \
  --budget "15000" \
  --project "E-commerce website redesign" \
  --timeline "3 months" \
  --source "LinkedIn" \
  --notes "Interested in Shopify integration"
```

**Interactive Mode** (when details are unclear):
```bash
python execution/add_lead.py --interactive
```

### Move Lead Through Pipeline
**User says**: "Move [Name] to [Stage]"

**Process**:
1. Find task by name
2. Update task to move to new list
3. Confirm move

**Stage List IDs**:
- Intake: 901709133703
- Qualification: 901709133704
- Meeting Booked: 901709133705
- Proposal Sent: 901709133706
- Negotiation: 901709133707
- Closed Won: 901709133708
- Closed Lost: 901709133709

### View Pipeline
**User says**: "Show me all deals in [Stage]" or "What's in the pipeline?"

**Process**:
1. List tasks in specified stage (or all stages)
2. Display with client names and status
3. Show counts per stage

### Mark Deal as Won/Lost
**User says**: "Mark [Name] as closed won" or "Lost the [Name] deal"

**Process**:
1. Move task to appropriate list (Closed Won or Closed Lost)
2. If Closed Won: Trigger onboarding workflow
3. If Closed Lost: Add notes about why (for analysis)

## Integrated Workflows

### New Lead → Onboarding
1. User: "Add new lead john@example.com with name John Smith for mobile app"
2. Create task in Intake
3. Send onboarding email with Calendly link
4. Return confirmation with both ClickUp URL and email status

### Meeting Booked → Update CRM
1. User: "Move John Smith to Meeting Booked"
2. Update task to Meeting Booked list
3. Optionally add meeting details to task description

### Closed Won → Client Onboarding
1. User: "Mark Sarah as closed won"
2. Move to Closed Won list
3. Trigger full client onboarding sequence
4. Create project tasks in separate project management area

## Reporting & Analytics

### Pipeline Overview
**User says**: "Show me the pipeline summary"

**Output**:
- Intake: 5 leads
- Qualification: 3 leads
- Meeting Booked: 2 leads
- Proposal Sent: 4 leads
- Negotiation: 1 lead
- Closed Won (this month): 3 deals
- Closed Lost (this month): 2 deals
- **Conversion rate**: 60%

### Deal Velocity
Track average time in each stage to identify bottlenecks.

## Best Practices

1. **Always start in Intake** - Every new lead begins here
2. **Update regularly** - Move deals as they progress
3. **Add context** - Use task descriptions for notes, emails, call summaries
4. **Track lost reasons** - When marking Closed Lost, note why (price, timing, competitor, etc.)
5. **Celebrate wins** - Closed Won deserves recognition!

## Inputs
- **Lead name**: Person or company name
- **Contact info**: Email, phone
- **Project type**: What they need
- **Stage**: Current pipeline stage
- **Deal value** (optional): Expected revenue
- **Notes**: Any relevant context

## Tools
- `execution/clickup_api.py` - ClickUp API wrapper
- `execution/send_onboarding_email.py` - Email automation
- `execution/setup_sales_crm.py` - CRM setup (already run)

## Outputs
- **Task created**: ClickUp task URL
- **Pipeline view**: List of deals by stage
- **Move confirmation**: Task moved to new stage
- **Reports**: Pipeline summary and metrics

## Edge Cases
- **Duplicate leads**: Check for existing tasks before creating
- **Missing stage**: Validate stage name against valid stages
- **Reopening lost deals**: Move from Closed Lost back to appropriate stage
- **Multiple contacts per deal**: Use subtasks or comments for additional contacts
- **Deal value tracking**: Add custom field for revenue tracking

## Configuration

ClickUp Structure (already created):
- Folder: Sales Pipeline (ID: 90175146991)
- Lists: 7 stage lists (IDs noted above)

## Learnings
- Initial creation: 2026-01-03
- Structure created with 7-stage pipeline
- Integrated with email onboarding workflow
