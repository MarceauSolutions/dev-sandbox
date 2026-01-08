# Interactive PowerPoint Editing Workflow

## Goal
Allow users to make iterative edits to generated PowerPoint presentations through natural language chat commands. Edit text, replace images, update titles, and regenerate AI images without leaving the conversation.

## When to Use
After generating an interview prep PowerPoint (or any presentation), the user wants to:
- Change wording on a specific slide
- Replace or regenerate an image
- Update a slide title
- Add a new image to a slide
- Fine-tune the presentation content

## Tools/Scripts

### PowerPoint Editor
`execution/pptx_editor.py` - Interactive presentation editor

**Capabilities:**
- List all slides with content summary
- Inspect detailed slide content
- Edit/replace text on slides
- Replace images with local files
- Regenerate images with new AI prompts
- Update slide titles
- Add new images to slides

## Chat Interaction Patterns

### 1. User Wants to See What's in the Presentation

**User says:** "What slides are in the presentation?" or "Show me the slides"

**Action:** Run list command
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action list
```

### 2. User Wants to See a Specific Slide

**User says:** "What's on slide 5?" or "Show me slide 14"

**Action:** Run inspect command
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action inspect --slide 5
```

### 3. User Wants to Edit Text

**User says:** "Change 'old text' to 'new text' on slide 3" or "On slide 7, replace 'wrong word' with 'correct word'"

**Action:** Run edit-text command
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action edit-text --slide 3 --find "old text" --replace "new text"
```

**For all occurrences:**
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action edit-text --slide 3 --find "old text" --replace "new text" --match-all
```

### 4. User Wants to Change an Image

**User says:** "Replace the image on slide 14 with a photo of a particle accelerator" or "Change the image on experience slide 1"

**Two options:**

**Option A - Regenerate with AI (costs $0.07):**
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action regenerate-image --slide 14 --prompt "Technical photo of particle accelerator beamline with superconducting magnets"
```

**Option B - Replace with local file (free):**
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action replace-image --slide 14 --image-index 0 --new-image /path/to/new-image.jpg
```

### 5. User Wants to Update a Slide Title

**User says:** "Change the title on slide 6 to 'My Engineering Background'"

**Action:** Run update-title command
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action update-title --slide 6 --title "My Engineering Background"
```

### 6. User Wants to Add a New Image

**User says:** "Add an image to slide 5" or "Put this photo on slide 3"

**Action:** Run add-image command
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action add-image --slide 5 --new-image /path/to/image.jpg --position left --width 5
```

**Position options:** `left`, `right`, `center`, or `"x,y"` in inches (e.g., `"2.5,3.0"`)

### 7. User Wants to Add a NEW SLIDE with Their Own Image

**User says:** "Add a slide for my fuel cap design using this image" or "Create a new experience slide with my photo"

**Two options:**

**Option A - With user's own image (FREE):**
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action add-slide \
  --title "Aircraft Fuel Cap Design" \
  --description "Designed gravity-fill fuel caps for general aviation with safety compliance." \
  --relevance "Precision mechanical design for safety-critical aerospace components." \
  --new-image ~/Downloads/my_fuel_cap_photo.jpg \
  --after-slide 18 --open
```

**Option B - With AI-generated image ($0.07):**
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action add-slide \
  --title "Aircraft Fuel Cap Design" \
  --description "Designed gravity-fill fuel caps for general aviation with safety compliance." \
  --relevance "Precision mechanical design for safety-critical aerospace components." \
  --prompt "Technical product photography of aircraft gravity-fill fuel cap, aluminum aviation component" \
  --after-slide 18 --open
```

**Key difference:** Use `--new-image` for your own photo (free), or `--prompt` for AI generation ($0.07)

## Common Edit Scenarios

### Scenario 1: User Doesn't Like an Experience Image

**User:** "The image on the VTOL slide doesn't look right. Can you make it more technical?"

**Response:**
1. First identify which slide (list slides if needed)
2. Regenerate the image with a better prompt

