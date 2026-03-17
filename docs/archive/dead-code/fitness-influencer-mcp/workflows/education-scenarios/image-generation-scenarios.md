# Education Scenarios: AI Image Generation

*Tool: `generate_fitness_image`*
*Module: grok_image_gen.py*
*Category: 2 (Requires XAI_API_KEY)*

## Persona

**Emma S., Social Media Manager for Fitness Brand**
- Needs daily motivational images for social posts
- Requires custom thumbnails for YouTube videos
- Creates promotional graphics for fitness programs
- Budget-conscious ($0.07/image)

---

## Prerequisites

### Required: XAI API Key
```bash
# Check if key is set
echo $XAI_API_KEY

# Or in .env file
grep XAI_API_KEY .env
```

### Cost Awareness
- **$0.07 per image generated**
- Test scenarios should use minimal image count
- Consider dry-run testing where possible

---

## Scenario 1: Motivational Quote Image

**Goal:** Generate a motivational fitness image for Instagram

**Input:**
```python
{
    "prompt": "Fit athletic person doing push-ups at sunrise on a beach, motivational, inspiring, high energy",
    "count": 1,
    "output_path": None  # Returns URL
}
```

**Expected Output:**
- Single image URL
- Fitness-appropriate content
- High quality, usable for social media

**Test Command (Dry Run - No API Call):**
```bash
python -c "
import os
from src.grok_image_gen import GrokImageGenerator

if not os.getenv('XAI_API_KEY'):
    print('⚠️ SKIPPED: XAI_API_KEY not set')
    print('Set with: export XAI_API_KEY=your_key')
else:
    gen = GrokImageGenerator()
    print('✅ GrokImageGenerator initialized')
    print('API key present: Yes')
    print('Ready for image generation')
"
```

**Full Test (Uses API - $0.07):**
```bash
python -c "
import os
from src.grok_image_gen import GrokImageGenerator

if not os.getenv('XAI_API_KEY'):
    print('SKIPPED: No API key')
else:
    gen = GrokImageGenerator()
    result = gen.generate_image(
        'Fit person doing yoga at sunset, peaceful, healthy lifestyle',
        count=1
    )
    print('Generated:', len(result), 'image(s)')
    print('URL:', result[0] if result else 'None')
    print('Cost: \$0.07')
"
```

**Pass Criteria:**
- [ ] Generator initializes with API key
- [ ] Returns valid image URL(s)
- [ ] Image matches prompt theme

---

## Scenario 2: YouTube Thumbnail

**Goal:** Generate a clickable thumbnail for fitness video

**Input:**
```python
{
    "prompt": "Muscular person flexing biceps, dramatic lighting, text space on left side, YouTube thumbnail style, vibrant colors",
    "count": 1,
    "output_path": "/tmp/thumbnail.jpg"
}
```

**Expected Output:**
- Image saved to specified path
- Thumbnail-appropriate composition
- Space for text overlay

**Pass Criteria:**
- [ ] Image saved to output path
- [ ] File is valid image format
- [ ] Composition suits thumbnail use

---

## Scenario 3: Multiple Image Options

**Goal:** Generate multiple images to choose from

**Input:**
```python
{
    "prompt": "Athletic woman doing deadlift in modern gym, professional photography",
    "count": 3
}
```

**Expected Output:**
- 3 image URLs
- Variations on same theme
- Cost: $0.21 (3 × $0.07)

**Pass Criteria:**
- [ ] Returns exactly 3 images
- [ ] Each image is unique
- [ ] All match prompt theme

---

## Scenario 4: Before/After Transformation

**Goal:** Generate transformation-style image

**Input:**
```python
{
    "prompt": "Split image showing fitness transformation, before and after, dramatic change, inspiring results",
    "count": 1
}
```

**Expected Output:**
- Single transformation-style image
- Clear visual contrast

**Pass Criteria:**
- [ ] Image shows transformation concept
- [ ] Suitable for motivational content

---

## Scenario 5: Product/Equipment Focus

**Goal:** Generate image featuring fitness equipment

**Input:**
```python
{
    "prompt": "High-end home gym equipment, dumbbells, resistance bands, yoga mat, clean aesthetic, product photography",
    "count": 1
}
```

**Pass Criteria:**
- [ ] Equipment clearly visible
- [ ] Professional product shot style

---

## Edge Cases

### Edge Case 1: Missing API Key

