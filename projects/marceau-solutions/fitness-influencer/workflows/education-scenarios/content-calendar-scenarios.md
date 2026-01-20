# Education Scenarios: Content Calendar Generator

*Tool: `generate_content_calendar`*
*Module: content_calendar.py*
*Category: 1 (FREE)*

## Persona

**Jessica T., Multi-Platform Fitness Influencer**
- Posts to Instagram, TikTok, and YouTube
- Struggles with burnout from constant content creation
- Needs balanced scheduling to maintain consistency
- Wants to plan 2-4 weeks ahead

---

## Scenario 1: Standard 7-Day Calendar

**Goal:** Create a one-week content plan with moderate posting frequency

**Input:**
```python
{
    "days": 7,
    "posts_per_day": 2,
    "platforms": ["instagram", "tiktok"],
    "content_focus": ["workout", "nutrition"],
    "rest_days": ["Sunday"]
}
```

**Expected Output:**
- 6 posting days (Sunday rest)
- ~12 posts total
- Mix of workout and nutrition content
- Balanced platform distribution
- Effort levels varied (not all high-effort)

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.content_calendar import ContentCalendarGenerator
gen = ContentCalendarGenerator()
cal = gen.generate_calendar(
    days=7,
    posts_per_day=2,
    platforms=['instagram', 'tiktok'],
    content_focus=['workout', 'nutrition'],
    rest_days=['Sunday']
)
print('Days in calendar:', len(cal.get('days', [])))
total_posts = sum(len(d.get('posts', [])) for d in cal.get('days', []))
print('Total posts:', total_posts)
print('Workload assessment:', cal.get('workload_assessment', 'N/A'))
"
```

**Pass Criteria:**
- [ ] Returns 7 days
- [ ] Sunday has no posts (rest day)
- [ ] Approximately 12 posts total
- [ ] Posts balanced between platforms
- [ ] Content types match focus areas

---

## Scenario 2: Heavy Posting Schedule (4 posts/day)

**Goal:** Test high-volume content calendar for aggressive growth

**Input:**
```python
{
    "days": 14,
    "posts_per_day": 4,
    "platforms": ["instagram", "tiktok", "youtube"],
    "content_focus": ["workout", "motivation", "lifestyle"],
    "rest_days": []  # No rest
}
```

**Expected Output:**
- 14 days of content
- ~56 posts
- Warning about potential burnout
- Mix of effort levels (can't all be high)
- Recommendations for sustainability

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.content_calendar import ContentCalendarGenerator
gen = ContentCalendarGenerator()
cal = gen.generate_calendar(
    days=14,
    posts_per_day=4,
    platforms=['instagram', 'tiktok', 'youtube']
)
total_posts = sum(len(d.get('posts', [])) for d in cal.get('days', []))
print('Total posts:', total_posts)
print('Workload:', cal.get('workload_assessment', 'N/A'))
print('Has warnings:', 'warning' in str(cal).lower())
"
```

**Pass Criteria:**
- [ ] Returns 14 days
- [ ] High volume but includes low-effort posts
- [ ] Workload assessment reflects heavy schedule
- [ ] Mix of effort levels for sustainability

---

## Scenario 3: Minimal Posting (1 post/day)

**Goal:** Create sustainable low-volume calendar for beginners

**Input:**
```python
{
    "days": 30,
    "posts_per_day": 1,
    "platforms": ["instagram"],
    "content_focus": ["workout", "education"],
    "rest_days": ["Saturday", "Sunday"]
}
```

**Expected Output:**
- 30 days planned
- ~22 posts (weekends off)
- All content focused on Instagram
- Beginner-friendly workload

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.content_calendar import ContentCalendarGenerator
gen = ContentCalendarGenerator()
cal = gen.generate_calendar(
    days=30,
    posts_per_day=1,
    platforms=['instagram'],
    content_focus=['workout', 'education'],
    rest_days=['Saturday', 'Sunday']
)
active_days = [d for d in cal.get('days', []) if d.get('posts')]
print('Active posting days:', len(active_days))
print('Rest days:', 30 - len(active_days))
"
```

**Pass Criteria:**
- [ ] Returns 30 days
- [ ] Saturdays and Sundays have no posts
- [ ] Approximately 22 posts (weekdays only)
- [ ] Workload assessment is sustainable

---

## Scenario 4: Full Platform Coverage

**Goal:** Test calendar with all supported platforms

**Input:**
```python
{
    "days": 7,
    "posts_per_day": 3,
    "platforms": ["instagram", "tiktok", "youtube", "twitter", "threads", "linkedin"]
}
```

**Expected Output:**
- Posts distributed across all platforms
- Platform-appropriate content suggestions
- No platform gets all the posts

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.content_calendar import ContentCalendarGenerator
gen = ContentCalendarGenerator()
cal = gen.generate_calendar(
    days=7,
    posts_per_day=3,
    platforms=['instagram', 'tiktok', 'youtube', 'twitter', 'threads', 'linkedin']
)
platforms_used = set()
for day in cal.get('days', []):
    for post in day.get('posts', []):
        platforms_used.add(post.get('platform'))
print('Platforms covered:', platforms_used)
print('Platform count:', len(platforms_used))
"
```