```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action regenerate-image --slide 15 --prompt "Technical cutaway diagram of electric VTOL aircraft showing propulsion motors, battery systems, and tilt-rotor mechanism. Engineering schematic style, detailed mechanical components visible."
```

### Scenario 2: User Wants to Correct a Typo

**User:** "On slide 8, 'aerosapce' should be 'aerospace'"

**Response:**
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action edit-text --slide 8 --find "aerosapce" --replace "aerospace"
```

### Scenario 3: User Wants More Specific Content

**User:** "The talking points slide should mention 'precision tolerance of 0.0001 inches' instead of just 'precision'"

**Response:**
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action edit-text --slide 12 --find "precision" --replace "precision tolerance of 0.0001 inches"
```

### Scenario 4: User Wants to Replace Image with Their Own

**User:** "I have a better photo of the actual oxygen system I designed. Can you use this instead?" (with file path)

**Response:**
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action replace-image --slide 14 --image-index 0 --new-image ~/Documents/aerox_oxygen_system.jpg
```

### Scenario 5: User Wants to Add a New Slide with Their Own Photo

**User:** "Add a slide about my EV charger work. Here's a photo: ~/Downloads/ev_charger.jpg"

**Response:**
1. Identify where to insert (after last experience slide)
2. Create slide with user's image

```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action add-slide \
  --title "Electric Vehicle Charging Systems" \
  --description "Designed Level 1 and Level 2 EVSE charging equipment for residential and commercial applications with integrated safety features." \
  --relevance "Experience with high-voltage power systems and thermal management translates to power distribution systems in scientific facilities." \
  --new-image ~/Downloads/ev_charger.jpg \
  --after-slide 18 --open
```

### Scenario 6: User Provides Image Path in Chat

**User:** "Use this image /Users/me/Photos/project.jpg to add a slide about my mechanical design work"

**Response:**
```bash
python execution/pptx_editor.py --input .tmp/interview_prep_brookhaven_national_laboratory.pptx --action add-slide \
  --title "Precision Mechanical Design" \
  --description "[Ask user for description or infer from context]" \
  --relevance "[Relate to target role requirements]" \
  --new-image /Users/me/Photos/project.jpg \
  --after-slide 18 --open
```

## Workflow Integration

After making edits, always:
1. Confirm the changes were saved
2. Offer to open the updated presentation
3. Ask if they need any other modifications

```bash
# Open the updated presentation
open .tmp/interview_prep_brookhaven_national_laboratory.pptx
```

## Image Generation Prompts for Technical Content

When regenerating images for technical/engineering presentations, use prompts like:

**For Aerospace/Aviation:**
- "Technical CAD rendering of [specific component], detailed engineering visualization, cutaway view showing internal mechanisms"
- "Product photography of [aerospace equipment], studio lighting, technical documentation style"

**For Scientific Equipment:**
- "Laboratory equipment photograph showing [instrument type], clean technical setup, scientific visualization"
- "Particle accelerator beamline with superconducting magnets, technical facility photo"

**For Engineering Drawings:**
- "Engineering blueprint with GD&T callouts per ASME Y14.5, technical drawing style, datum references and tolerances visible"
- "Exploded assembly view diagram showing [component], mechanical engineering documentation"

**For EV/Clean Energy:**
- "Electric vehicle charging infrastructure, DC fast charger station, commercial installation"
- "Battery management system technical diagram, power electronics visualization"

## Cost

| Action | Cost |
|--------|------|
| Text edits | FREE |
| Title updates | FREE |
| Replace image with local file | FREE |
| Add slide with user's own image | FREE |
| AI image regeneration | $0.07 per image |
| Add slide with AI-generated image | $0.07 per image |

## Output

All edits save to the same file by default. To save as a new file:
```bash
python execution/pptx_editor.py --input original.pptx --action edit-text --slide 3 --find "old" --replace "new" --output edited_version.pptx
```
