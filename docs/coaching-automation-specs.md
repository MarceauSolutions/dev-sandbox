# Coaching Automation Workflow Specifications

> n8n workflow specs for automating coaching operations.
> Each workflow is specified in enough detail to build directly in n8n.
> All workflows run on EC2 at https://n8n.marceausolutions.com
> Clone patterns from existing Coaching-Monday-Checkin (`aBxCj48nGQVLRRnq`).

---

## Workflow A: Coaching-Midweek-Tip

**Purpose**: Send a rotating coaching tip SMS to all active clients every Wednesday at 6pm ET.
**Replaces**: Manual mid-week tip sending via `python execution/twilio_sms.py --template coaching_midweek_tip`.

### Trigger
- **Node**: Schedule Trigger (Cron)
- **Schedule**: `0 0 18 * * 3` (6-field cron: sec min hour dom mon dow — Wednesday 6pm ET)
- **Timezone**: America/New_York

### Node 1: Read Active Clients from PT Tracker
- **Node type**: Google Sheets (Read Rows)
- **Credential**: `RIFdaHtNYdTpFnlu` (Google Sheets)
- **Spreadsheet ID**: `1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA`
- **Sheet GID**: `1584175390` (Roster tab) — **USE mode:id, NEVER mode:name**
- **Filter**: Column "Status" = "Active"
- **Output**: Array of `{ name, phone, status }`

### Node 2: Read Midweek Tips JSON
- **Node type**: HTTP Request (GET) or Read Binary File
- **Source**: `projects/marceau-solutions/fitness/clients/pt-business/data/midweek-tips.json`
- **Alternative**: Store tips directly in n8n as a Code node:
  ```javascript
  // Code node — rotate tips
  const tips = $json; // from Read Binary or hardcoded
  const weekNumber = Math.floor(Date.now() / (7 * 24 * 60 * 60 * 1000));
  const tipIndex = weekNumber % tips.length;
  return [{ tip: tips[tipIndex].text, category: tips[tipIndex].category }];
  ```

### Node 3: Select Tip (Code Node)
- **Node type**: Code
- **Logic**:
  ```javascript
  // Get current week number to rotate through tips
  const now = new Date();
  const startOfYear = new Date(now.getFullYear(), 0, 1);
  const weekNumber = Math.floor((now - startOfYear) / (7 * 24 * 60 * 60 * 1000));

  // 30 tips in midweek-tips.json, rotate through them
  const tips = [
    // Hardcode all 30 tips here from midweek-tips.json
    // OR read from previous node
  ];
  const tip = tips[weekNumber % tips.length];

  return [{ json: { tipText: tip.text, tipCategory: tip.category } }];
  ```

### Node 4: Loop Over Clients
- **Node type**: Split In Batches
- **Batch size**: 1 (one at a time to respect Twilio rate limits)

### Node 5: Send SMS via Twilio
- **Node type**: Twilio (Send SMS)
- **Credential**: `hduvneOOzFzKMfOa` (Twilio)
- **From**: +18552399364
- **To**: `{{ $node["Read Active Clients"].json.phone }}`
- **Body**:
  ```
  Hey {{ $node["Read Active Clients"].json.name }}! 💡 Mid-week tip:

  {{ $node["Select Tip"].json.tipText }}

  Keep pushing! - Coach William
  ```

### Node 6: Log to Google Sheets
- **Node type**: Google Sheets (Append Row)
- **Credential**: `RIFdaHtNYdTpFnlu`
- **Spreadsheet ID**: `1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA`
- **Sheet**: SMS Log tab
- **Row data**: `{ timestamp, client_name, phone, tip_category, tip_text, status: "sent" }`

