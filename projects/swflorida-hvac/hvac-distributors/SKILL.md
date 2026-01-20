# HVAC Distributor RFQ Skill

Submit RFQs (Request for Quote) to HVAC equipment distributors and compare quotes to find the best deals for your contracting business.

## What This Skill Does

This skill helps HVAC contractors:
- **Submit RFQs** to multiple equipment distributors at once
- **Track RFQ status** and wait for distributor responses
- **Get quotes** from distributors as they come in
- **Compare quotes** by price, delivery time, and total value
- **Find the best deal** with automated analysis

## When to Use This Skill

Use this skill when you need to:
- Source HVAC equipment for a job (AC units, furnaces, heat pumps, etc.)
- Get competitive pricing from multiple distributors
- Compare quotes on price, availability, and lead time
- Find equipment availability in your region
- Track outstanding RFQs and their status

## Example Prompts

### Submitting RFQs
- "I need a 3-ton AC unit delivered to Naples, FL"
- "Submit an RFQ for a Carrier 16 SEER heat pump"
- "Get quotes for a commercial rooftop unit, 5-ton"
- "I need pricing on 2 furnaces for delivery to Fort Myers"

### Checking Status
- "What's the status of my RFQ?"
- "Check if any quotes have come in"
- "How many distributors responded to my last RFQ?"

### Comparing Quotes
- "Compare the quotes I received"
- "Which distributor has the best price?"
- "Find me the fastest delivery option"
- "Show me a comparison of all quotes"

### Equipment Types
- "Submit RFQ for ac_unit" - Air conditioning units
- "Submit RFQ for furnace" - Gas/electric furnaces
- "Submit RFQ for heat_pump" - Heat pump systems
- "Submit RFQ for rooftop_unit" - Commercial rooftop units
- "Submit RFQ for mini_split" - Ductless mini-split systems
- "Submit RFQ for boiler" - Hot water boilers
- "Submit RFQ for chiller" - Commercial chillers
- "Submit RFQ for air_handler" - Air handling units

## How It Works

### 1. Submit RFQ
**Input**: Equipment type, delivery address, specifications
**Process**:
- Finds distributors in your region
- Matches distributors to your brand preferences
- Sends RFQ via email to up to 3 distributors
- Returns RFQ tracking IDs

**Example**:
```
Submit RFQ:
- Equipment: 3-ton AC unit, 16 SEER
- Brand preference: Carrier
- Delivery: 123 Main St, Naples, FL 34102
- Need by: 2026-01-20
```

### 2. Track Status
**Input**: RFQ ID
**Process**:
- Checks if RFQ was sent
- Monitors for incoming quotes
- Reports time elapsed and expiration

**Output**: Status (pending, sent, quoted, expired)

### 3. Get Quotes
**Input**: RFQ ID
**Process**:
- Retrieves all quotes for the RFQ
- Shows pricing, availability, lead times
- Calculates total cost including shipping

### 4. Compare Quotes
**Input**: One or more RFQ IDs
**Process**:
- Aggregates all quotes
- Ranks by price, lead time, or total value
- Identifies best option in each category

**Output**: Comparison with recommendations

## Supported Distributors

The system connects with regional distributors including:
- **Ferguson HVAC** - Southeast US, all major brands
- **Johnstone Supply** - National, Carrier, Lennox focus
- **?"RE/MAX HVAC** - FL focus, Trane specialist
- **Baker Distributing** - Southeast, multi-brand
- **Gemaire Distributors** - FL, Rheem/Ruud focus
- And others...

## Specifications You Can Include

When submitting an RFQ, you can specify:

| Spec | Example Values | Notes |
|------|----------------|-------|
| `tonnage` | 2, 3, 4, 5 | AC/heat pump size |
| `seer` | 14, 16, 18, 20 | Efficiency rating |
| `btu` | 80000, 100000 | Heating capacity |
| `voltage` | "208-230V", "460V" | Electrical requirements |
| `refrigerant` | "R-410A", "R-32" | Refrigerant type |
| `brand_preference` | "Carrier", "Trane" | Preferred manufacturer |
| `quantity` | 1, 2, 5 | Number of units |
| `needed_by_date` | "2026-01-20" | Delivery deadline |

## Response Times

HVAC distributor quotes typically arrive within:
- **Same-day**: 4-8 hours for in-stock items
- **Standard**: 24-48 hours for most requests
- **Custom/special order**: 3-5 business days

The system is designed for these async workflows - check back after 24 hours for best results.

## What You'll Get

### Quote Details
- Unit price per item
- Quantity available
- Lead time in days
- Shipping cost
- Total price
- Quote validity period

### Comparison Analysis
- Best price option
- Fastest delivery option
- Best overall value
- Side-by-side comparison table

### Recommendations
- Clear "best choice" with rationale
- Trade-off analysis (price vs speed)
- Alternative options

## Tips for Best Results

### Getting Competitive Quotes
1. **Include specifications**: More detail = better quotes
2. **Mention brand preference**: Distributors may offer alternatives
3. **Provide realistic timeline**: Rush orders cost more
4. **Include quantity**: Bulk orders get better pricing

### Comparing Effectively
1. **Wait for multiple responses**: Check back after 24-48 hours
2. **Consider total cost**: Include shipping in comparisons
3. **Check lead times**: Fastest isn't always best if you have time
4. **Verify availability**: Quoted quantity vs your needs

### Common Mistakes to Avoid
- Submitting without delivery address (can't match distributors)
- Not checking status (quotes expire)
- Comparing before quotes arrive (incomplete data)

## Limitations

### Current Limitations
- Email-based (responses take hours, not seconds)
- Regional coverage (Southeast US focus currently)
- Quote validity (typically 7-14 days)

### Coming Soon
- Direct API integration with major distributors
- Real-time inventory checking
- Automatic quote comparison alerts
- Price history tracking

## Setup

No special setup required. The skill uses mock email mode for testing. For production use with real distributors, SMTP credentials will be configured.

---

**Version**: 1.0.0-dev
**Last Updated**: 2026-01-13
**Status**: Development - Mock email mode active
