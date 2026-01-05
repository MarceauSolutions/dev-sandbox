# Integrating Fitness Assistant with marceausolutions.com

**Goal:** Add AI-powered fitness tools to your existing GitHub Pages website

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         marceausolutions.com (GitHub Pages)             │
│         • Static HTML/CSS/JavaScript                    │
│         • Your existing website                         │
└──────────────────┬──────────────────────────────────────┘
                   │ JavaScript fetch() calls
                   ↓
┌─────────────────────────────────────────────────────────┐
│     FastAPI Server (Replit - Free or $7/month)          │
│     • https://your-username-fitness-api.repl.co         │
│     • Runs Python execution scripts                     │
└──────────────────┬──────────────────────────────────────┘
                   │ Executes tools
                   ↓
┌─────────────────────────────────────────────────────────┐
│              Python Execution Scripts                    │
│     • video_jumpcut.py                                  │
│     • educational_graphics.py                           │
│     • gmail_monitor.py                                  │
│     • revenue_analytics.py                              │
│     • grok_image_gen.py                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Setup

### **Step 1: Deploy API to Replit**

1. **Create New Replit Project**
   - Go to https://replit.com
   - Click "Create Repl"
   - Choose "Python" template
   - Name: `fitness-influencer-api`

2. **Upload Files to Replit**
   - Upload entire `execution/` folder from dev-sandbox
   - Upload `execution/fitness_assistant_api.py`

3. **Install Dependencies**

   Create `requirements.txt`:
   ```
   fastapi==0.109.0
   uvicorn==0.27.0
   python-multipart==0.0.6
   moviepy==1.0.3
   pillow==10.2.0
   google-api-python-client==2.116.0
   google-auth==2.27.0
   google-auth-oauthlib==1.2.0
   google-auth-httplib2==0.2.0
   requests==2.31.0
   python-dotenv==1.0.0
   ```

   Replit will auto-install, or run:
   ```bash
   pip install -r requirements.txt
   ```

4. **Create main.py**
   ```python
   from execution.fitness_assistant_api import app
   import uvicorn

   if __name__ == "__main__":
       uvicorn.run(app, host="0.0.0.0", port=8000)
   ```

5. **Configure CORS**

   Edit `execution/fitness_assistant_api.py`:
   ```python
   # Update the CORS middleware
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "https://marceausolutions.com",
           "http://marceausolutions.com",
           "https://your-github-username.github.io",  # If using GitHub subdomain
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

6. **Set Environment Variables**

   In Replit, go to "Secrets" (🔒 icon) and add:
   ```
   XAI_API_KEY=your_grok_api_key
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```

7. **Run the Server**
   ```bash
   python main.py
   ```

8. **Get Your API URL**
   - Replit will show: `https://your-username-fitness-influencer-api.repl.co`
   - Save this URL - you'll use it in your website

9. **Test API**
   - Visit: `https://your-api-url.repl.co/docs`
   - You should see FastAPI interactive documentation
   - Test the endpoints directly in browser

---

### **Step 2: Add to marceausolutions.com**

#### Option A: Add Tools Page

