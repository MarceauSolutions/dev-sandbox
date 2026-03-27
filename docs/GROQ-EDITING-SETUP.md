# Groq-Powered File Editing — Setup Guide

## Honest Assessment

| Tool | Interactive? | Conversational? | File browsing? | Cost | Best for |
|------|-------------|-----------------|----------------|------|----------|
| **Claude Code (current)** | Yes | Yes | Yes | Anthropic subscription | Complex multi-file tasks |
| **Continue.dev + Groq** | Yes | Yes | Yes | Free (Groq free tier) | Quick edits, second opinion |
| **Cursor** | Yes | Yes | Yes | $20/mo | Full IDE replacement |
| **n8n Groq webhook** | No | No | No | Free | Automated one-shot edits |

**Recommendation**: Install Continue.dev in VS Code. It gives you a second AI assistant (Groq) alongside Claude Code. Free, 2 minutes to set up, actually conversational.

## Continue.dev + Groq Setup (2 minutes)

### Step 1: Install Continue.dev
1. Open VS Code
2. Press `Cmd+Shift+X` (Extensions)
3. Search "Continue"
4. Click Install on "Continue - Codestral, Claude, and more"

### Step 2: Get Groq API Key
1. Go to https://console.groq.com/keys
2. Click "Create API Key"
3. Copy the key (starts with `gsk_`)

### Step 3: Configure Groq in Continue
1. Click the Continue icon in VS Code sidebar (looks like a play button)
2. Click the gear icon → "Open config.json"
3. Add Groq as a model:

```json
{
  "models": [
    {
      "title": "Groq Llama 3.3 70B",
      "provider": "groq",
      "model": "llama-3.3-70b-versatile",
      "apiKey": "gsk_YOUR_KEY_HERE"
    }
  ]
}
```

4. Save. Done.

### Step 4: Use It
- Select code → press `Cmd+L` → ask Groq to edit it
- Press `Cmd+I` for inline edit suggestions
- Type in the Continue chat panel for conversational editing

## When to Use Which Tool

| Situation | Use |
|-----------|-----|
| Complex multi-file refactoring, tower work, architecture | Claude Code |
| Quick single-file edits, "change this function" | Continue.dev + Groq |
| Automated edits triggered by n8n workflows | n8n Groq webhook |
| Full IDE replacement with AI | Cursor ($20/mo) |
