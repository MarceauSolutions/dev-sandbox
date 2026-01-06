# Fitness Influencer AI - Setup Guide

**Welcome!** This guide will walk you through personalizing your AI assistant for your fitness business.

**Estimated Time:** 5-10 minutes  
**What You'll Need:** API keys (we'll show you how to get them)  
**Cost:** Most features are pay-per-use (as low as $0.06/video)

---

## 📋 Overview

Your Fitness Influencer AI is a powerful assistant that helps you:
- ✂️ **Edit videos** automatically (remove silence, add jump cuts)
- 🎨 **Create graphics** for Instagram, YouTube, TikTok
- 🤖 **Generate AI images** for your content ($0.07/image)
- 🎬 **Produce video ads** automatically ($0.34/ad)
- 📧 **Monitor emails** and categorize leads
- 💪 **Generate workout plans** for clients
- 🥗 **Create nutrition guides** with macro calculations
- 📊 **Track revenue** and analytics

**Before you can use these features, you need to personalize the system with YOUR information and API keys.**

---

## 🚀 Quick Start: Choose Your Setup Method

We provide **two ways** to set up your AI assistant. Pick the one you're most comfortable with:

### Option 1: Web Form (Easiest) 🌐
**Best for:** Non-technical users, visual learners  
**Time:** 5-7 minutes  
**Interface:** Beautiful web form with step-by-step guidance

