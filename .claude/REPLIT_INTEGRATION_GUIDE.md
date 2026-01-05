# Replit App Integration Guide
**How to integrate the Fitness Influencer Assistant with your Replit app**

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR REPLIT APP                          │
│                    (Frontend/Backend)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP Requests
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              FASTAPI WRAPPER (Can be on Replit)             │
│              execution/fitness_assistant_api.py              │
└───────────────────────┬─────────────────────────────────────┘
                        │ Executes
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                 PYTHON EXECUTION SCRIPTS                     │
│   • video_jumpcut.py                                        │
│   • educational_graphics.py                                 │
│   • gmail_monitor.py                                        │
│   • revenue_analytics.py                                    │
│   • grok_image_gen.py                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Option 1: FastAPI Wrapper (Recommended)

### **Pros:**
- ✅ Simple HTTP API - works with any language
- ✅ Can deploy API server on Replit too
- ✅ No Claude API costs
- ✅ Full control over execution
- ✅ Easy to test with Postman/curl

### **Cons:**
- Requires running a separate API server
- No natural language interface (just direct tool calls)

### **Step-by-Step Setup:**

#### 1. Deploy API Server on Replit

**Option A: Same Replit project**
```bash
# In your Replit project terminal:
cd /path/to/dev-sandbox

# Install dependencies
pip install fastapi uvicorn python-multipart moviepy pillow

# Start API server
python execution/fitness_assistant_api.py
```

**Option B: Separate Replit project**
1. Create new Replit project (Python template)
2. Upload your `execution/` folder
3. Install dependencies:
   ```bash
   pip install fastapi uvicorn python-multipart moviepy pillow google-api-python-client google-auth
   ```
4. Create `main.py`:
   ```python
   from execution.fitness_assistant_api import app
   import uvicorn

   if __name__ == "__main__":
       uvicorn.run(app, host="0.0.0.0", port=8000)
   ```
5. Run project - Replit will expose it publicly

#### 2. Call API from Your App

**JavaScript/TypeScript (Next.js, React, etc.):**

```javascript
// Example: Edit video with jump cuts
async function editVideo(videoFile) {
  const formData = new FormData();
  formData.append('video', videoFile);

  const response = await fetch('https://your-replit-api.repl.co/api/video/edit', {
    method: 'POST',
    body: formData
  });

  const editedVideo = await response.blob();
  return editedVideo;
}

// Example: Create educational graphic
async function createGraphic(title, points, platform = 'instagram_post') {
  const response = await fetch('https://your-replit-api.repl.co/api/graphics/create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      title,
      points,
      platform
    })
  });

  const graphic = await response.blob();
  return graphic;
}

// Example: Get email digest
async function getEmailDigest(hoursBack = 24) {
  const response = await fetch('https://your-replit-api.repl.co/api/email/digest', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      hours_back: hoursBack
    })
  });

  const digest = await response.json();
  return digest;
}

// Example: Generate AI image
async function generateImage(prompt, count = 1) {
  const response = await fetch('https://your-replit-api.repl.co/api/images/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      prompt,
      count
    })
  });

  const image = await response.blob();
  return image;
}
```

**Python (Flask/Django backend):**

```python
import requests

API_URL = "https://your-replit-api.repl.co"

def edit_video(video_path):
    with open(video_path, 'rb') as f:
        files = {'video': f}
        response = requests.post(
            f"{API_URL}/api/video/edit",
            files=files
        )
    return response.content  # Edited video bytes

def create_graphic(title, points, platform='instagram_post'):
    response = requests.post(
        f"{API_URL}/api/graphics/create",
        json={
            'title': title,
            'points': points,
            'platform': platform
        }
    )
    return response.content  # Graphic image bytes

def get_email_digest(hours_back=24):
    response = requests.post(
        f"{API_URL}/api/email/digest",
        json={'hours_back': hours_back}
    )
    return response.json()
```

#### 3. Environment Variables

Set these in your Replit secrets:

```bash
# For Gmail integration
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token

# For Grok image generation
XAI_API_KEY=your_xai_api_key

# For Amazon tools (if using)
AMAZON_REFRESH_TOKEN=your_token
AMAZON_LWA_APP_ID=your_app_id
AMAZON_LWA_CLIENT_SECRET=your_secret
```

#### 4. Test API

