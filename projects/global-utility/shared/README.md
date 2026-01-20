# Shared Utilities

Common utilities and services used across multiple AI assistant projects.

## Directory Structure

```
shared/
├── ai/                     # AI service integrations
│   └── grok_image_gen.py   # xAI Grok image generation ($0.07/image)
│
├── google/                 # Google API integrations
│   ├── google_auth_setup.py  # OAuth setup for Google APIs
│   └── gmail_monitor.py      # Gmail reading and summarization
│
├── analytics/              # Business analytics
│   └── revenue_analytics.py  # Google Sheets revenue tracking
│
├── communication/          # Messaging services
│   └── twilio_sms.py        # SMS notifications via Twilio
│
├── utils/                  # General utilities
│   └── markdown_to_pdf.py   # PDF generation from markdown
│
└── templates/              # Shared templates
```

## Usage

Import shared utilities in any project:

```python
# From project src/
import sys
sys.path.insert(0, '../../shared')

from ai.grok_image_gen import generate_image
from google.gmail_monitor import get_email_summary
from analytics.revenue_analytics import get_revenue_data
```

## Environment Variables (Shared)

These credentials are used across multiple projects:

```env
# AI Services
XAI_API_KEY=your_xai_key              # Grok image generation
ANTHROPIC_API_KEY=your_anthropic_key  # Claude AI

# Google APIs
GOOGLE_CREDENTIALS_PATH=credentials.json

# Communication
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890
```

## Projects Using Shared Utilities

| Utility | Fitness Influencer | Interview Prep | Amazon Seller |
|---------|-------------------|----------------|---------------|
| grok_image_gen.py | ✅ | ✅ | ❌ |
| gmail_monitor.py | ✅ | ❌ | ✅ |
| revenue_analytics.py | ✅ | ❌ | ✅ |
| twilio_sms.py | ✅ | ❌ | ✅ |
| google_auth_setup.py | ✅ | ❌ | ✅ |
