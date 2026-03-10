# SOP 34: Fitness Influencer Automation Pattern

> Reusable playbook for onboarding fitness influencer clients and automating their SMS programs.
> First client: Julia Marceau (BoabFit). This SOP captures what we learned.

## Overview

When a fitness influencer signs up as a client, they get:
1. **Client roster management** — track their subscribers
2. **Automated daily SMS** — workout breakdowns + nutrition tips to their clients
3. **Questionnaire system** — get their preferences without manual back-and-forth
4. **Response watcher** — auto-detect when they answer and route actions
5. **Two-way SMS relay** — they can text their clients through our Twilio number

## Architecture

```
Influencer answers questionnaire via SMS
         ↓
questionnaire_response_watcher.py (every 5 min via n8n)
         ↓
Detects completion → ACTION_MANIFESTS
         ↓
Auto-execute simple actions | Route complex ones to William
         ↓
n8n Daily Workflow → daily_checkin_sms.py → Twilio → Clients
```

## Step-by-Step: New Influencer Onboarding

### 1. Create Project Structure

```
projects/marceau-solutions/fitness/clients/{client_name}/
├── src/
│   ├── daily_checkin_sms.py     # Copy from boabfit, customize
│   └── workout_plan.json        # Their specific program
├── clients/
│   ├── roster.json              # Their client list
│   └── conversations.jsonl      # SMS relay log
├── website/                     # If they need a landing page
└── CLAUDE.md                    # Project docs
```

### 2. Configure Questionnaire

Add a new template to `execution/client_questionnaire.py` QUESTIONNAIRES dict:
```python
"{client}_template_approval": {
    "title": "{Client} SMS Template Approval",
    "description": "...",
    "intro": "Hey {name}! ...",
    "questions": [ ... ],
    "outro": "...",
    "sender_id": "\n\n— William from Marceau Solutions"
}
```

Add matching action manifest to `execution/questionnaire_response_watcher.py` ACTION_MANIFESTS:
```python
"{client}_template_approval": {
    "description": "...",
    "actions": {
        "sender_name": {"type": "route", ...},
        "message_tone": {"type": "auto_acknowledge", ...},
        ...
    }
}
```

### 3. Send Questionnaire
```bash
python execution/client_questionnaire.py send \
  --to "+1XXXXXXXXXX" \
  --name "Influencer Name" \
  --questionnaire {client}_template_approval
```

The **response watcher** (n8n: `Questionnaire Response Watcher`, ID: `SNVOcExULzj5mMR8`) will automatically detect when they respond.

### 4. Create n8n Daily Workflow

Use the BoabFit workflow as a template (`aiYWIAJnzD4qUplH`):
- Schedule trigger at their preferred time
- SSH to EC2 to run their daily_checkin_sms.py

### 5. Verify Everything

```bash
# Verify n8n workflow is actually active and valid
python execution/n8n_workflow_verifier.py verify {workflow_id}

# Dry run on EC2
ssh -i ~/.ssh/marceau-ec2-key.pem ec2-user@34.193.98.97 \
  "cd /home/ec2-user/dev-sandbox && python3 projects/{client}/src/daily_checkin_sms.py --dry-run"
```

### 6. Sync to EC2

Update `scripts/sync_boabfit_to_ec2.sh` or create a new sync script for the client.

## Critical Lessons (From BoabFit)

### What Went Wrong
1. **No automated response detection** — questionnaire responses sat unread until William manually checked
2. **n8n workflow had invalid node type** — `executeCommand` node prevented activation but wasn't caught
3. **EC2 didn't have the code** — workflows SSHed to EC2 but files only existed on Mac
4. **`python` command didn't exist on EC2** — symlink missing, workflows silently failed

### How We Fixed It
1. **`questionnaire_response_watcher.py`** — polls every 5 min, auto-detects completions
2. **`n8n_workflow_verifier.py`** — validates node types, connections, active state, execution history
3. **`sync_boabfit_to_ec2.sh`** — explicit file sync, not git-dependent
4. **All n8n workflows use `python3`** — never rely on `python` alias

### Mandatory Checklist (Before Saying "It Works")

- [ ] n8n workflow is ACTIVE (verified via API, not just UI)
- [ ] `n8n_workflow_verifier.py verify {id}` passes with 0 issues
- [ ] Dry run succeeds ON EC2 (not just local Mac)
- [ ] Files are synced to EC2 (run sync script)
- [ ] Response watcher has the client's questionnaire in its ACTION_MANIFESTS
- [ ] `python3` used in all n8n SSH commands (never bare `python`)

## Key Files

| File | Purpose |
|------|---------|
| `execution/client_questionnaire.py` | Send questionnaires, collect responses |
| `execution/questionnaire_response_watcher.py` | Auto-detect completions, route actions |
| `execution/n8n_workflow_verifier.py` | Verify n8n workflows are valid and active |
| `execution/twilio_sms.py` | Shared SMS sending utility |
| `scripts/sync_boabfit_to_ec2.sh` | Sync files to EC2 |

## n8n Workflows

| Workflow | ID | Schedule | Purpose |
|----------|----|----------|---------|
| BoabFit Daily Check-in SMS | `aiYWIAJnzD4qUplH` | 8am ET daily | Send workout messages |
| Questionnaire Response Watcher | `SNVOcExULzj5mMR8` | Every 5 min | Detect questionnaire responses |
