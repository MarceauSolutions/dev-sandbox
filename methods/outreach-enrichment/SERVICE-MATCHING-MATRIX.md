# Service Matching Matrix

*Created: 2026-01-18*

## Business Type → Service Mapping

| Business Type | Primary Service | Secondary Services | Pain Points to Mention |
|--------------|-----------------|--------------------|-----------------------|
| **Restaurant** | AI Customer Service | Voice AI, Booking | Phone volume, order taking, reservations |
| **Gym/Fitness Studio** | Fitness Content Automation | Voice AI, Booking | Content creation, class scheduling, member engagement |
| **Fitness Influencer** | Fitness Content Automation | Content Editing | Video editing time, consistency, engagement |
| **Personal Trainer** | Fitness Content Automation | Booking, CRM | Client booking, content, follow-ups |
| **Retail Store** | AI Customer Service | Inventory, Voice AI | Customer inquiries, product questions |
| **Medical/Dental** | Voice AI | Booking | Appointment scheduling, patient inquiries |
| **Law Office** | Voice AI | CRM | Intake calls, scheduling |
| **Real Estate** | Voice AI | CRM | Lead qualification, showing scheduling |
| **Salon/Spa** | Voice AI | Booking | Appointment booking, service questions |
| **Auto Shop** | Voice AI | Customer Service | Appointment scheduling, status updates |
| **HVAC/Plumbing** | Voice AI | Dispatch | Service calls, scheduling |
| **General B2B** | Business Automation | Custom | Workflow efficiency, data processing |

## Service Catalog

### 1. AI Customer Service
**Best for**: High phone volume businesses (restaurants, retail)
**Value prop**: "Answer every call, take orders 24/7, never miss a customer"
**Price range**: $149-399/month

### 2. Voice AI Agents
**Best for**: Appointment-based businesses
**Value prop**: "Automated scheduling, intake, and follow-up calls"
**Price range**: $199-499/month

### 3. Fitness Content Automation
**Best for**: Gyms, trainers, fitness influencers
**Value prop**: "Automated video editing, captions, posting schedule"
**Price range**: $99-299/month

### 4. Business Automation
**Best for**: Any business with repetitive workflows
**Value prop**: "Custom AI solutions for your specific processes"
**Price range**: $500-2000/month (custom)

## Matching Algorithm

```python
def match_service(business_type: str, signals: dict) -> str:
    """
    Match business to best service offering.

    Signals:
    - has_high_phone_volume: bool
    - has_appointments: bool
    - creates_content: bool
    - has_repetitive_workflows: bool
    """

    # Primary matches by business type
    type_map = {
        "restaurant": "ai_customer_service",
        "gym": "fitness_content_automation",
        "fitness_studio": "fitness_content_automation",
        "fitness_influencer": "fitness_content_automation",
        "personal_trainer": "fitness_content_automation",
        "retail": "ai_customer_service",
        "medical": "voice_ai",
        "dental": "voice_ai",
        "law": "voice_ai",
        "real_estate": "voice_ai",
        "salon": "voice_ai",
        "spa": "voice_ai",
        "auto": "voice_ai",
        "hvac": "voice_ai",
        "plumbing": "voice_ai",
    }

    # Check signals for override
    if signals.get("creates_content") and business_type in ["gym", "fitness", "trainer"]:
        return "fitness_content_automation"

    if signals.get("has_high_phone_volume"):
        return "ai_customer_service"

    if signals.get("has_appointments"):
        return "voice_ai"

    # Default to type map or general automation
    return type_map.get(business_type, "business_automation")
```

## Pain Point Scripts

### Restaurant Pain Points
- "Are you having trouble keeping up with phone orders?"
- "How much time do you spend answering the same questions?"
- "Do you ever miss calls during the rush?"

### Fitness Pain Points
- "How much time do you spend editing workout videos?"
- "Is it hard to stay consistent with content?"
- "Do you wish you could post more without spending hours editing?"

### Appointment Business Pain Points
- "How many calls do you miss while with clients?"
- "Is scheduling back-and-forth eating up your time?"
- "Would automated reminders help reduce no-shows?"

## Personalization Variables

| Variable | Source | Example |
|----------|--------|---------|
| `{business_name}` | Enrichment | "Boab Fit" |
| `{business_type}` | Classification | "fitness" |
| `{owner_name}` | Enrichment (optional) | "Sarah" |
| `{pain_point}` | Service matrix | "content creation" |
| `{service_name}` | Matching | "Fitness Content Automation" |
| `{value_prop}` | Service catalog | "automated video editing" |
| `{city}` | Enrichment | "Naples" |