Visit the auto-generated docs:
```
https://your-replit-api.repl.co/docs
```

Test endpoints with:
```bash
# Health check
curl https://your-replit-api.repl.co/api/status

# Create graphic (example)
curl -X POST https://your-replit-api.repl.co/api/graphics/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fitness Tip",
    "points": ["Eat protein", "Lift weights", "Stay consistent"],
    "platform": "instagram_post"
  }' \
  --output graphic.jpg
```

---

## Option 2: Claude API Integration

### **Pros:**
- ✅ Natural language interface
- ✅ Conversational AI assistant
- ✅ Can reason and make decisions

### **Cons:**
- ❌ Requires Claude API subscription ($$$)
- ❌ More complex to implement
- ❌ Need to handle tool calling

### **Step-by-Step Setup:**

#### 1. Get Claude API Key

1. Sign up at https://console.anthropic.com
2. Create API key
3. Add to Replit secrets: `ANTHROPIC_API_KEY`

#### 2. Install Anthropic SDK

```bash
pip install anthropic
```

#### 3. Create Claude Agent in Your App

```python
import anthropic
import os

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

def chat_with_assistant(user_message):
    """Send message to fitness influencer assistant."""

    # System prompt with access to your tools
    system_prompt = """
    You are a fitness influencer assistant with access to these tools:

    1. video_jumpcut - Edit videos with automatic jump cuts
    2. educational_graphics - Create branded fitness graphics
    3. gmail_monitor - Monitor and summarize emails
    4. revenue_analytics - Generate financial reports
    5. grok_image_gen - Generate AI images

    When the user asks for help with these tasks, execute the appropriate tool.

    Execution scripts are available at /path/to/execution/
    """

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    return response.content[0].text

# Example usage
result = chat_with_assistant(
    "Create an educational graphic about staying lean without tracking macros"
)
print(result)
```

#### 4. Implement Tool Calling

For full integration with tool execution, you'll need to implement the Anthropic tool calling pattern. See: https://docs.anthropic.com/en/docs/build-with-claude/tool-use

---

## Option 3: Hybrid Approach (Best of Both Worlds)

Combine FastAPI wrapper + Claude API for natural language + tool execution:

```python
import anthropic
import requests

# FastAPI wrapper for tool execution
API_URL = "https://your-replit-api.repl.co"

# Claude API for natural language
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def intelligent_assistant(user_message):
    """
    Natural language interface that executes tools via FastAPI.
    """

    # Define tools for Claude
    tools = [
        {
            "name": "edit_video",
            "description": "Edit video with automatic jump cuts to remove silence",
            "input_schema": {
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "Path to video file"},
                    "silence_threshold": {"type": "number", "description": "Silence threshold in dB", "default": -40}
                },
                "required": ["video_path"]
            }
        },
        {
            "name": "create_graphic",
            "description": "Create branded educational fitness graphic",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Main title"},
                    "points": {"type": "array", "items": {"type": "string"}, "description": "Key points"},
                    "platform": {"type": "string", "enum": ["instagram_post", "youtube_thumbnail", "tiktok"]}
                },
                "required": ["title", "points"]
            }
        }
    ]

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        tools=tools,
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    # Check if Claude wants to use a tool
    for content_block in response.content:
        if content_block.type == "tool_use":
            tool_name = content_block.name
            tool_input = content_block.input

            # Execute tool via FastAPI
            if tool_name == "edit_video":
                result = requests.post(
                    f"{API_URL}/api/video/edit",
                    files={'video': open(tool_input['video_path'], 'rb')}
                )
                return result.content

            elif tool_name == "create_graphic":
                result = requests.post(
                    f"{API_URL}/api/graphics/create",
                    json=tool_input
                )
                return result.content

    # Return text response if no tool used
    return response.content[0].text

# Example usage
result = intelligent_assistant(
    "Create a fitness tip graphic about protein intake with 3 key points"
)
```

---

## Deployment Checklist

### For FastAPI Wrapper:

- [ ] Create new Replit project or add to existing
- [ ] Upload `execution/` folder with all scripts
- [ ] Install dependencies: `pip install fastapi uvicorn python-multipart moviepy pillow google-api-python-client google-auth`
- [ ] Set environment variables in Replit Secrets
- [ ] Run `fitness_assistant_api.py`
- [ ] Test endpoints at `/docs`
- [ ] Update CORS settings to allow your frontend domain
- [ ] Get Replit public URL
- [ ] Update your app to call API endpoints