👉 [Jump to Web Form Instructions](#option-1-web-form-setup)

---

### Option 2: Command Line Wizard 💻
**Best for:** Developers, technical users  
**Time:** 5-10 minutes  
**Interface:** Interactive terminal with colored output

👉 [Jump to CLI Wizard Instructions](#option-2-cli-wizard-setup)

---

## Option 1: Web Form Setup

### Step 1: Open the Setup Form

1. **Download the setup form:**
   - If you received `setup_form.html` via email, open it in your browser
   - OR visit: `file:///path/to/setup_form.html` (replace with actual path)

2. **You'll see a beautiful purple-gradient interface with 8 steps**

### Step 2: Personal Information

Fill in your details:
- ✅ **Full Name** (required) - e.g., "Sarah Johnson"
- ✅ **Email** (required) - e.g., "sarah@fitcoachpro.com"
- **Business Name** (optional) - e.g., "FitCoach Pro"
- **Website** (optional) - e.g., "https://fitcoachpro.com"
- **Instagram Handle** (optional) - e.g., "sarahfitness" (no @ symbol)

**Click "Next →"**

---

### Step 3: Brand Customization

Make the AI match your brand:
- **Tagline** (optional) - e.g., "Transform Your Body, Transform Your Life"
- **Primary Color** (optional) - Hex code like "#FF5733" (used in graphics)
- **Logo URL** (optional) - Direct link to your logo image

**Click "Next →"**

---

### Step 4: Grok/xAI API Key (Required)

**What it does:** Generates AI images for your content  
**Cost:** $0.07 per image  
**Why you need it:** Powers the AI image generation feature

#### How to Get Your Grok API Key:

1. **Go to:** https://console.x.ai/
2. **Sign up** or log in with your X (Twitter) account
3. Navigate to **"API Keys"** section
4. Click **"Create new API key"**
5. **Copy the key** (it starts with `xai-`)
6. **Paste it** in the form below

**The form provides clickable links and clear instructions!**

**Click "Next →"**

---

### Step 5: Shotstack API Key (Required)

**What it does:** Creates professional video ads automatically  
**Cost:** $0.06 per video  
**Why you need it:** Powers the video ad creation feature

#### How to Get Your Shotstack API Key:

1. **Go to:** https://shotstack.io/
2. Click **"Sign Up"** (free account available)
3. **Verify your email**
4. Go to your **Dashboard**
5. Find **"API Keys"** in the left menu
6. Copy your **"Stage"** environment key (for testing)
7. **Paste it** in the form

**Choose environment:** Stage (for testing) or Production (v1)

**Click "Next →"**

---

### Step 6: Optional Integrations

These are **optional** but enable powerful features:

#### Google APIs (FREE)
**Enables:** Email monitoring, calendar reminders, revenue analytics

- Google Client ID
- Google Client Secret
- Google Refresh Token

**Note:** Setting up Google OAuth is more involved. You can skip this and add it later.

#### Canva API (FREE with Pro account)
**Enables:** Advanced design templates from Canva

- Canva API Key

**The form shows you exactly where to get each key!**

**Click "Next →"**

---

### Step 7: Feature Preferences

Choose which features to enable by default:

- ✅ **Video Editing** - Jump cuts, silence removal
- ✅ **Graphics Generation** - Branded content for social media
- ☐ **Email Monitoring** - Requires Google API
- ✅ **AI Image Generation** - Costs $0.07/image
- ✅ **Video Ad Creation** - Costs $0.34/video
- ✅ **Workout Plans** - Generate custom workout programs
- ✅ **Nutrition Guides** - Calculate macros and meal plans
- ✅ **Auto Branding** - Add your logo/colors to all content

**Click "Next →"**

---

### Step 8: Review & Download

1. **Review your configuration** - Check all details are correct
2. **Click "Generate Files →"**
3. **Download both files:**
   - 📄 **`.env`** - Your environment configuration
   - ⚙️ **`user_config.json`** - Your personalized settings

### Step 9: Install Configuration

1. **Place the `.env` file** in your project root directory:
   ```
   /Users/your-username/fitness-influencer-ai/.env
   ```

2. **Place the `user_config.json` file** in the same directory

3. **You're ready!** Proceed to [Next Steps](#next-steps-after-setup)

---

## Option 2: CLI Wizard Setup

### Step 1: Open Terminal

**Mac/Linux:**
- Press `Cmd + Space`, type "Terminal", press Enter

**Windows:**
- Press `Win + R`, type "cmd", press Enter

### Step 2: Navigate to Project Directory

```bash
cd /path/to/fitness-influencer-ai
```

### Step 3: Run the Setup Wizard

```bash
python execution/setup_wizard.py
```

You'll see a colorful welcome screen:

```
======================================================================
              🎯 FITNESS INFLUENCER AI - SETUP WIZARD
======================================================================

Welcome! This wizard will help you personalize your AI assistant.
We'll walk you through obtaining API keys and configuring your settings.

⏱  Estimated time: 5-10 minutes

➜ Ready to begin (yes/no): 
```

Type **`yes`** and press Enter.

---

### Step 4: Follow the Interactive Prompts

The wizard will guide you through **7 steps** with colored output:

#### 🟦 Step 1: Personal Information
```
▶ Step 1: Personal Information

Let's start with some basic information about you.

➜ Your full name: Sarah Johnson
➜ Your email address: sarah@fitcoachpro.com
➜ Your business/brand name (optional): FitCoach Pro
➜ Your website URL (optional): https://fitcoachpro.com
➜ Your Instagram handle (without @) (optional): sarahfitness

✓ Personal information saved!
```

#### 🟦 Step 2: Brand Customization
```
▶ Step 2: Brand Customization

Customize how your AI assistant represents your brand.

➜ Your brand tagline (optional): Transform Your Body, Transform Your Life
➜ Primary brand color (hex code, e.g., '#FF5733') (optional): #4A90E2
➜ Logo URL (for graphics) (optional): https://fitcoachpro.com/logo.png

✓ Branding configured!
```

#### 🟦 Step 3: Grok/xAI API Key (Required)
```
▶ Step 3: Required API Keys

ℹ 📸 Grok/xAI API Key (for AI image generation)

This allows you to generate AI images for your content.
Cost: $0.07 per image

How to get your Grok API key:
  1. Go to https://console.x.ai/
  2. Sign up or log in with your X (Twitter) account
  3. Navigate to 'API Keys' section
  4. Click 'Create new API key'
  5. Copy the key (it starts with 'xai-')
  6. Paste it below

➜ Do you have your Grok API key ready (yes/no): yes
➜ Paste your Grok API key here: xai-abc123...

✓ Grok API key saved!
```

#### 🟦 Step 4: Shotstack API Key (Required)
```
ℹ 🎬 Shotstack API Key (for video generation)

This allows you to create professional video ads automatically.
Cost: $0.06 per video

How to get your Shotstack API key:
  1. Go to https://shotstack.io/
  2. Click 'Sign Up' (free account available)
  3. Verify your email
  4. Go to your Dashboard
  5. Find 'API Keys' in the left menu
  6. Copy your 'Stage' environment key for testing
  7. Paste it below

➜ Do you have your Shotstack API key ready (yes/no): yes
➜ Paste your Shotstack API key here: abc123def456...
➜ Which environment? (stage/v1): stage

✓ Shotstack API key saved!
```

#### 🟦 Step 5: Optional Integrations
```
▶ Step 4: Optional Integrations

These are optional but enable additional features.

➜ Would you like to set up Google integrations (Gmail, Calendar, Sheets) (yes/no): no

➜ Would you like to set up Canva integration (yes/no): no
```

#### 🟦 Step 6: Feature Preferences
```
▶ Step 5: Feature Preferences

Customize which features are enabled by default.

➜ Enable video editing (jump cuts, silence removal) (yes/no): yes
➜ Enable graphics generation (branded content) (yes/no): yes
➜ Enable email monitoring and categorization (yes/no): no
➜ Enable AI image generation (costs $0.07/image) (yes/no): yes
➜ Enable video ad creation (costs $0.34/video) (yes/no): yes
➜ Enable workout plan generation (yes/no): yes
➜ Enable nutrition guide generation (yes/no): yes
➜ Automatically add your branding to all content (yes/no): yes

✓ Preferences saved!
```

#### 🟦 Step 7: Save & Test
```
▶ Step 6: Saving Configuration

Saving your personalized configuration...

✓ Configuration saved to: /path/to/user_config.json
✓ Environment file created: /path/to/.env
✓ Personalized settings saved: /path/to/.claude/personalized_settings.json

➜ Would you like to test your API connections now (yes/no): yes

▶ Step 7: Testing Connections

Testing your API connections...

ℹ Testing Grok/xAI API...
✓ Grok API connection successful!

ℹ Testing Shotstack API...
✓ Shotstack API connection successful!
```

---

### Step 5: Setup Complete! 🎉

```
======================================================================
                      🎉 SETUP COMPLETE!
======================================================================

Your Fitness Influencer AI is now personalized and ready to use!

Configuration Summary:
  Name: Sarah Johnson
  Business: FitCoach Pro
  Email: sarah@fitcoachpro.com

Enabled Features (7):
  ✓ Video Editing
  ✓ Graphics Generation
  ✓ Ai Images
  ✓ Video Ads
  ✓ Workout Plans
  ✓ Nutrition Guides
  ✓ Auto Branding

Next Steps:
  1. Test your setup: ./quick_test.sh
  2. Review your configuration: cat .env
  3. Deploy to Railway: See DEPLOYMENT_GUIDE.md
  4. Start using: Visit marceausolutions.com/assistant.html

Need help? See SETUP_GUIDE.md for detailed documentation
```

---

## Next Steps After Setup

### 1. Test Your Configuration

Run the automated test suite:

```bash
chmod +x quick_test.sh
./quick_test.sh
```

**Expected output:**
```
🧪 Running Fitness Influencer AI Test Suite...

✓ Test 1: Workout Plan Generator
✓ Test 2: Nutrition Guide Generator
✓ Test 3: Living Documentation System
✓ Test 4: Capability Gap Monitoring
✓ Test 5: File Validation
✓ Test 6: JSON Validation
✓ Test 7: Output Files

========================================
✅ ALL TESTS PASSED (7/7)
========================================
```

---

### 2. Deploy to Production (Optional)

If you want to deploy your AI assistant to the cloud:

1. **Read the deployment guide:**
   ```bash
   cat DEPLOYMENT_GUIDE.md
   ```

2. **Deploy to Railway:**
   - See DEPLOYMENT_GUIDE.md for step-by-step instructions
   - Railway provides free hosting for hobby projects

---

### 3. Start Using Your AI Assistant

**Two ways to use your AI:**

#### Option A: Web Interface
Visit: https://marceausolutions.com/assistant.html

- Upload videos for editing
- Request graphics generation
- Create workout plans
- Generate nutrition guides
- All from a beautiful web interface!

#### Option B: Command Line
```bash
# Generate a workout plan
python execution/workout_plan_generator.py \
  --days 4 \
  --goal "Muscle Gain" \
  --level intermediate \
  --equipment full_gym

# Create a nutrition guide
python execution/nutrition_guide_generator.py \
  --weight 180 \
  --goal "Lean Bulk" \
  --diet flexible

# Edit a video (remove silence)
python execution/video_jumpcut.py \
  --input raw_video.mp4 \
  --output edited_video.mp4
```

---

## 🔧 Troubleshooting

### Issue: "API key invalid" error

**Solution:**
1. Double-check you copied the full API key (no spaces)
2. Verify the key starts with the correct prefix:
   - Grok: `xai-`
   - Shotstack: varies
3. Check if the key is activated in the provider's dashboard

---

### Issue: ".env file not found" error

**Solution:**
```bash
# Check if .env exists
ls -la | grep .env

# If missing, run setup again:
python execution/setup_wizard.py
```

---

### Issue: "Permission denied" error

**Solution:**
```bash
# Make scripts executable
chmod +x quick_test.sh
chmod +x execution/*.py

# Try again
./quick_test.sh
```

---

### Issue: Google OAuth not working

**Solution:**
Google OAuth requires additional setup:

1. Go to: https://console.cloud.google.com/
2. Create a new project
3. Enable Gmail, Calendar, and Sheets APIs
4. Create OAuth credentials (Desktop app)
5. Download `credentials.json`
6. Run: `python execution/google_oauth_setup.py`
7. Follow the browser authorization flow

**Note:** Google setup is optional. You can skip it if you don't need email/calendar features.

---

## 💰 Cost Breakdown

**Most features are FREE!** Only AI generation has costs:

| Feature | Cost | When You're Charged |
|---------|------|---------------------|
| Video Editing | **FREE** | Never |
| Graphics Generation | **FREE** | Never |
| Workout Plans | **FREE** | Never |
| Nutrition Guides | **FREE** | Never |
| Email Monitoring | **FREE** | Never |
| **AI Image Generation** | **$0.07/image** | When you request AI images |
| **Video Ad Creation** | **$0.34/ad** | When you create video ads ($0.07×4 images + $0.06 video) |

**Example monthly costs:**
- Light use (10 AI images, 5 video ads): $2.40
- Medium use (50 AI images, 20 video ads): $10.30
- Heavy use (200 AI images, 100 video ads): $48.00

**All other features are completely free with no usage limits!**

---

## 📚 Additional Resources

- **Optimization Report:** `FITNESS_INFLUENCER_OPTIMIZATION_REPORT.md`
- **Deployment Guide:** `DEPLOYMENT_GUIDE.md`
- **Testing Guide:** `TESTING_GUIDE.md`
- **Session Log:** `.claude/SESSION_LOG.md`

---

## 🎯 Feature Highlights

### Video Editing (FREE)
- Automatic silence removal
- Jump cut detection
- Processing time: ~2 minutes per 10-minute video
- Supports: MP4, MOV, AVI

### Graphics Generation (FREE)
- Instagram posts (1080×1080)
- Instagram stories (1080×1920)
- YouTube thumbnails (1280×720)
- Automatic branding with your logo/colors

### AI Image Generation ($0.07/image)
- Powered by Grok/xAI
- High-quality (1024×1024+)
- Generation time: ~15 seconds
- Use for: Social media, blog posts, ads

### Video Ad Creation ($0.34/video)
- Generates 4 AI images + stitches into video
- 15-second vertical format (perfect for Instagram/TikTok)
- Professional transitions and effects
- Total time: ~90 seconds

### Workout Plans (FREE)
- 3-6 day splits
- Customizable equipment (full gym, home gym, minimal)
- Experience levels (beginner, intermediate, advanced)
- Exports to PDF and JSON

### Nutrition Guides (FREE)
- TDEE-based macro calculations
- Meal timing recommendations
- Dietary preferences (flexible, vegan, keto, paleo)
- Exports to PDF and JSON

---

## 🎉 You're Ready!

**Congratulations!** Your Fitness Influencer AI is now personalized and ready to supercharge your content creation.

**Need help?** Contact support at: support@marceausolutions.com

---

**Last Updated:** January 6, 2026  
**Version:** 2.0 (Personalization System)  
**Created By:** Marceau Solutions