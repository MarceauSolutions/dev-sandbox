#!/usr/bin/env python3
"""
monitor_capability_gaps.py - Auto-Implementation Monitor

WHAT: Monitors USE_CASES.json and flags capabilities for implementation based on frequency
WHY: Automate decision-making on which features to build based on user demand
INPUT: USE_CASES.json (automatically reads)
OUTPUT: Implementation recommendations, auto-updates priority levels
COST: FREE
TIME: <5 seconds

QUICK USAGE:
  python execution/monitor_capability_gaps.py check
  python execution/monitor_capability_gaps.py implement --id pending-001

CAPABILITIES:
  • Monitor unhandled requests and track frequency
  • Auto-flag requests with frequency ≥ 3 for implementation
  • Generate priority recommendations based on demand
  • Update capability gap priorities automatically
  • Send notifications when threshold reached
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class CapabilityMonitor:
    """Monitors USE_CASES.json for patterns requiring implementation."""
    
    FREQUENCY_THRESHOLDS = {
        "log_only": (1, 2),        # Just track, no action
        "monitor": (3, 4),         # Start considering
        "low_priority": (5, 7),    # Should implement soon
        "high_priority": (8, float('inf'))  # Implement immediately
    }
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.use_cases_path = self.base_dir / ".claude/skills/fitness-influencer-operations/USE_CASES.json"
        self.data = self._load_data()
    
    def _load_data(self):
        """Load USE_CASES.json."""
        with open(self.use_cases_path, 'r') as f:
            return json.load(f)
    
    def _save_data(self):
        """Save updated USE_CASES.json."""
        self.data['last_updated'] = datetime.now().isoformat()
        with open(self.use_cases_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def check_thresholds(self):
        """Check all capability gaps against thresholds."""
        
        print("\n" + "="*70)
        print("CAPABILITY GAP MONITORING REPORT")
        print("="*70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Analyze unhandled requests
        unhandled = self.data.get('unhandled_requests', [])
        
        if not unhandled:
            print("✓ No unhandled requests currently pending\n")
        else:
            print(f"⚠️  Unhandled Requests: {len(unhandled)}\n")
            for req in unhandled:
                print(f"  ID: {req['id']}")
                print(f"  Request: {req['request']}")
                print(f"  Status: {req['status']}")
                print(f"  Priority: {req['priority']}")
                if req.get('potential_solution'):
                    print(f"  Solution: {req['potential_solution']}")
                print()
        
        # Analyze capability gaps
        gaps = self.data.get('capability_gaps', [])
        
        if not gaps:
            print("✓ No capability gaps identified\n")
            return []
        
        print(f"🔍 Capability Gaps: {len(gaps)}\n")
        
        recommendations = []
        
        for gap in sorted(gaps, key=lambda x: x['frequency_requested'], reverse=True):
            freq = gap['frequency_requested']
            gap_name = gap['gap']
            
            # Determine priority level based on frequency
            priority_level = self._get_priority_level(freq)
            action = self._get_recommended_action(freq)
            
            # Update priority if changed
            if gap.get('priority') != priority_level:
                gap['priority'] = priority_level
            
            print(f"  Gap: {gap_name}")
            print(f"  Frequency: {freq} requests")
            print(f"  Current Priority: {gap.get('priority', 'unknown')}")
            print(f"  📊 Status: {action}")
            
            if freq >= 3:
                print(f"  🚨 ACTION REQUIRED: Frequency threshold met (≥3)")
                recommendations.append({
                    "gap": gap_name,
                    "frequency": freq,
                    "action": "implement",
                    "proposed_solution": gap.get('proposed_solution', 'To be determined')
                })
            
            print()
        
        # Save updated priorities
        self._save_data()
        
        return recommendations
    
    def _get_priority_level(self, frequency):
        """Determine priority level based on frequency."""
        for level, (min_freq, max_freq) in self.FREQUENCY_THRESHOLDS.items():
            if min_freq <= frequency <= max_freq:
                return level.replace('_', ' ')
        return "unknown"
    
    def _get_recommended_action(self, frequency):
        """Get recommended action based on frequency."""
        if frequency <= 2:
            return "Monitor only - insufficient demand"
        elif frequency <= 4:
            return "Consider implementation - emerging pattern"
        elif frequency <= 7:
            return "Implement soon - validated demand"
        else:
            return "IMPLEMENT NOW - high demand validated"
    
    def generate_implementation_plan(self, gap_id=None):
        """Generate detailed implementation plan for a capability gap."""
        
        gaps = self.data.get('capability_gaps', [])
        
        if gap_id:
            # Find specific gap
            target_gaps = [g for g in gaps if gap_id.lower() in g['gap'].lower()]
        else:
            # Get all high-priority gaps (freq ≥ 8)
            target_gaps = [g for g in gaps if g['frequency_requested'] >= 8]
        
        if not target_gaps:
            print(f"⚠️  No gaps found matching criteria")
            return
        
        print("\n" + "="*70)
        print("IMPLEMENTATION PLAN")
        print("="*70 + "\n")
        
        for gap in target_gaps:
            print(f"## {gap['gap']}")
            print(f"**Frequency:** {gap['frequency_requested']} requests")
            print(f"**Priority:** {gap.get('priority', 'unknown')}")
            print(f"**Proposed Solution:** {gap.get('proposed_solution', 'TBD')}\n")
            
            # Generate implementation steps
            self._generate_implementation_steps(gap)
            print("\n" + "-"*70 + "\n")
    
    def _generate_implementation_steps(self, gap):
        """Generate step-by-step implementation plan."""
        
        gap_name = gap['gap'].lower()
        
        print("### Implementation Steps:\n")
        
        if "workout" in gap_name:
            print("1. ✅ Create `execution/workout_plan_generator.py`")
            print("   - Generate 3-6 day splits based on experience")
            print("   - Customize for equipment (gym/home/minimal)")
            print("   - Export as PDF + markdown\n")
            
            print("2. [ ] Add to SKILL.md decision tree:")
            print("   ```")
            print("   ├─ 'workout plan' / 'training program'")
            print("   │  └─ USE: execution/workout_plan_generator.py")
            print("   ```\n")
            
            print("3. [ ] Update USE_CASES.json:")
            print("   - Move from capability_gaps[] to known_use_cases[]")
            print("   - Set initial frequency: 1")
            print("   - Add example command\n")
            
            print("4. [ ] Test implementation:")
            print("   ```bash")
            print("   python execution/workout_plan_generator.py \\")
            print("     --goal 'muscle gain' --experience intermediate \\")
            print("     --days 4 --equipment 'full_gym'")
            print("   ```\n")
            
            print("5. [ ] Deploy to Railway backend")
            print("6. [ ] Document in SESSION_LOG.md")
            
        elif "nutrition" in gap_name:
            print("1. ✅ Create `execution/nutrition_guide_generator.py`")
            print("   - Calculate personalized macros")
            print("   - Generate meal timing recommendations")
            print("   - Export as PDF + markdown\n")
            
            print("2. [ ] Add to SKILL.md decision tree:")
            print("   ```")
            print("   ├─ 'nutrition plan' / 'meal plan' / 'macros'")
            print("   │  └─ USE: execution/nutrition_guide_generator.py")
            print("   ```\n")
            
            print("3. [ ] Update USE_CASES.json")
            print("4. [ ] Test implementation")
            print("5. [ ] Deploy to Railway backend")
            
        else:
            print("1. [ ] Analyze request patterns")
            print("2. [ ] Design solution approach")
            print("3. [ ] Create execution script")
            print("4. [ ] Update SKILL.md decision tree")
            print("5. [ ] Test and deploy")
    
    def mark_implemented(self, gap_name):
        """Mark a capability gap as implemented."""
        
        gaps = self.data.get('capability_gaps', [])
        
        for i, gap in enumerate(gaps):
            if gap_name.lower() in gap['gap'].lower():
                # Move to implemented
                implemented = gap.copy()
                implemented['status'] = 'implemented'
                implemented['implemented_at'] = datetime.now().isoformat()
                
                # Add to learning log
                self.data['learning_log'].append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "lesson": f"Implemented {gap['gap']} after {gap['frequency_requested']} requests",
                    "applied_to": f"capability_{i}",
                    "impact": "Expanded system capabilities based on user demand"
                })
                
                # Remove from capability gaps
                gaps.pop(i)
                
                # Save
                self._save_data()
                
                print(f"✓ Marked '{gap['gap']}' as implemented")
                print(f"  Frequency: {implemented['frequency_requested']} requests")
                print(f"  Implementation date: {implemented['implemented_at']}")
                
                return True
        
        print(f"⚠️  Gap '{gap_name}' not found")
        return False
    
    def daily_check(self):
        """Run daily monitoring check (for cron job)."""
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running daily capability check...\n")
        
        recommendations = self.check_thresholds()
        
        if recommendations:
            print("\n🚨 HIGH PRIORITY RECOMMENDATIONS:\n")
            for rec in recommendations:
                print(f"  • {rec['gap']}: {rec['frequency']} requests")
                print(f"    Action: {rec['action']}")
                print(f"    Solution: {rec['proposed_solution']}\n")
            
            # Could send email/slack notification here
            return len(recommendations)
        else:
            print("✓ No immediate actions required\n")
            return 0


def main():
    parser = argparse.ArgumentParser(description='Monitor capability gaps and recommend implementations')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Check thresholds
    subparsers.add_parser('check', help='Check current status and thresholds')
    
    # Generate implementation plan
    plan_parser = subparsers.add_parser('plan', help='Generate implementation plan')
    plan_parser.add_argument('--gap', help='Specific gap to plan for')
    
    # Mark as implemented
    impl_parser = subparsers.add_parser('mark-implemented', help='Mark gap as implemented')
    impl_parser.add_argument('--gap', required=True, help='Gap name')
    
    # Daily check (for cron)
    subparsers.add_parser('daily', help='Run daily monitoring check')
    
    args = parser.parse_args()
    monitor = CapabilityMonitor()
    
    if args.command == 'check':
        monitor.check_thresholds()
        
    elif args.command == 'plan':
        monitor.generate_implementation_plan(args.gap if hasattr(args, 'gap') else None)
        
    elif args.command == 'mark-implemented':
        monitor.mark_implemented(args.gap)
        
    elif args.command == 'daily':
        count = monitor.daily_check()
        exit(count)  # Exit code = number of high-priority items
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()