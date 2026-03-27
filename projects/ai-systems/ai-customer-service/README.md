# AI Customer Service

Voice AI ordering system for independent restaurants. Handles phone orders, answers menu questions, and integrates with POS systems.

## Market Viability

- **Score**: 4.15/5 (GO)
- **TAM**: $50B+ by 2030
- **Target**: Independent restaurants (1-10 locations)
- **Pricing**: $149-399/month + usage

See [market-analysis/](market-analysis/) for full research.

## Quick Start

### 1. Install Dependencies

```bash
cd projects/ai-customer-service
pip install -r requirements.txt
```

### 2. Configure Environment

Ensure these are in your root `.env`:

```bash
ANTHROPIC_API_KEY=your_key
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX
```

### 3. Test Locally (No Twilio)

```bash
# View demo menu
python -m src.cli menu

# Simulate a phone conversation
python -m src.cli simulate
```

### 4. Run Server

```bash
# Start the server
python -m src.cli serve --port 8000

# Or with uvicorn directly
uvicorn src.main:app --reload --port 8000
```

### 5. Expose for Twilio (Development)

```bash
# Use ngrok to expose local server
ngrok http 8000

# Configure Twilio webhook to:
# https://your-ngrok-url.ngrok.io/twilio/voice
```

## Project Structure

```
ai-customer-service/
├── src/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── config.py         # Settings
│   ├── models.py         # Data models
│   ├── voice_engine.py   # AI conversation logic
│   ├── twilio_handler.py # Twilio webhooks
│   └── cli.py            # CLI for testing
├── market-analysis/      # SOP 17 research
├── workflows/            # Documented procedures
├── tests/               # Test files
├── KICKOFF.md           # SOP 0 decisions
├── CHANGELOG.md         # Version history
├── VERSION              # Current version
└── requirements.txt     # Dependencies
```

## CLI Commands

```bash
# Show menu
python -m src.cli menu

# Simulate phone conversation (no Twilio needed)
python -m src.cli simulate

# Start server
python -m src.cli serve --port 8000
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | Detailed health status |
| `/twilio/voice` | POST | Incoming call webhook |
| `/twilio/gather` | POST | Speech input webhook |
| `/twilio/status` | POST | Call status webhook |
| `/twilio/calls` | GET | List active calls |
| `/twilio/calls/{sid}` | GET | Get call details |

## Development Phases

- [x] Phase 1: Voice Engine MVP (current)
- [ ] Phase 2: Restaurant Dashboard
- [ ] Phase 3: POS Integrations (Toast, Square)
- [ ] Phase 4: Beta Launch (10 Naples pizzerias)

## Architecture

```
Phone → Twilio → STT → LLM (Claude) → TTS → Twilio → Phone
                         ↓
                   Order → POS API
```

## References

- [Directive](../../directives/ai-customer-service.md)
- [Market Analysis](market-analysis/consolidated/GO-NO-GO-DECISION.md)
- [KICKOFF.md](KICKOFF.md)
