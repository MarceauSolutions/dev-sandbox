#!/usr/bin/env python3
"""
update_skill_docs.py - Living Documentation Updater

WHAT: Automatically updates fitness influencer SKILL.md and USE_CASES.json with new patterns
WHY: Keep documentation current and self-improving without manual editing
INPUT: New use case data (request, solution, outcome)
OUTPUT: Updated SKILL.md and USE_CASES.json
COST: FREE
TIME: <5 seconds

QUICK USAGE:
  python execution/update_skill_docs.py add-use-case \
    --request "Edit video for Instagram" \
    --capability "video_jumpcut.py" \
    --success true

CAPABILITIES:
  • Add new use cases to USE_CASES.json
  • Log unhandled requests for analysis
  • Update SKILL.md decision tree automatically
  • Track capability gaps and frequency
  • Generate learning insights
"""

import json
import os
from datetime import datetime
from pathlib import Path
import argparse
import re


class SkillDocUpdater:
    """Manages living documentation updates for fitness influencer skill."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.use_cases_path = self.base_dir / ".claude/skills/fitness-influencer-operations/USE_CASES.json"
        self.skill_path = self.base_dir / ".claude/skills/fitness-influencer-operations/SKILL.md"
        
    def load_use_cases(self):
        """Load USE_CASES.json data."""
        with open(self.use_cases_path, 'r') as f:
            return json.load(f)
    
    def save_use_cases(self, data):
        """Save updated USE_CASES.json."""
        data['last_updated'] = datetime.now().isoformat()
        with open(self.use_cases_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Updated USE_CASES.json at {data['last_updated']}")
    
    def add_use_case(self, request, capability, command=None, success=True, 
                     execution_time=None, cost=None, notes=None):
        """Add a new successful use case."""
        data = self.load_use_cases()
        
        # Generate ID
        category = self._categorize_request(request)
        existing_ids = [uc['id'] for uc in data['known_use_cases'] if uc['category'] == category]
        next_num = len(existing_ids) + 1
        use_case_id = f"{category}-{next_num:03d}"
        
        # Create use case entry
        new_case = {
            "id": use_case_id,
            "category": category,
            "user_request": request,
            "matched_capability": capability,
            "command": command or f"python execution/{capability}",
            "success": success,
            "frequency": 1,
            "last_used": datetime.now().strftime("%Y-%m-%d"),
            "avg_execution_time": execution_time or "unknown"
        }
        
        if cost:
            new_case['cost_per_use'] = cost
        if notes:
            new_case['notes'] = notes
        
        # Add to known use cases
        data['known_use_cases'].append(new_case)
        
        # Log learning
        data['learning_log'].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "lesson": f"New pattern discovered: {request}",
            "applied_to": use_case_id,
            "impact": "Expanded capability recognition"
        })
        
        self.save_use_cases(data)
        print(f"✓ Added use case: {use_case_id}")
        print(f"  Request: {request}")
        print(f"  Capability: {capability}")
        
        return use_case_id
    
    def log_unhandled_request(self, request, analysis=None, potential_solution=None, priority="medium"):
        """Log a request that couldn't be handled."""
        data = self.load_use_cases()
        
        # Check if already logged
        for ur in data['unhandled_requests']:
            if ur['request'].lower() == request.lower():
                print(f"⚠ Request already logged: {request}")
                return
        
        # Create new unhandled request entry
        next_id = len(data['unhandled_requests']) + 1
        new_request = {
            "id": f"pending-{next_id:03d}",
            "request": request,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis or self._analyze_request(request),
            "potential_solution": potential_solution,
            "status": "pending_review",
            "priority": priority
        }
        
        data['unhandled_requests'].append(new_request)
        
        # Update capability gaps if pattern emerges
        self._update_capability_gaps(data, request, analysis)
        
        self.save_use_cases(data)
        print(f"✓ Logged unhandled request: {request}")
        print(f"  Analysis: {new_request['analysis']}")
        
        return new_request['id']
    
    def increment_frequency(self, use_case_id):
        """Increment frequency counter for existing use case."""
        data = self.load_use_cases()
        
        for uc in data['known_use_cases']:
            if uc['id'] == use_case_id:
                uc['frequency'] += 1
                uc['last_used'] = datetime.now().strftime("%Y-%m-%d")
                self.save_use_cases(data)
                print(f"✓ Updated frequency for {use_case_id}: {uc['frequency']} uses")
                return
        
        print(f"⚠ Use case not found: {use_case_id}")
    
    def update_skill_md_example(self, use_case_id):
        """Add usage example to SKILL.md if frequency > 3."""
        data = self.load_use_cases()
        
        # Find use case
        use_case = None
        for uc in data['known_use_cases']:
            if uc['id'] == use_case_id:
                use_case = uc
                break
        
        if not use_case:
            print(f"⚠ Use case not found: {use_case_id}")
            return
        
        if use_case['frequency'] < 3:
            print(f"ℹ Frequency too low ({use_case['frequency']}) - need 3+ to add example")
            return
        
        # Read SKILL.md
        with open(self.skill_path, 'r') as f:
            skill_content = f.read()
        
        # Check if example already exists
        if use_case['user_request'] in skill_content:
            print(f"ℹ Example already exists in SKILL.md")
            return
        
        # Generate new example
        example_num = skill_content.count("**Example") + 1
        new_example = self._generate_example(use_case, example_num)
        
        # Insert before "Complete Documentation" section
        marker = "---\n\n## 📚 Complete Documentation"
        if marker in skill_content:
            skill_content = skill_content.replace(marker, f"{new_example}\n{marker}")
            
            with open(self.skill_path, 'w') as f:
                f.write(skill_content)
            
            print(f"✓ Added example {example_num} to SKILL.md")
            print(f"  Use case: {use_case['user_request']}")
        else:
            print("⚠ Could not find insertion point in SKILL.md")
    
    def _categorize_request(self, request):
        """Categorize request by type."""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ['video', 'edit', 'cut', 'silence']):
            return 'video_editing'
        elif any(word in request_lower for word in ['graphic', 'image', 'card', 'post', 'story']):
            return 'content_creation'
        elif any(word in request_lower for word in ['email', 'inbox', 'message']):
            return 'email_management'
        elif any(word in request_lower for word in ['revenue', 'analytics', 'expense', 'profit']):
            return 'business_analytics'
        elif any(word in request_lower for word in ['ai image', 'generate', 'grok']):
            return 'ai_generation'
        elif any(word in request_lower for word in ['ad', 'advertisement', 'promo']):
            return 'video_creation'
        else:
            return 'other'
    
    def _analyze_request(self, request):
        """Analyze unhandled request to extract components."""
        request_lower = request.lower()
        
        # Extract action verb
        action = None
        for verb in ['create', 'make', 'generate', 'edit', 'analyze', 'summarize', 'track']:
            if verb in request_lower:
                action = verb
                break
        
        # Extract object
        obj = None
        for item in ['pdf', 'video', 'graphic', 'plan', 'report', 'email', 'workout', 'meal']:
            if item in request_lower:
                obj = item
                break
        
        # Determine domain
        domain = self._categorize_request(request)
        
        return {
            "action": action or "unknown",
            "object": obj or "unknown",
            "domain": domain,
            "complexity": "medium"
        }
    
    def _update_capability_gaps(self, data, request, analysis):
        """Update capability gaps if pattern emerges."""
        if not analysis:
            return
        
        domain = analysis.get('domain') if isinstance(analysis, dict) else None
        if not domain or domain == 'other':
            return
        
        # Check if gap already exists
        for gap in data.get('capability_gaps', []):
            if domain in gap['description'].lower():
                gap['frequency_requested'] += 1
                return
        
        # Add new capability gap
        if 'capability_gaps' not in data:
            data['capability_gaps'] = []
        
        data['capability_gaps'].append({
            "gap": f"{domain.replace('_', ' ').title()}",
            "description": f"No tool for: {request}",
            "frequency_requested": 1,
            "proposed_solution": "To be determined",
            "priority": "low"
        })
    
    def _generate_example(self, use_case, num):
        """Generate SKILL.md example from use case."""
        return f"""
**Example {num}: {use_case['user_request']}**
```
User: "{use_case['user_request']}"

AI Decision:
  ✓ Matches: {use_case['category'].replace('_', ' ')} capability
  ✓ Execute: {use_case['matched_capability']}
  ✓ Frequency: {use_case['frequency']} successful uses

Command:
  {use_case['command']}

Output:
  {use_case.get('notes', 'See script header for output details')}
```
"""
    
    def generate_report(self):
        """Generate analytics report on use cases."""
        data = self.load_use_cases()
        
        print("\n" + "="*60)
        print("FITNESS INFLUENCER AI - USE CASE ANALYTICS")
        print("="*60)
        
        # Known use cases
        print(f"\n📊 Known Use Cases: {len(data['known_use_cases'])}")
        categories = {}
        total_freq = 0
        for uc in data['known_use_cases']:
            cat = uc['category']
            categories[cat] = categories.get(cat, 0) + uc['frequency']
            total_freq += uc['frequency']
        
        print(f"   Total uses: {total_freq}")
        print("\n   By category:")
        for cat, freq in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            pct = (freq / total_freq * 100) if total_freq > 0 else 0
            print(f"   - {cat.replace('_', ' ').title()}: {freq} ({pct:.1f}%)")
        
        # Unhandled requests
        print(f"\n⚠️  Unhandled Requests: {len(data.get('unhandled_requests', []))}")
        for ur in data.get('unhandled_requests', []):
            print(f"   - {ur['request']} [{ur['priority']} priority]")
        
        # Capability gaps
        print(f"\n🔍 Capability Gaps: {len(data.get('capability_gaps', []))}")
        for gap in sorted(data.get('capability_gaps', []), key=lambda x: x['frequency_requested'], reverse=True):
            print(f"   - {gap['gap']}: requested {gap['frequency_requested']} times")
        
        # Recent learning
        print(f"\n📚 Recent Learning: {len(data.get('learning_log', []))} insights")
        for log in data.get('learning_log', [])[-3:]:
            print(f"   - [{log['date']}] {log['lesson']}")
        
        print("\n" + "="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Update fitness influencer skill documentation')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Add use case
    add_parser = subparsers.add_parser('add-use-case', help='Add new successful use case')
    add_parser.add_argument('--request', required=True, help='User request text')
    add_parser.add_argument('--capability', required=True, help='Script that handled it')
    add_parser.add_argument('--command', help='Full command used')
    add_parser.add_argument('--success', type=bool, default=True, help='Whether it succeeded')
    add_parser.add_argument('--time', help='Execution time')
    add_parser.add_argument('--cost', type=float, help='Cost per use')
    add_parser.add_argument('--notes', help='Additional notes')
    
    # Log unhandled
    log_parser = subparsers.add_parser('log-unhandled', help='Log unhandled request')
    log_parser.add_argument('--request', required=True, help='User request text')
    log_parser.add_argument('--solution', help='Potential solution')
    log_parser.add_argument('--priority', default='medium', choices=['low', 'medium', 'high'])
    
    # Increment frequency
    freq_parser = subparsers.add_parser('increment', help='Increment use case frequency')
    freq_parser.add_argument('--id', required=True, help='Use case ID')
    
    # Update SKILL.md
    update_parser = subparsers.add_parser('update-skill', help='Update SKILL.md with example')
    update_parser.add_argument('--id', required=True, help='Use case ID')
    
    # Generate report
    subparsers.add_parser('report', help='Generate analytics report')
    
    args = parser.parse_args()
    updater = SkillDocUpdater()
    
    if args.command == 'add-use-case':
        use_case_id = updater.add_use_case(
            request=args.request,
            capability=args.capability,
            command=args.command,
            success=args.success,
            execution_time=args.time,
            cost=args.cost,
            notes=args.notes
        )
        print(f"\n💡 Tip: Use 'increment --id {use_case_id}' when this pattern repeats")
        
    elif args.command == 'log-unhandled':
        updater.log_unhandled_request(
            request=args.request,
            potential_solution=args.solution,
            priority=args.priority
        )
        
    elif args.command == 'increment':
        updater.increment_frequency(args.id)
        updater.update_skill_md_example(args.id)
        
    elif args.command == 'update-skill':
        updater.update_skill_md_example(args.id)
        
    elif args.command == 'report':
        updater.generate_report()
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()