Create new file `tools.html` in your GitHub Pages repo:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fitness Creator Tools | Marceau Solutions</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        h1 {
            text-align: center;
            color: #D4AF37;
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }

        .tagline {
            text-align: center;
            color: #ffffff;
            font-size: 1.2em;
            margin-bottom: 40px;
            letter-spacing: 2px;
        }

        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }

        .tool-card {
            background: rgba(255,255,255,0.05);
            border: 2px solid #D4AF37;
            border-radius: 15px;
            padding: 30px;
            backdrop-filter: blur(10px);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .tool-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(212, 175, 55, 0.3);
        }

        .tool-card h2 {
            color: #D4AF37;
            margin-bottom: 15px;
            font-size: 1.8em;
        }

        .tool-card p {
            color: #cccccc;
            margin-bottom: 20px;
            line-height: 1.6;
        }

        input, textarea, select {
            width: 100%;
            padding: 12px;
            margin-bottom: 15px;
            background: rgba(255,255,255,0.1);
            border: 1px solid #D4AF37;
            border-radius: 8px;
            color: #ffffff;
            font-size: 1em;
        }

        input::placeholder, textarea::placeholder {
            color: rgba(255,255,255,0.5);
        }

        textarea {
            min-height: 100px;
            resize: vertical;
        }

        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #D4AF37 0%, #B8860B 100%);
            border: none;
            border-radius: 8px;
            color: #000000;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        button:hover {
            transform: scale(1.02);
            box-shadow: 0 5px 20px rgba(212, 175, 55, 0.5);
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .result {
            margin-top: 20px;
            padding: 20px;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            display: none;
        }

        .result.show {
            display: block;
        }

        .result img, .result video {
            max-width: 100%;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        .download-btn {
            display: inline-block;
            padding: 10px 20px;
            background: #D4AF37;
            color: #000;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
        }

        .loading {
            text-align: center;
            color: #D4AF37;
            font-size: 1.2em;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>FITNESS CREATOR TOOLS</h1>
        <p class="tagline">EMBRACE THE PAIN & DEFY THE ODDS</p>

        <div class="tools-grid">
            <!-- Educational Graphics Generator -->
            <div class="tool-card">
                <h2>📊 Branded Graphics</h2>
                <p>Create professional educational fitness graphics with your branding</p>

                <input type="text" id="graphic-title" placeholder="Title (e.g., Staying Lean)">
                <textarea id="graphic-points" placeholder="Key points (one per line)&#10;Focus on whole foods&#10;Eat protein with every meal&#10;Listen to hunger cues"></textarea>

                <select id="graphic-platform">
                    <option value="instagram_post">Instagram Post (1080x1080)</option>
                    <option value="instagram_story">Instagram Story (1080x1920)</option>
                    <option value="youtube_thumbnail">YouTube Thumbnail (1280x720)</option>
                    <option value="tiktok">TikTok (1080x1920)</option>
                </select>

                <button onclick="createGraphic()" id="graphic-btn">Generate Graphic</button>

                <div id="graphic-result" class="result"></div>
            </div>

            <!-- Video Jump Cut Editor -->
            <div class="tool-card">
                <h2>🎬 Video Editor</h2>
                <p>Automatically remove silence and add jump cuts to your videos</p>

                <input type="file" id="video-upload" accept="video/*">
                <p style="font-size: 0.9em; color: #D4AF37;">⚠️ Video processing may take several minutes</p>

                <button onclick="editVideo()" id="video-btn">Edit Video</button>

                <div id="video-result" class="result"></div>
            </div>

            <!-- AI Image Generator -->
            <div class="tool-card">
                <h2>🎨 AI Image Generator</h2>
                <p>Generate custom images using AI ($0.07 per image)</p>

                <textarea id="image-prompt" placeholder="Describe the image you want...&#10;Example: Fitness influencer doing workout in modern gym"></textarea>

                <input type="number" id="image-count" min="1" max="10" value="1" placeholder="Number of images (1-10)">

                <button onclick="generateImage()" id="image-btn">Generate Image</button>

                <div id="image-result" class="result"></div>
            </div>

            <!-- Email Digest -->
            <div class="tool-card">
                <h2>📧 Email Digest</h2>
                <p>Get a categorized summary of your recent emails</p>

                <input type="number" id="email-hours" min="1" max="168" value="24" placeholder="Hours to look back">

                <button onclick="getEmailDigest()" id="email-btn">Get Digest</button>

                <div id="email-result" class="result"></div>
            </div>
        </div>
    </div>

    <script>
        // IMPORTANT: Replace with your actual Replit API URL
        const API_URL = 'https://YOUR-USERNAME-fitness-influencer-api.repl.co';

        async function createGraphic() {
            const title = document.getElementById('graphic-title').value;
            const pointsText = document.getElementById('graphic-points').value;
            const platform = document.getElementById('graphic-platform').value;
            const btn = document.getElementById('graphic-btn');
            const resultDiv = document.getElementById('graphic-result');

            if (!title || !pointsText) {
                alert('Please fill in title and points');
                return;
            }

            const points = pointsText.split('\\n').filter(p => p.trim());

            btn.disabled = true;
            btn.textContent = 'Generating...';
            resultDiv.innerHTML = '<div class="loading">Creating your graphic...</div>';
            resultDiv.classList.add('show');

            try {
                const response = await fetch(`${API_URL}/api/graphics/create`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, points, platform })
                });

                if (!response.ok) throw new Error('Generation failed');

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);

                resultDiv.innerHTML = `
                    <h3>✅ Graphic Generated!</h3>
                    <img src="${url}" alt="Generated graphic">
                    <a href="${url}" download="fitness_graphic.jpg" class="download-btn">⬇️ Download Graphic</a>
                `;
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: #ff6b6b;">Error: ${error.message}</p>`;
            } finally {
                btn.disabled = false;
                btn.textContent = 'Generate Graphic';
            }
        }

        async function editVideo() {
            const fileInput = document.getElementById('video-upload');
            const file = fileInput.files[0];
            const btn = document.getElementById('video-btn');
            const resultDiv = document.getElementById('video-result');

            if (!file) {
                alert('Please select a video file');
                return;
            }

            const formData = new FormData();
            formData.append('video', file);

            btn.disabled = true;
            btn.textContent = 'Processing...';
            resultDiv.innerHTML = '<div class="loading">⏳ Editing video... this may take several minutes</div>';
            resultDiv.classList.add('show');

            try {
                const response = await fetch(`${API_URL}/api/video/edit`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) throw new Error('Video processing failed');

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);

                resultDiv.innerHTML = `
                    <h3>✅ Video Edited!</h3>
                    <video src="${url}" controls></video>
                    <a href="${url}" download="edited_video.mp4" class="download-btn">⬇️ Download Video</a>
                `;
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: #ff6b6b;">Error: ${error.message}</p>`;
            } finally {
                btn.disabled = false;
                btn.textContent = 'Edit Video';
            }
        }

        async function generateImage() {
            const prompt = document.getElementById('image-prompt').value;
            const count = parseInt(document.getElementById('image-count').value);
            const btn = document.getElementById('image-btn');
            const resultDiv = document.getElementById('image-result');

            if (!prompt) {
                alert('Please enter an image description');
                return;
            }

            btn.disabled = true;
            btn.textContent = 'Generating...';
            resultDiv.innerHTML = '<div class="loading">🎨 Generating AI image...</div>';
            resultDiv.classList.add('show');

            try {
                const response = await fetch(`${API_URL}/api/images/generate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt, count })
                });

                if (!response.ok) throw new Error('Image generation failed');

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);

                resultDiv.innerHTML = `
                    <h3>✅ Image Generated!</h3>
                    <p>Cost: $${(count * 0.07).toFixed(2)}</p>
                    <img src="${url}" alt="Generated image">
                    <a href="${url}" download="generated_image.png" class="download-btn">⬇️ Download Image</a>
                `;
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: #ff6b6b;">Error: ${error.message}</p>`;
            } finally {
                btn.disabled = false;
                btn.textContent = 'Generate Image';
            }
        }

        async function getEmailDigest() {
            const hours = parseInt(document.getElementById('email-hours').value);
            const btn = document.getElementById('email-btn');
            const resultDiv = document.getElementById('email-result');

            btn.disabled = true;
            btn.textContent = 'Fetching...';
            resultDiv.innerHTML = '<div class="loading">📧 Analyzing emails...</div>';
            resultDiv.classList.add('show');

            try {
                const response = await fetch(`${API_URL}/api/email/digest`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ hours_back: hours })
                });

                if (!response.ok) throw new Error('Email digest failed');

                const data = await response.json();

                resultDiv.innerHTML = `
                    <h3>✅ Email Digest</h3>
                    <pre style="white-space: pre-wrap; color: #D4AF37;">${data.output}</pre>
                `;
            } catch (error) {
                resultDiv.innerHTML = `<p style="color: #ff6b6b;">Error: ${error.message}</p>`;
            } finally {
                btn.disabled = false;
                btn.textContent = 'Get Digest';
            }
        }
    </script>
