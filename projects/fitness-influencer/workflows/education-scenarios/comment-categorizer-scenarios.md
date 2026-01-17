# Education Scenarios: Comment Categorizer

*Tool: `categorize_comments`*
*Module: comment_categorizer.py*
*Category: 1 (FREE)*

## Persona

**Rachel B., Growing Fitness Influencer**
- Receives 200+ comments/DMs daily
- Struggles to identify collaboration opportunities
- Needs to filter spam and prioritize engagement
- Wants automated response suggestions

---

## Scenario 1: Mixed Comment Batch

**Goal:** Categorize a typical mix of comments

**Input:**
```python
{
    "comments": [
        "Love this workout! Been following you for 6 months 💪",
        "BUY FOLLOWERS NOW!! CLICK HERE www.spam.com",
        "Hey! Would love to collab on a fitness video. DM me!",
        "How many sets should I do for this exercise?",
        "This is terrible advice. You're going to hurt someone.",
        "Hi! I'm from FitBrand Co. We'd love to sponsor you."
    ],
    "include_auto_replies": True
}
```

**Expected Output:**
```json
{
    "results": [
        {"text": "Love this...", "category": "FAN_MESSAGE", "action": "engage", "auto_reply": "..."},
        {"text": "BUY FOLLOWERS...", "category": "SPAM", "action": "delete/block"},
        {"text": "Hey! Would love...", "category": "COLLAB_REQUEST", "action": "review"},
        {"text": "How many sets...", "category": "FAQ", "action": "respond", "auto_reply": "..."},
        {"text": "This is terrible...", "category": "NEGATIVE", "action": "review"},
        {"text": "Hi! I'm from...", "category": "BRAND_INQUIRY", "action": "prioritize"}
    ]
}
```

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.comment_categorizer import CommentCategorizer
cat = CommentCategorizer()
comments = [
    'Love this workout! 💪',
    'BUY FOLLOWERS NOW!! www.spam.com',
    'Would love to collab!',
    'How many sets for this?',
    'This is terrible advice',
    'Hi from FitBrand Co, want to sponsor you'
]
results = cat.categorize_batch(comments, include_auto_replies=True)
for r in results:
    print(f'{r[\"category\"]}: {r[\"text\"][:30]}...')
"
```

**Pass Criteria:**
- [ ] Correctly identifies SPAM
- [ ] Correctly identifies FAN_MESSAGE
- [ ] Correctly identifies COLLAB_REQUEST
- [ ] Correctly identifies FAQ
- [ ] Correctly identifies NEGATIVE
- [ ] Correctly identifies BRAND_INQUIRY

---

## Scenario 2: FAQ-Heavy Batch

**Goal:** Test handling of common questions

**Input:**
```python
{
    "comments": [
        "What time do you usually work out?",
        "How long did it take you to get those abs?",
        "What protein powder do you use?",
        "Do you have a workout plan I can follow?",
        "What's your diet like?"
    ],
    "include_auto_replies": True
}
```

**Expected Output:**
- All categorized as FAQ
- Auto-reply templates provided
- Relevant response suggestions

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.comment_categorizer import CommentCategorizer
cat = CommentCategorizer()
faq_comments = [
    'What time do you work out?',
    'How long for those abs?',
    'What protein powder?',
    'Do you have a workout plan?',
    'What\\'s your diet?'
]
results = cat.categorize_batch(faq_comments, include_auto_replies=True)
faq_count = sum(1 for r in results if r['category'] == 'FAQ')
print(f'FAQ identified: {faq_count}/{len(faq_comments)}')
for r in results:
    has_reply = bool(r.get('auto_reply'))
    print(f'  {r[\"category\"]}: {r[\"text\"][:20]}... (reply: {has_reply})')
"
```

**Pass Criteria:**
- [ ] All/most categorized as FAQ
- [ ] Auto-replies are relevant to questions
- [ ] No false spam positives

---

## Scenario 3: Spam Detection

**Goal:** Test spam filtering accuracy

**Input:**
```python
{
    "comments": [
        "🔥🔥🔥 GET FREE FOLLOWERS 🔥🔥🔥 Click my bio",
        "I made $5000 working from home! DM for info",
        "Check out my page for weight loss pills!!!",
        "www.scam-site.com/free-money",
        "Follow @spam_account for giveaway",
        "DM me for discount supplements 50% off!!!"
    ],
    "include_auto_replies": False
}
```