### Error Handling
- Wire to Self-Annealing-Error-Handler (`Ob7kiVvCnmDHAfNW`)
- On Twilio failure: log error, continue to next client (don't stop the batch)

### Data Flow Diagram
```
Schedule Trigger (Wed 6pm ET)
  → Read Active Clients (Google Sheets)
  → Select Tip (Code node - week rotation)
  → Split In Batches (1 per batch)
    → Send SMS (Twilio)
    → Log (Google Sheets)
  → [Error] → Self-Annealing
```

---

## Workflow B: Coaching-Tuesday-Followup

**Purpose**: Check if Monday check-in SMS was answered. Send a nudge to non-responders.
**Depends on**: Coaching-Monday-Checkin (`aBxCj48nGQVLRRnq`) running Monday 9am ET.

### Trigger
- **Node**: Schedule Trigger (Cron)
- **Schedule**: `0 0 8 * * 2` (Tuesday 8am ET)
- **Timezone**: America/New_York

### Node 1: Read Active Clients
- **Node type**: Google Sheets (Read Rows)
- **Credential**: `RIFdaHtNYdTpFnlu`
- **Spreadsheet ID**: `1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA`
- **Sheet GID**: `1584175390` (Roster tab) — **mode:id**
- **Filter**: Status = "Active"

### Node 2: Check Twilio Inbound Messages (Last 24h)
- **Node type**: HTTP Request
- **Method**: GET
- **URL**: `https://api.twilio.com/2010-04-01/Accounts/{{ $env.TWILIO_ACCOUNT_SID }}/Messages.json`
- **Auth**: Basic (Twilio Account SID + Auth Token from credential)
- **Query params**:
  - `To`: +18552399364
  - `DateSent>`: `{{ new Date(Date.now() - 24*60*60*1000).toISOString().split('T')[0] }}`
  - `PageSize`: 100
- **Output**: Array of inbound messages with `From` phone numbers

### Node 3: Identify Non-Responders (Code Node)
- **Node type**: Code
- **Logic**:
  ```javascript
  const clients = $input.all().filter(i => i.json.source === 'clients');
  const inboundMessages = $input.all().filter(i => i.json.source === 'twilio');

  // Extract phone numbers that responded
  const respondedPhones = new Set(
    inboundMessages.map(m => m.json.from.replace(/[^0-9]/g, ''))
  );

  // Find clients who did NOT respond
  const nonResponders = clients.filter(c => {
    const cleanPhone = c.json.phone.replace(/[^0-9]/g, '');
    return !respondedPhones.has(cleanPhone);
  });

  return nonResponders.map(c => ({ json: c.json }));
  ```

### Node 4: IF Non-Responders Exist
- **Node type**: IF
- **Condition**: Items count > 0
- **True branch**: Continue to SMS
- **False branch**: End (everyone responded)

### Node 5: Send Follow-Up SMS (Twilio)
- **Node type**: Twilio (Send SMS)
- **Credential**: `hduvneOOzFzKMfOa`
- **From**: +18552399364
- **To**: `{{ $json.phone }}`
- **Body**:
  ```
  Hey {{ $json.name }}, just checking in — didn't hear from you yesterday. How's training going this week? Even a quick "good" or "struggling" helps me help you. 💪

  - Coach William
  ```
- **Note**: This maps to the `coaching_no_response` template in `execution/twilio_sms.py`

### Node 6: Log Follow-Up
- **Node type**: Google Sheets (Append Row)
- **Sheet**: SMS Log tab
- **Row**: `{ timestamp, client_name, phone, type: "follow_up_no_response", status: "sent" }`

### Error Handling
- Wire to Self-Annealing-Error-Handler

### Data Flow Diagram
```
Schedule Trigger (Tue 8am ET)
  → Read Active Clients (Google Sheets)
  → Check Twilio Inbound (HTTP Request, last 24h)
  → Merge → Identify Non-Responders (Code)
  → IF non-responders exist
    → [True] Split In Batches → Send SMS → Log
    → [False] → End
  → [Error] → Self-Annealing
```

---

## Workflow C: Coaching-Weekly-Program-Generate

**Purpose**: Auto-generate weekly training programs for each active client every Sunday.
**Uses**: `execution/workout_plan_generator.py` on EC2.

### Trigger
- **Node**: Schedule Trigger (Cron)
- **Schedule**: `0 0 17 * * 0` (Sunday 5pm ET)
- **Timezone**: America/New_York

### Node 1: Read Active Clients
- **Node type**: Google Sheets (Read Rows)
- **Credential**: `RIFdaHtNYdTpFnlu`
- **Spreadsheet ID**: `1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA`
- **Sheet GID**: `1584175390` (Roster tab) — **mode:id**
- **Filter**: Status = "Active"
- **Output**: `{ name, phone, email, goals, limitations, current_week }`

### Node 2: Loop Over Clients
- **Node type**: Split In Batches
- **Batch size**: 1

### Node 3: Generate Workout Plan (Execute Command)
- **Node type**: Execute Command (SSH to EC2 or local if running on EC2)
- **Command**:
  ```bash
  cd /home/ec2-user/dev-sandbox && python execution/workout_plan_generator.py \
    --client-name "{{ $json.name }}" \
    --goals "{{ $json.goals }}" \
    --limitations "{{ $json.limitations }}" \
    --week {{ $json.current_week }} \
    --output "/tmp/programs/{{ $json.name | lower | replace(' ', '_') }}_week{{ $json.current_week }}.pdf"
  ```
- **Alternative**: Call via Agent Bridge API (localhost:5010) if the Python Bridge is running:
  ```
  POST http://localhost:5010/api/execute
  {
    "tool": "workout_plan_generator",
    "params": {
      "client_name": "{{ $json.name }}",
      "goals": "{{ $json.goals }}",
      "limitations": "{{ $json.limitations }}",
      "week": {{ $json.current_week }}
    }
  }
  ```

### Node 4: Generate PDF (Branded PDF Engine)
- **Node type**: Execute Command
- **Command**:
  ```bash
  cd /home/ec2-user/dev-sandbox && python execution/branded_pdf_engine.py \
    --template workout \
    --input "/tmp/programs/{{ $json.name | lower | replace(' ', '_') }}_week{{ $json.current_week }}.json" \
    --output "/tmp/programs/{{ $json.name | lower | replace(' ', '_') }}_week{{ $json.current_week }}.pdf"
  ```

### Node 5: Upload to Google Drive
- **Node type**: Google Drive (Upload File)
- **Credential**: Google Drive (from Sheets credential or separate)
- **Parent Folder ID**: `1v9iYh6Cb-1WC9ZRQXAl44LxgJS25mczJ` (Coaching Clients folder)
- **Subfolder**: `{{ $json.name }}/Programs/`
- **File name**: `Week_{{ $json.current_week }}_Program.pdf`

### Node 6: Send Notification SMS
- **Node type**: Twilio (Send SMS)
- **Credential**: `hduvneOOzFzKMfOa`
- **From**: +18552399364
- **To**: `{{ $json.phone }}`
- **Body**:
  ```
  Hey {{ $json.name }}! Your Week {{ $json.current_week }} program is ready 🔥

  Check your email/Drive for the PDF. Let me know if you have any questions about the programming!

  Let's have a great week. - Coach William
  ```

### Node 7: Update Week Counter
- **Node type**: Google Sheets (Update Row)
- **Sheet GID**: `1584175390` (Roster)
- **Update**: Increment `current_week` by 1

### Node 8: Log Generation
- **Node type**: Google Sheets (Append Row)
- **Sheet**: Program Log tab
- **Row**: `{ timestamp, client_name, week_number, pdf_generated: true, drive_uploaded: true, sms_sent: true }`

### Error Handling
- Wire to Self-Annealing-Error-Handler
- On PDF generation failure: Log error, send William an admin SMS, skip to next client
- Admin notification: Send SMS to +12393985676 on any failure

### Data Flow Diagram
```
Schedule Trigger (Sun 5pm ET)
  → Read Active Clients (Google Sheets)
  → Split In Batches (1 per client)
    → Generate Workout Plan (Execute Command)
    → Generate PDF (Branded PDF Engine)
    → Upload to Drive
    → Send SMS Notification (Twilio)
    → Update Week Counter (Google Sheets)
    → Log (Google Sheets)
  → [Error] → Self-Annealing → Admin SMS
```

---

## Workflow D: Coaching-Month-End-Review

**Purpose**: Send booking SMS with Calendly link for monthly 1:1 progress review. Follow up if not booked after 48h.

### Trigger
- **Node**: Schedule Trigger (Cron)
- **Schedule**: `0 0 8 * * 1` (Monday 8am ET)
- **Timezone**: America/New_York
- **Additional condition (Code node)**: Only fire on the LAST Monday of the month

### Node 1: Check If Last Monday (Code Node)
- **Node type**: Code
- **Logic**:
  ```javascript
  const now = new Date();
  const lastDayOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  const currentDay = now.getDate();
  const daysUntilEndOfMonth = lastDayOfMonth - currentDay;

  // If there are fewer than 7 days left in the month, this IS the last Monday
  if (daysUntilEndOfMonth < 7) {
    return [{ json: { isLastMonday: true, month: now.toLocaleString('en-US', { month: 'long' }) } }];
  }

  // Not the last Monday — stop execution
  return [];
  ```

### Node 2: Read Active Clients
- **Node type**: Google Sheets (Read Rows)
- **Credential**: `RIFdaHtNYdTpFnlu`
- **Spreadsheet ID**: `1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA`
- **Sheet GID**: `1584175390` (Roster tab) — **mode:id**
- **Filter**: Status = "Active"

### Node 3: Send Booking SMS
- **Node type**: Twilio (Send SMS)
- **Credential**: `hduvneOOzFzKMfOa`
- **From**: +18552399364
- **To**: `{{ $json.phone }}`
- **Body**:
  ```
  Hey {{ $json.name }}! It's time for your monthly progress review 📊

  Let's look at your numbers, adjust your programming, and set goals for next month.

  Book your 15-min slot here: https://calendly.com/wmarceau/kickoff-call

  - Coach William
  ```

### Node 4: Log Booking Request
- **Node type**: Google Sheets (Append Row)
- **Sheet**: SMS Log tab
- **Row**: `{ timestamp, client_name, phone, type: "month_end_review_invite", status: "sent" }`

### Node 5: Wait 48 Hours
- **Node type**: Wait
- **Duration**: 48 hours
- **Note**: n8n Wait node pauses the execution and resumes after the specified duration

### Node 6: Check Calendly Bookings (HTTP Request)
- **Node type**: HTTP Request
- **Method**: GET
- **URL**: `https://api.calendly.com/scheduled_events`
- **Headers**: `Authorization: Bearer {{ $env.CALENDLY_API_KEY }}`
- **Query params**:
  - `min_start_time`: ISO timestamp of 48h ago
  - `max_start_time`: ISO timestamp of 7 days from now
  - `status`: active
- **Alternative (simpler)**: Skip Calendly API check. Just send the reminder to everyone — if they already booked, the reminder is harmless.

### Node 7: Send Reminder SMS (to all — simpler approach)
- **Node type**: Twilio (Send SMS)
- **Body**:
  ```
  Hey {{ $json.name }}, friendly reminder — have you booked your monthly review yet?

  It's only 15 minutes and it makes a huge difference for your programming next month.

  Book here: https://calendly.com/wmarceau/kickoff-call

  - Coach William
  ```

### Node 8: Log Reminder
- **Node type**: Google Sheets (Append Row)
- **Sheet**: SMS Log tab
- **Row**: `{ timestamp, client_name, phone, type: "month_end_review_reminder", status: "sent" }`

### Error Handling
- Wire to Self-Annealing-Error-Handler

### Data Flow Diagram
```
Schedule Trigger (every Monday 8am ET)
  → Check If Last Monday (Code)
    → [Empty = not last Monday] → End
    → [Has data = IS last Monday]
      → Read Active Clients (Google Sheets)
      → Split In Batches
        → Send Booking SMS (Twilio)
        → Log (Google Sheets)
        → Wait 48h
        → Send Reminder SMS (Twilio)
        → Log Reminder (Google Sheets)
  → [Error] → Self-Annealing
```

---

## Implementation Priority

| # | Workflow | Complexity | Impact | Build Order |
|---|---------|-----------|--------|-------------|
| 1 | A: Midweek Tip | Low | High — automates weekly manual task | First |
| 2 | B: Tuesday Followup | Medium | High — closes accountability gap | Second |
| 3 | D: Month-End Review | Low-Medium | Medium — automates monthly booking | Third |
| 4 | C: Weekly Program Generate | High | High — full automation of program delivery | Fourth (needs testing) |

## Shared Resources

- **Twilio credential**: `hduvneOOzFzKMfOa`
- **Google Sheets credential**: `RIFdaHtNYdTpFnlu`
- **PT Tracker Sheet**: `1ZkzOY9SxMcDrDtq69rDcQ0ZMd9Ss8YaE-qeJmS7FuBA`
- **Roster tab GID**: `1584175390`
- **Error handler**: Self-Annealing-Error-Handler (`Ob7kiVvCnmDHAfNW`)
- **Coaching clients Drive folder**: `1v9iYh6Cb-1WC9ZRQXAl44LxgJS25mczJ`
- **Twilio FROM number**: +18552399364
- **Admin phone** (notifications): +12393985676

---

*Specs created March 2026. Ready to build in n8n.*
