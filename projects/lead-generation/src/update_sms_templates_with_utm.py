"""
Helper script to add UTM-tracked links to SMS templates

Updates existing SMS templates to include UTM-tracked landing page links
for proper source attribution.
"""

import json
from pathlib import Path
from src.utm_tracker import generate_sms_link


def update_template_with_utm_link(template_path: Path):
    """Add UTM-tracked link to SMS template

    Args:
        template_path: Path to template JSON file
    """
    with open(template_path, 'r') as f:
        template = json.load(f)

    template_name = template.get('template_name', template_path.stem)
    pain_point = template.get('pain_point', 'general')

    # Determine business based on pain point
    if 'hvac' in template_name.lower() or 'energy' in template_name.lower():
        business_id = 'swflorida-hvac'
    elif 'shipping' in template_name.lower() or 'logistics' in template_name.lower():
        business_id = 'shipping-logistics'
    else:
        business_id = 'marceau-solutions'

    # Determine landing page path
    if 'audit' in template_name.lower():
        path = '/free-audit'
    elif 'demo' in template_name.lower():
        path = '/demo'
    elif 'setup' in template_name.lower():
        path = '/get-started'
    else:
        path = '/contact'

    # Generate UTM link
    campaign = f"{pain_point}_jan26"  # Current month campaign
    utm_link = generate_sms_link(
        business_id=business_id,
        campaign=campaign,
        template_name=template_name,
        path=path
    )

    # Add UTM link to template
    template['utm_tracked_link'] = utm_link

    # Add note about UTM tracking
    if 'notes' in template:
        if isinstance(template['notes'], str):
            template['notes'] = [template['notes']]
        template['notes'].append(f"UTM tracked link: {utm_link}")
    else:
        template['notes'] = [f"UTM tracked link: {utm_link}"]

    # Save updated template
    with open(template_path, 'w') as f:
        json.dump(template, f, indent=2)

    print(f"✓ Updated {template_path.name} with UTM link")
    print(f"  Link: {utm_link}")


def main():
    """Update all SMS templates with UTM links"""
    project_root = Path(__file__).parent.parent
    templates_dir = project_root / 'templates' / 'sms' / 'optimized'

    if not templates_dir.exists():
        print(f"Templates directory not found: {templates_dir}")
        return

    template_files = list(templates_dir.glob('*.json'))
    print(f"\nFound {len(template_files)} SMS templates to update...\n")

    for template_path in template_files:
        update_template_with_utm_link(template_path)

    print(f"\n✓ Updated {len(template_files)} templates with UTM tracking")


if __name__ == '__main__':
    main()
