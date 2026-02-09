# Personal Training Business

William's personal training business that **uses** the fitness-influencer tool as a customer.

## Architecture

```
fitness-influencer/ = The PRODUCT (SaaS tool sold to trainers)
personal-training-business/ = William's BUSINESS (first customer of the product)
```

This is the **customer-side** operations:
- Client management
- Content library
- Workout programs
- Business workflows/SOPs

The product (fitness-influencer) provides the **tools**:
- Video editing automation
- Content generation
- Gamification dashboard
- Social media scheduling

## Folder Structure

```
personal-training-business/
├── clients/          # Client management
│   ├── active/       # Current clients
│   └── prospects/    # Lead tracking
├── content/          # William's content library
│   ├── videos/       # Raw and edited videos
│   ├── graphics/     # Images and graphics
│   └── posts/        # Written content
├── programs/         # Workout programs
│   ├── templates/    # Program templates
│   └── custom/       # Client-specific programs
└── workflows/        # Business SOPs
    ├── onboarding.md # New client onboarding
    ├── content.md    # Content creation workflow
    └── scheduling.md # Session scheduling
```

## Related Resources

- **Product Dashboard**: Access gamification at `http://localhost:8000/gamification`
- **Fitness Influencer Tool**: `projects/marceau-solutions/fitness-influencer/`
- **Build-in-Public Content**: `projects/shared/social-media-automation/templates/build-in-public-content.json`

## Getting Started

1. **Access the product tools**:
   ```bash
   cd projects/marceau-solutions/fitness-influencer
   uvicorn backend.main:app --reload --port 8000
   ```

2. **Use gamification dashboard**:
   - Open browser to `http://localhost:8000/gamification`
   - Log daily actions (posts, comments, clients signed)
   - Track XP, streaks, and achievements

3. **X Social Automation**:
   - Workflow active on EC2 n8n: `X-Social-Post-Scheduler`
   - Content queue at: `projects/shared/social-media-automation/`

## Tenant ID

William's data in the fitness-influencer product uses tenant ID: `wmarceau`