**Test Command:**
```bash
python -c "
import os
# Temporarily unset key
original = os.environ.pop('XAI_API_KEY', None)

from src.grok_image_gen import GrokImageGenerator
try:
    gen = GrokImageGenerator()
    result = gen.generate_image('Test prompt', count=1)
    print('Result without key:', result)
except Exception as e:
    print('Error handled:', type(e).__name__)
finally:
    if original:
        os.environ['XAI_API_KEY'] = original
"
```

**Pass Criteria:**
- [ ] Does not crash without API key
- [ ] Clear error message about missing key

---

### Edge Case 2: Invalid Prompt (Empty)

**Input:**
```python
{
    "prompt": "",
    "count": 1
}
```

**Pass Criteria:**
- [ ] Rejects empty prompt
- [ ] Helpful error message

---

### Edge Case 3: High Count Request

**Input:**
```python
{
    "prompt": "Fitness image",
    "count": 10  # Maximum or beyond
}
```

**Pass Criteria:**
- [ ] Either generates 10 or caps at maximum
- [ ] Clear feedback on limits
- [ ] Cost warning: $0.70

---

### Edge Case 4: Inappropriate Content Request

**Input:**
```python
{
    "prompt": "[Inappropriate content request]"
}
```

**Expected Output:**
- API should reject inappropriate requests
- Graceful error handling

**Pass Criteria:**
- [ ] Inappropriate content blocked
- [ ] No crash

---

## Cost Tracking Test

**Goal:** Verify cost tracking works

**Test Command:**
```bash
python -c "
import os
from src.grok_image_gen import GrokImageGenerator

if not os.getenv('XAI_API_KEY'):
    print('SKIPPED: No API key')
else:
    gen = GrokImageGenerator()
    # Check usage tracking
    usage = gen.get_usage_summary()
    print('Usage tracking available:', bool(usage))
    print('Current usage:', usage)
"
```

**Pass Criteria:**
- [ ] Usage tracking method exists
- [ ] Returns cost information
- [ ] Tracks total spend

---

## Batch Test Script (Initialization Only)

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer

python -c "
import os
print('Testing AI Image Generation...')
print('=' * 50)

# Test 1: Check API key
api_key = os.getenv('XAI_API_KEY')
if api_key:
    print(f'✅ XAI_API_KEY is set ({len(api_key)} chars)')
else:
    print('❌ XAI_API_KEY not set')
    print('   Set with: export XAI_API_KEY=your_key')
    print('   Or add to .env file')

# Test 2: Import module
try:
    from src.grok_image_gen import GrokImageGenerator
    print('✅ GrokImageGenerator imported')
except Exception as e:
    print(f'❌ Import failed: {e}')

# Test 3: Initialize (may fail without key)
if api_key:
    try:
        gen = GrokImageGenerator()
        print('✅ Generator initialized')

        # Test 4: Check methods
        methods = ['generate_image', 'get_usage_summary']
        for method in methods:
            has_method = hasattr(gen, method)
            status = '✅' if has_method else '❌'
            print(f'{status} Method: {method}')
    except Exception as e:
        print(f'❌ Initialization failed: {e}')
else:
    print('⚠️ Skipping initialization (no API key)')

print('=' * 50)
print('Note: Actual image generation costs \$0.07 per image')
print('Full testing requires XAI_API_KEY')
"
```

---

## Success Criteria Summary

| Scenario | Count | Cost | Key Check |
|----------|-------|------|-----------|
| Motivational image | 1 | $0.07 | Valid URL returned |
| YouTube thumbnail | 1 | $0.07 | Saved to path |
| Multiple options | 3 | $0.21 | 3 unique images |
| Transformation | 1 | $0.07 | Theme matches |
| Equipment focus | 1 | $0.07 | Professional style |
| Edge: No API key | 0 | $0 | Error handled |
| Edge: Empty prompt | 0 | $0 | Rejected |
| Edge: High count | 10 | $0.70 | Capped or allowed |
| Edge: Inappropriate | 0 | $0 | Blocked |

---

## Cost Management Recommendations

1. **Development Testing**: Use minimal count (1)
2. **Production**: Implement daily/monthly limits
3. **Tracking**: Monitor usage via get_usage_summary()
4. **Budget Alert**: Set threshold at $10/day

## API Key Setup

```bash
# Option 1: Environment variable
export XAI_API_KEY=xai-your-api-key-here

# Option 2: .env file
echo "XAI_API_KEY=xai-your-api-key-here" >> .env

# Verify
python -c "import os; print('Key set:', bool(os.getenv('XAI_API_KEY')))"
```