**Pass Criteria:**
- [ ] Multiple platforms receive posts
- [ ] Distribution is reasonable (not all to one platform)

---

## Scenario 5: Content Focus Specialization

**Goal:** Test specific content focus areas

**Input:**
```python
{
    "days": 7,
    "posts_per_day": 2,
    "content_focus": ["nutrition", "motivation"]  # No workout
}
```

**Expected Output:**
- Posts focused on nutrition and motivation
- No workout-specific content
- Categories match request

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.content_calendar import ContentCalendarGenerator
gen = ContentCalendarGenerator()
cal = gen.generate_calendar(
    days=7,
    posts_per_day=2,
    content_focus=['nutrition', 'motivation']
)
categories = []
for day in cal.get('days', []):
    for post in day.get('posts', []):
        categories.append(post.get('category', post.get('type', 'unknown')))
print('Categories found:', set(categories))
"
```

**Pass Criteria:**
- [ ] Content matches focus areas
- [ ] No off-topic content

---

## Edge Case 1: Single Day Calendar

**Input:**
```python
{
    "days": 1,
    "posts_per_day": 2
}
```

**Pass Criteria:**
- [ ] Returns 1 day
- [ ] 2 posts planned
- [ ] Valid structure

---

## Edge Case 2: All Rest Days

**Input:**
```python
{
    "days": 7,
    "posts_per_day": 2,
    "rest_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
}
```

**Expected Output:**
- Either error/warning OR returns calendar with 0 posts

**Test Command:**
```bash
python -c "
from src.fitness_influencer_mcp.content_calendar import ContentCalendarGenerator
gen = ContentCalendarGenerator()
cal = gen.generate_calendar(
    days=7,
    posts_per_day=2,
    rest_days=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
)
total_posts = sum(len(d.get('posts', [])) for d in cal.get('days', []))
print('Total posts (should be 0 or warning):', total_posts)
"
```

**Pass Criteria:**
- [ ] Does not crash
- [ ] Either returns empty calendar or provides helpful feedback

---

## Edge Case 3: No Platforms Specified

**Input:**
```python
{
    "days": 7,
    "posts_per_day": 2,
    "platforms": None  # Should default to all
}
```

**Pass Criteria:**
- [ ] Defaults to reasonable platform set
- [ ] Does not crash

---

## Batch Test Script

```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer

python -c "
from src.fitness_influencer_mcp.content_calendar import ContentCalendarGenerator
gen = ContentCalendarGenerator()

scenarios = [
    {'days': 7, 'posts_per_day': 2, 'rest_days': ['Sunday']},
    {'days': 14, 'posts_per_day': 4},
    {'days': 30, 'posts_per_day': 1, 'rest_days': ['Saturday', 'Sunday']},
    {'days': 7, 'posts_per_day': 3, 'platforms': ['instagram', 'tiktok', 'youtube']},
    {'days': 1, 'posts_per_day': 2},
]

print('Running content calendar scenarios...')
for i, params in enumerate(scenarios, 1):
    try:
        cal = gen.generate_calendar(**params)
        days = len(cal.get('days', []))
        posts = sum(len(d.get('posts', [])) for d in cal.get('days', []))
        status = '✅' if days == params['days'] else '❌'
        print(f'{status} Scenario {i}: {days} days, {posts} posts')
    except Exception as e:
        print(f'❌ Scenario {i} - Error: {e}')
print('Done!')
"
```

---

## Success Criteria Summary

| Scenario | Days | Posts/Day | Key Check |
|----------|------|-----------|-----------|
| Standard week | 7 | 2 | Sunday rest works |
| Heavy schedule | 14 | 4 | Burnout warning |
| Minimal posting | 30 | 1 | Weekend rest |
| All platforms | 7 | 3 | Platform distribution |
| Focus areas | 7 | 2 | Category matching |
| Edge: 1 day | 1 | 2 | Valid structure |
| Edge: All rest | 7 | 2 | No crash |
| Edge: No platforms | 7 | 2 | Defaults work |
