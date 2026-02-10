# Multi-Business Form Handling System

## Overview

A unified form handling system that routes submissions from multiple websites to the correct business pipelines.

**Supported Websites:**
- marceausolutions.com (main)
- swfloridacomfort.com (HVAC client)
- squarefootshipping.com (shipping client)

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Website Form   │     │  Website Form   │     │  Website Form   │
│ marceausolutions│     │ swfloridacomfort│     │ squarefootship  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   api.marceausolutions │
                    │   /api/form/submit     │
                    └───────────┬────────────┘
                                │
                                ▼
                    ┌────────────────────────┐
                    │ MultiBusinessFormHandler│
                    │  - Detect business     │
                    │  - Route to pipeline   │
                    └───────────┬────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Marceau Pipeline│    │  HVAC Pipeline  │    │ Shipping Pipeline│
│ - ClickUp list  │    │ - ClickUp list  │    │ - ClickUp list  │
│ - Google Sheet  │    │ - Google Sheet  │    │ - Google Sheet  │
│ - Notify William│    │ - Notify Owner  │    │ - Notify Owner  │
│ - Auto-respond  │    │ - Auto-respond  │    │ - Auto-respond  │
│ - Nurture seq   │    │ - Nurture seq   │    │ - Nurture seq   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## API Endpoints

**Base URL:** `https://api.marceausolutions.com`

### POST /api/form/submit

Submit a form from any website.

**Request:**
```json
{
  "email": "customer@example.com",
  "name": "John Doe",
  "phone": "+12395551234",
  "source": "swfloridacomfort",
  "interest": "AC Repair",
  "message": "My AC isn't cooling",
  "email_opt_in": true,
  "sms_opt_in": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Form submitted successfully",
  "submission_id": "uuid-here",
  "business_id": "swfloridacomfort",
  "task_url": "https://app.clickup.com/t/...",
  "auto_responses": ["email", "sms"]
}
```

### GET /api/form/health

Check system status.

```json
{
  "status": "healthy",
  "service": "multi-business-form-handler",
  "businesses_configured": 3,
  "business_ids": ["marceausolutions", "swfloridacomfort", "squarefootshipping"],
  "integrations": {
    "clickup": true,
    "google_sheets": true,
    "email": true,
    "sms": true
  }
}
```

### GET /api/form/businesses

List configured businesses.

---

## Business Detection

The system detects which business a form belongs to using (in order):

1. **Explicit `business_id` field** - Highest priority
2. **`source` field** - Page or campaign identifier
3. **`referrer` header** - Original referring page
4. **`origin` header** - Website domain
5. **Default** - Falls back to `marceausolutions`

**Source Pattern Matching:**
- `hvac`, `swflorida` → swfloridacomfort
- `squarefoot`, `shipping`, `storage` → squarefootshipping
- `marceau`, `fitness`, `interview`, `amazon` → marceausolutions

---

## Integration Flow

When a form is submitted:

1. **Save to JSON** - Backup storage in `/output/form_submissions/{business_id}/`
2. **Create ClickUp Task** - In business-specific list with 2-hour due date
3. **Append to Google Sheets** - Business-specific spreadsheet
4. **Notify Business Owner** - Email + SMS with lead details
5. **Notify Central** - William also gets notified for all leads
6. **Auto-Respond to Customer** - Immediate email + SMS confirmation
7. **Add to Nurturing Queue** - For multi-touch follow-up

---

## Frontend Integration

### Option 1: Include form-handler.js

```html
<form data-form-handler data-business="swfloridacomfort">
  <input name="name" required>
  <input name="email" type="email" required>
  <input name="phone">
  <select name="interest">
    <option value="AC Repair">AC Repair</option>
  </select>
  <textarea name="message"></textarea>
  <button type="submit">Submit</button>
</form>

<script src="https://api.marceausolutions.com/static/form-handler.js"></script>
```

### Option 2: Direct API Call

```javascript
fetch('https://api.marceausolutions.com/api/form/submit', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'customer@example.com',
    name: 'John Doe',
    source: 'swfloridacomfort',
    interest: 'AC Repair'
  })
});
```

---

## Business Configuration

Located in `/execution/form_handler/business_config.py`

Each business has:
- `business_id` - Unique identifier
- `business_name` - Display name
- `domain` - Website domain
- `owner_name`, `owner_email`, `owner_phone` - Owner contact
- `clickup_list_id` - CRM list for leads
- `google_sheet_id` - Spreadsheet for tracking
- `auto_response_*_template` - Auto-response messages
- `calendly_link` - For appointment scheduling

---

## Files

| File | Purpose |
|------|---------|
| `/execution/form_handler/business_config.py` | Business configurations |
| `/execution/form_handler/multi_business_handler.py` | Main handler with routing |
| `/execution/form_handler/handler.py` | Base form handler |
| `/execution/form_handler/models.py` | FormSubmission model |
| `/execution/form_handler/api.py` | Flask API (standalone) |
| `/projects/ai-customer-service/src/form_router.py` | FastAPI router |
| `/projects/ai-customer-service/static/form-handler.js` | Frontend script |

---

## Testing

**Test submission via curl:**
```bash
curl -X POST https://api.marceausolutions.com/api/form/submit \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test","source":"swfloridacomfort","interest":"AC Repair"}'
```

**Check health:**
```bash
curl https://api.marceausolutions.com/api/form/health
```

---

## TODO

- [ ] Create ClickUp list for SW Florida Comfort
- [ ] Create ClickUp list for Square Foot Shipping
- [ ] Create Google Sheet for each business
- [ ] Get Square Foot owner contact info
- [ ] Deploy form-handler.js to CDN
- [ ] Add form components to client websites

---

*Last Updated: 2026-01-18*
