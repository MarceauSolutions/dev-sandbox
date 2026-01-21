# Fitness Influencer Assistant - Backend

FastAPI backend for the Fitness Influencer AI Assistant.

## Related Repositories

- **Frontend:** [fitness-influencer-frontend](https://github.com/MarceauSolutions/fitness-influencer-frontend) - Web interface
- **Backend (this repo):** Python FastAPI server

## Deployment

- **Frontend:** GitHub Pages
- **Backend:** Railway - `https://web-production-44ade.up.railway.app`

## Features

- 🎬 Video editing with automatic jump cuts (FFmpeg)
- 🎨 Branded educational graphics creation (Pillow)
- 📧 Email digest and categorization (Gmail API)
- 📊 Revenue analytics from Google Sheets
- 🤖 AI image generation (Grok/xAI)
- 📅 Calendar management (Google Calendar API)

## API Documentation

Once deployed, visit: `https://web-production-44ade.up.railway.app/docs`

## Environment Variables Required

```
XAI_API_KEY=your_grok_api_key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email
SMTP_PASSWORD=your_password
SENDER_NAME=Your Name
SENDER_EMAIL=your_email
```

## Local Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Visit: http://localhost:8000/docs

## Deployment

Deployed on Railway with automatic deploys from `main` branch.

## Tech Stack

- Python 3.10
- FastAPI
- Google APIs (Gmail, Calendar, Sheets)
- MoviePy + FFmpeg (video editing)
- Pillow (image processing)
- Grok/xAI API (AI image generation)