**Expected Output:**
- All categorized as SPAM
- Action: delete or block
- No auto-replies needed

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.comment_categorizer import CommentCategorizer
cat = CommentCategorizer()
spam_comments = [
    'GET FREE FOLLOWERS Click my bio',
    'I made \$5000 working from home!',
    'Check out my page for weight loss pills',
    'www.scam-site.com/free-money',
    'Follow @spam for giveaway'
]
results = cat.categorize_batch(spam_comments, include_auto_replies=False)
spam_count = sum(1 for r in results if r['category'] == 'SPAM')
print(f'Spam detected: {spam_count}/{len(spam_comments)}')
"
```

**Pass Criteria:**
- [ ] High spam detection rate (80%+)
- [ ] No false negatives on obvious spam
- [ ] Appropriate action suggestions

---

## Scenario 4: Brand Opportunities

**Goal:** Identify potential sponsorship opportunities

**Input:**
```python
{
    "comments": [
        "Hey! I work at Nike and we love your content. Can we chat?",
        "We're a new fitness app and would love to partner. Email me!",
        "Our supplement brand wants to send you free products to review",
        "I'm a talent manager looking for fitness influencers. Interested?"
    ],
    "include_auto_replies": True
}
```

**Expected Output:**
- Categorized as BRAND_INQUIRY or COLLAB_REQUEST
- Priority action: review/respond
- Professional response templates

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.comment_categorizer import CommentCategorizer
cat = CommentCategorizer()
brand_comments = [
    'I work at Nike, can we chat?',
    'New fitness app wants to partner',
    'Supplement brand - free products',
    'Talent manager looking for influencers'
]
results = cat.categorize_batch(brand_comments, include_auto_replies=True)
priority_count = sum(1 for r in results if r['category'] in ['BRAND_INQUIRY', 'COLLAB_REQUEST'])
print(f'Brand/Collab identified: {priority_count}/{len(brand_comments)}')
"
```

**Pass Criteria:**
- [ ] Identifies brand opportunities
- [ ] Distinguishes from spam (no false positives)
- [ ] Priority action assigned

---

## Scenario 5: Negative Feedback Handling

**Goal:** Test handling of criticism and negative comments

**Input:**
```python
{
    "comments": [
        "This form is dangerous and will cause injury",
        "You clearly don't know what you're talking about",
        "Unfollowing. Your content has gone downhill",
        "This is the worst advice I've ever seen",
        "Stop spreading misinformation"
    ],
    "include_auto_replies": True
}
```

**Expected Output:**
- Categorized as NEGATIVE
- Suggested action: review (not auto-reply)
- Flags for potential PR response

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.comment_categorizer import CommentCategorizer
cat = CommentCategorizer()
negative_comments = [
    'This form is dangerous',
    'You don\\'t know what you\\'re talking about',
    'Unfollowing, content went downhill',
    'Worst advice ever'
]
results = cat.categorize_batch(negative_comments, include_auto_replies=True)
negative_count = sum(1 for r in results if r['category'] == 'NEGATIVE')
print(f'Negative identified: {negative_count}/{len(negative_comments)}')
"
```

**Pass Criteria:**
- [ ] Identifies negative feedback
- [ ] Does NOT auto-reply to criticism
- [ ] Flags for human review

---

## Edge Case 1: Empty Comments Array

**Input:**
```python
{
    "comments": [],
    "include_auto_replies": True
}
```

**Pass Criteria:**
- [ ] Returns empty results (not error)
- [ ] Does not crash

---

## Edge Case 2: Single Comment

**Input:**
```python
{
    "comments": ["Great workout!"],
    "include_auto_replies": True
}
```

**Pass Criteria:**
- [ ] Works with single comment
- [ ] Returns properly formatted result

---

## Edge Case 3: Very Long Comment

**Input:**
```python
{
    "comments": ["A" * 10000],  # 10,000 characters
    "include_auto_replies": True
}
```

**Pass Criteria:**
- [ ] Does not crash
- [ ] Handles or truncates appropriately

---

## Edge Case 4: Non-English Comments

**Input:**
```python
{
    "comments": [
        "¡Me encanta tu entrenamiento!",
        "素晴らしいワークアウト！",
        "Отличная тренировка!"
    ]
}
```

**Pass Criteria:**
- [ ] Does not crash
- [ ] Attempts categorization or marks as OTHER

---

## Batch Test Script

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer

python -c "
from src.fitness_influencer_mcp.comment_categorizer import CommentCategorizer
cat = CommentCategorizer()

# Test mixed batch
mixed = [
    'Love this! 💪',
    'BUY NOW www.spam.com',
    'Can we collab?',
    'How many reps?',
    'Terrible advice',
    'Brand partnership inquiry'
]

print('Running comment categorizer scenarios...')
try:
    results = cat.categorize_batch(mixed, include_auto_replies=True)
    categories = [r['category'] for r in results]
    print(f'✅ Mixed batch: {len(results)} categorized')
    print(f'   Categories: {set(categories)}')
except Exception as e:
    print(f'❌ Mixed batch failed: {e}')

# Test empty
try:
    empty_results = cat.categorize_batch([], include_auto_replies=True)
    print(f'✅ Empty batch: {len(empty_results)} results (expected 0)')
except Exception as e:
    print(f'❌ Empty batch failed: {e}')

# Test single
try:
    single_results = cat.categorize_batch(['Great workout!'], include_auto_replies=True)
    print(f'✅ Single comment: {single_results[0][\"category\"]}')
except Exception as e:
    print(f'❌ Single comment failed: {e}')

print('Done!')
"
```

---

## Success Criteria Summary

| Scenario | Input Type | Key Check |
|----------|------------|-----------|
| Mixed batch | Various | Correct categories |
| FAQ batch | Questions | Auto-replies provided |
| Spam batch | Spam | High detection rate |
| Brand batch | Opportunities | Not marked as spam |
| Negative batch | Criticism | Flagged for review |
| Edge: Empty | [] | No crash |
| Edge: Single | 1 comment | Works |
| Edge: Long | 10K chars | Handles gracefully |
| Edge: Non-English | Other langs | No crash |