</body>
</html>
```

#### Option B: Add to Existing Page

If you want to add tools to an existing page on marceausolutions.com, just copy the tool cards and JavaScript from above.

---

### **Step 3: Deploy to GitHub Pages**

1. **Add tools.html** to your GitHub repo
2. **Commit and push:**
   ```bash
   git add tools.html
   git commit -m "Add fitness creator tools"
   git push
   ```
3. **Access at:** https://marceausolutions.com/tools.html

---

### **Step 4: Update API URL**

In `tools.html`, find this line:
```javascript
const API_URL = 'https://YOUR-USERNAME-fitness-influencer-api.repl.co';
```

Replace with your actual Replit URL from Step 1.

---

## Testing

1. Visit: https://marceausolutions.com/tools.html
2. Try each tool:
   - Create a graphic
   - Upload a short video (start with <1 min)
   - Generate an AI image
   - Get email digest (requires Google OAuth setup)

---

## Next Steps

### Free Tier Limitations:
- **Replit Free:** Server sleeps after inactivity (wakes on request)
- **Solution:** Upgrade to Replit Hacker ($7/month) for always-on

### Better Hosting (Optional):
Move API from Replit to:
- **Railway.app** (better free tier)
- **Render.com** (professional)
- **DigitalOcean** ($5/month)

---

## Troubleshooting

**CORS Errors:**
- Make sure marceausolutions.com is in allowed_origins
- Check browser console for errors

**API Not Responding:**
- Replit free tier sleeps - first request takes ~30s
- Check API status: https://your-api.repl.co/api/status

**Video Processing Timeout:**
- Use shorter videos first (<2 min)
- Upgrade Replit plan for better resources

---

You're all set! Your website will now have AI-powered fitness tools that match your Marceau Solutions branding! 🎬✨