### For Claude API Integration:

- [ ] Get Anthropic API key
- [ ] Add key to Replit Secrets
- [ ] Install `pip install anthropic`
- [ ] Implement tool calling pattern
- [ ] Test natural language queries
- [ ] Monitor API costs

---

## Example Frontend Components

### React Component for Video Editor

```jsx
import React, { useState } from 'react';

function VideoEditor() {
  const [videoFile, setVideoFile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editedVideo, setEditedVideo] = useState(null);

  const handleEdit = async () => {
    if (!videoFile) return;

    setEditing(true);

    const formData = new FormData();
    formData.append('video', videoFile);

    try {
      const response = await fetch('https://your-api.repl.co/api/video/edit', {
        method: 'POST',
        body: formData
      });

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setEditedVideo(url);
    } catch (error) {
      console.error('Error editing video:', error);
    } finally {
      setEditing(false);
    }
  };

  return (
    <div>
      <h2>Automatic Jump Cut Editor</h2>
      <input
        type="file"
        accept="video/*"
        onChange={(e) => setVideoFile(e.target.files[0])}
      />
      <button onClick={handleEdit} disabled={editing || !videoFile}>
        {editing ? 'Editing...' : 'Edit Video'}
      </button>

      {editedVideo && (
        <div>
          <h3>Edited Video:</h3>
          <video src={editedVideo} controls style={{ maxWidth: '100%' }} />
          <a href={editedVideo} download="edited_video.mp4">Download</a>
        </div>
      )}
    </div>
  );
}

export default VideoEditor;
```

### React Component for Graphics Generator

```jsx
import React, { useState } from 'react';

function GraphicsGenerator() {
  const [title, setTitle] = useState('');
  const [points, setPoints] = useState(['', '', '']);
  const [platform, setPlatform] = useState('instagram_post');
  const [graphic, setGraphic] = useState(null);
  const [generating, setGenerating] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);

    try {
      const response = await fetch('https://your-api.repl.co/api/graphics/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          points: points.filter(p => p.trim()),
          platform
        })
      });

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setGraphic(url);
    } catch (error) {
      console.error('Error generating graphic:', error);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div>
      <h2>Educational Graphics Generator</h2>

      <input
        type="text"
        placeholder="Title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />

      {points.map((point, i) => (
        <input
          key={i}
          type="text"
          placeholder={`Point ${i + 1}`}
          value={point}
          onChange={(e) => {
            const newPoints = [...points];
            newPoints[i] = e.target.value;
            setPoints(newPoints);
          }}
        />
      ))}

      <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
        <option value="instagram_post">Instagram Post</option>
        <option value="instagram_story">Instagram Story</option>
        <option value="youtube_thumbnail">YouTube Thumbnail</option>
        <option value="tiktok">TikTok</option>
      </select>

      <button onClick={handleGenerate} disabled={generating || !title}>
        {generating ? 'Generating...' : 'Create Graphic'}
      </button>

      {graphic && (
        <div>
          <h3>Generated Graphic:</h3>
          <img src={graphic} alt="Generated" style={{ maxWidth: '100%' }} />
          <a href={graphic} download="fitness_graphic.jpg">Download</a>
        </div>
      )}
    </div>
  );
}

export default GraphicsGenerator;
```

---

## Recommended Approach

**For Your Situation:**

1. **Start with FastAPI Wrapper** (Option 1)
   - Easiest to implement
   - No API costs
   - Works with any frontend
   - Can add Claude later if needed

2. **Deploy API on Replit**
   - Create separate Replit project
   - Upload execution scripts
   - Run FastAPI server
   - Get public URL

3. **Call from Your App**
   - Use fetch/axios from frontend
   - Pass video files, text, images
   - Get back processed results

4. **Optional: Add Claude Later**
   - If you want natural language interface
   - Implement hybrid approach
   - Claude understands intent → calls tools via FastAPI

---

## Next Steps

1. Let me know which option you prefer
2. I can help you deploy the FastAPI wrapper to Replit
3. I can create example frontend components for your specific framework
4. We can test the integration end-to-end

What framework is your Replit app built with? (React, Next.js, Flask, etc.)
