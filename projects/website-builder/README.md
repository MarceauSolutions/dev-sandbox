# Website Builder AI

Automated website generation powered by AI research and social media personality matching. Provide company info and social profiles, get a website that authentically matches the owner's brand personality.

## How It Works

### Basic Workflow
1. **Research Phase**: Claude researches the company and owner
2. **Content Generation**: AI generates copy, value propositions, testimonials
3. **Design Selection**: Picks appropriate template based on industry
4. **Build & Deploy**: Generates static site ready for deployment

### Enhanced Social Research Workflow (New)
1. **Social Analysis**: Analyze X, LinkedIn, Instagram profiles for communication style
2. **Web Context**: Gather reviews, news mentions, competitor info
3. **Personality Synthesis**: Combine all sources into unified brand personality
4. **Personality-Driven Content**: Generate copy matching brand voice
5. **Personality-Styled Site**: Build website with matching visual identity

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your-key"
export BRAVE_SEARCH_API_KEY="your-key"  # Optional
export TAVILY_API_KEY="your-key"        # Optional

# Start API server
cd src
uvicorn website_builder_api:app --reload --port 8001

# Open API docs
open http://localhost:8001/docs
```

## API Usage

### Basic Workflow
```bash
# Full workflow (research + generate + build)
curl -X POST http://localhost:8001/api/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Project Evolve",
    "owner_name": "Jake Raleigh",
    "location": "Naples, FL"
  }'
```

### Social Research Workflow
```bash
# Enhanced workflow with social profiles
curl -X POST http://localhost:8001/api/workflow/social \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Project Evolve",
    "owner_name": "Jake Raleigh",
    "location": "Naples, FL",
    "social_profiles": {
      "x": "https://x.com/projectevolve",
      "instagram": "https://instagram.com/projectevolve",
      "linkedin": "https://linkedin.com/in/jakeraleigh"
    }
  }'
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Social Research Pipeline                  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Social Profile│    │  Web Search   │    │  AI Research  │
│   Analyzer    │    │   (Context)   │    │   (Baseline)  │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                  ┌───────────────────┐
                  │   Personality     │
                  │   Synthesizer     │
                  └───────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Brand Voice  │    │Visual Identity│    │Content Strategy│
└───────────────┘    └───────────────┘    └───────────────┘
                              │
                              ▼
                  ┌───────────────────┐
                  │Content Generator  │
                  │(Personality-Driven│
                  └───────────────────┘
                              │
                              ▼
                  ┌───────────────────┐
                  │   Site Builder    │
                  │(Personality-Styled│
                  └───────────────────┘
                              │
                              ▼
                     [Generated Website]
```

## Project Structure

```
website-builder/
├── src/
│   ├── research_engine.py         # Company/owner research + social integration
│   ├── social_profile_analyzer.py # Social media profile analysis
│   ├── web_search.py              # Brave/Tavily web search integration
│   ├── personality_synthesizer.py # Brand personality synthesis
│   ├── content_generator.py       # AI-powered copywriting
│   ├── site_builder.py            # HTML/CSS generation with personality styling
│   └── website_builder_api.py     # FastAPI backend
├── output/                        # Generated websites
├── templates/                     # Template components (future)
├── workflows/                     # Workflow documentation
├── requirements.txt
├── VERSION
└── README.md
```

## API Endpoints

### Basic Workflow
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/research` | POST | Research company (basic) |
| `/api/generate` | POST | Generate content |
| `/api/build` | POST | Build static site |
| `/api/workflow` | POST | Full basic workflow |

### Social Research Workflow
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/research/social` | POST | Research with social profiles |
| `/api/generate/personality` | POST | Generate personality-driven content |
| `/api/build/personality` | POST | Build personality-styled site |
| `/api/workflow/social` | POST | Full social workflow |

### Utility
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/session/{id}` | GET | Get session data |
| `/api/download/{id}` | GET | Download site as ZIP |
| `/preview/{id}/index.html` | GET | Preview generated site |
| `/health` | GET | Health check |

## Features

### Core
- [x] AI-powered company research
- [x] Owner/founder research
- [x] Industry detection
- [x] AI copywriting (headlines, about, services, testimonials)
- [x] Contact form generation
- [x] Mobile responsive (Tailwind CSS)
- [x] SEO optimization

### Social Research (New)
- [x] Social profile URL parsing (X, LinkedIn, Instagram, etc.)
- [x] Communication style analysis
- [x] Brand personality synthesis
- [x] Personality-driven content generation
- [x] Dynamic visual identity
  - [x] Typography matching
  - [x] Border radius customization
  - [x] Shadow intensity
  - [x] Animation levels
  - [x] Color schemes
- [x] Web search integration (Brave/Tavily)
- [x] Confidence scoring

### Planned
- [ ] Frontend builder UI
- [ ] Template library
- [ ] One-click deployment (Netlify/Vercel)
- [ ] Email integration for contact forms
- [ ] Multi-page site generation

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `BRAVE_SEARCH_API_KEY` | No | Brave Search API (for web context) |
| `TAVILY_API_KEY` | No | Tavily Search API (alternative) |

## Tech Stack

- **AI**: Claude (claude-sonnet-4-20250514)
- **Web Search**: Brave Search API / Tavily API
- **Framework**: FastAPI
- **Styling**: Tailwind CSS (via CDN)
- **Fonts**: Google Fonts (dynamic based on personality)

## Version

Current: 0.2.0

See [CHANGELOG.md](CHANGELOG.md) for version history.
