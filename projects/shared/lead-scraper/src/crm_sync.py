"""
CRM Sync Automation - ClickUp Integration

Auto-syncs qualified leads to ClickUp CRM with deduplication, priority-based
sync rules, and comprehensive logging.
"""

import json
import os
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from src.lead_intake import LeadIntakeSystem, LeadStatus


class CRMSync:
    """ClickUp CRM synchronization system"""

    def __init__(self, api_token: str = None, list_id: str = None):
        """Initialize CRM sync

        Args:
            api_token: ClickUp API token (from CLICKUP_API_TOKEN env var if not provided)
            list_id: ClickUp list ID (from CLICKUP_LIST_ID env var if not provided)
        """
        self.lead_system = LeadIntakeSystem()

        # Get API credentials
        self.api_token = api_token or os.getenv('CLICKUP_API_TOKEN')
        self.list_id = list_id or os.getenv('CLICKUP_LIST_ID')

        if not self.api_token:
            raise ValueError("ClickUp API token required (CLICKUP_API_TOKEN env var)")
        if not self.list_id:
            raise ValueError("ClickUp list ID required (CLICKUP_LIST_ID env var)")

        self.base_url = 'https://api.clickup.com/api/v2'
        self.headers = {
            'Authorization': self.api_token,
            'Content-Type': 'application/json'
        }

        # Sync log
        project_root = Path(__file__).parent.parent
        self.sync_log_file = project_root / 'output' / 'crm_sync_log.json'
        self.sync_log_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_sync_log()

    def _load_sync_log(self):
        """Load sync log"""
        if self.sync_log_file.exists():
            with open(self.sync_log_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.sync_log = data
                else:
                    self.sync_log = []
        else:
            self.sync_log = []

    def _save_sync_log(self):
        """Save sync log"""
        with open(self.sync_log_file, 'w') as f:
            json.dump(self.sync_log, f, indent=2, default=str)

    def _check_sync_rules(self, lead: Dict) -> tuple[bool, str]:
        """Check if lead should be synced based on sync rules

        Args:
            lead: Lead dict from lead_intake

        Returns:
            Tuple of (should_sync: bool, reason: str)
        """
        status = lead.get('status')
        priority = lead.get('priority', 'medium')

        # Hot leads (critical/high priority, qualified/converted status) sync immediately
        if priority in ['critical', 'high'] and status in ['qualified', 'converted']:
            return (True, 'hot_lead_immediate_sync')

        # Qualified leads sync (daily batch would be handled by scheduler)
        if status == 'qualified':
            return (True, 'qualified_batch_sync')

        # Don't sync contacted (not qualified yet) or lost leads
        if status in ['contacted', 'lost']:
            return (False, f'status={status}_no_sync')

        # Default: sync if not already synced
        return (True, 'default_sync_rule')

    def _search_clickup_task(self, phone: str = None, email: str = None) -> Optional[str]:
        """Search ClickUp for existing task with same phone/email

        Args:
            phone: Phone number to search
            email: Email to search

        Returns:
            ClickUp task ID if found, None otherwise
        """
        try:
            # Search by custom field or task name/description
            # ClickUp API doesn't have great search, so we'll list tasks and filter
            url = f"{self.base_url}/list/{self.list_id}/task"
            params = {
                'archived': 'false',
                'subtasks': 'false'
            }

            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            tasks = response.json().get('tasks', [])

            # Search task descriptions for phone/email
            for task in tasks:
                description = task.get('description', '').lower()
                name = task.get('name', '').lower()

                if phone and phone.lower() in description:
                    return task['id']
                if email and email.lower() in description:
                    return task['id']

                # Also check custom fields if they exist
                custom_fields = task.get('custom_fields', [])
                for field in custom_fields:
                    value = str(field.get('value', '')).lower()
                    if phone and phone.lower() in value:
                        return task['id']
                    if email and email.lower() in value:
                        return task['id']

            return None

        except Exception as e:
            print(f"Warning: ClickUp search failed: {e}")
            return None

    def _create_clickup_task(self, lead: Dict) -> str:
        """Create ClickUp task for lead

        Args:
            lead: Lead dict

        Returns:
            Created task ID
        """
        contact = lead.get('contact_info', {})
        source = lead.get('source_channel', 'unknown')
        source_detail = lead.get('source_detail', {})

        # Build task name
        name = f"Lead: {contact.get('name', 'Unknown')} ({source})"

        # Build task description
        description_parts = [
            f"**Source:** {source}",
            f"**Business:** {lead.get('business_id', 'unknown')}",
            f"**Phone:** {contact.get('phone', 'N/A')}",
            f"**Email:** {contact.get('email', 'N/A')}",
            f"**Status:** {lead.get('status', 'new')}",
            f"**Priority:** {lead.get('priority', 'medium')}",
            f"**Lead ID:** {lead.get('lead_id')}",
            ""
        ]

        # Add UTM params if available
        if source_detail:
            if 'utm_source' in source_detail:
                description_parts.append(f"**UTM Source:** {source_detail.get('utm_source')}")
            if 'utm_campaign' in source_detail:
                description_parts.append(f"**UTM Campaign:** {source_detail.get('utm_campaign')}")
            if 'form_message' in source_detail:
                description_parts.append(f"\n**Message:**\n{source_detail.get('form_message')}")

        description = "\n".join(description_parts)

        # Map priority to ClickUp priority
        priority_map = {
            'critical': 1,  # Urgent
            'high': 2,      # High
            'medium': 3,    # Normal
            'low': 4        # Low
        }
        clickup_priority = priority_map.get(lead.get('priority', 'medium'), 3)

        # Create task
        url = f"{self.base_url}/list/{self.list_id}/task"
        payload = {
            'name': name,
            'description': description,
            'priority': clickup_priority,
            'tags': [
                source,
                lead.get('business_id', 'unknown'),
                lead.get('status', 'new')
            ]
        }

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()

        task = response.json()
        return task['id']

    def _add_clickup_comment(self, task_id: str, comment: str):
        """Add comment to existing ClickUp task

        Args:
            task_id: ClickUp task ID
            comment: Comment text
        """
        url = f"{self.base_url}/task/{task_id}/comment"
        payload = {
            'comment_text': comment
        }

        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()

    def sync_lead(self, lead: Dict, dry_run: bool = False) -> Dict:
        """Sync single lead to ClickUp

        Args:
            lead: Lead dict from lead_intake
            dry_run: If True, don't actually create tasks (just report what would happen)

        Returns:
            Sync result dict
        """
        lead_id = lead.get('lead_id')
        contact = lead.get('contact_info', {})

        # Check sync rules
        should_sync, reason = self._check_sync_rules(lead)

        if not should_sync:
            return {
                'lead_id': lead_id,
                'synced': False,
                'reason': reason,
                'dry_run': dry_run
            }

        # Check if already synced
        if lead.get('crm_synced') and not dry_run:
            return {
                'lead_id': lead_id,
                'synced': False,
                'reason': 'already_synced',
                'dry_run': dry_run
            }

        if dry_run:
            # Just report what would happen
            existing_task = self._search_clickup_task(
                phone=contact.get('phone'),
                email=contact.get('email')
            )

            if existing_task:
                action = f"Would add comment to existing task {existing_task}"
            else:
                action = "Would create new task"

            return {
                'lead_id': lead_id,
                'synced': False,
                'action': action,
                'reason': reason,
                'dry_run': True
            }

        # Check for duplicate in ClickUp
        existing_task_id = self._search_clickup_task(
            phone=contact.get('phone'),
            email=contact.get('email')
        )

        if existing_task_id:
            # Add comment about new touchpoint
            touchpoints = lead.get('touchpoint_history', [])
            latest = touchpoints[-1] if touchpoints else {}

            comment = f"**New touchpoint:** {latest.get('source_channel', 'unknown')} on {latest.get('timestamp', 'unknown')}"
            self._add_clickup_comment(existing_task_id, comment)

            result = {
                'lead_id': lead_id,
                'synced': True,
                'action': 'added_comment',
                'task_id': existing_task_id,
                'reason': reason
            }

        else:
            # Create new task
            task_id = self._create_clickup_task(lead)

            # Mark as synced in lead intake
            self.lead_system.mark_crm_synced(lead_id, task_id)

            result = {
                'lead_id': lead_id,
                'synced': True,
                'action': 'created_task',
                'task_id': task_id,
                'reason': reason
            }

        # Log sync
        log_entry = {
            **result,
            'timestamp': datetime.now().isoformat()
        }
        self.sync_log.append(log_entry)
        self._save_sync_log()

        return result

    def sync_all(self, dry_run: bool = False, status_filter: LeadStatus = None, priority_filter: str = None) -> List[Dict]:
        """Sync all leads that meet criteria

        Args:
            dry_run: If True, don't actually sync (just report)
            status_filter: Optional status filter (e.g., 'qualified')
            priority_filter: Optional priority filter (e.g., 'high')

        Returns:
            List of sync results
        """
        # Get unsynced leads
        if priority_filter:
            leads = self.lead_system.get_unsynced_leads(priority=priority_filter)
        else:
            leads = self.lead_system.get_unsynced_leads()

        # Filter by status if specified
        if status_filter:
            leads = [l for l in leads if l.get('status') == status_filter]

        results = []
        for lead in leads:
            result = self.sync_lead(lead, dry_run=dry_run)
            results.append(result)

        return results


def main():
    """CLI for CRM sync"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.crm_sync <command>")
        print("\nCommands:")
        print("  sync --dry-run          - Show what would be synced")
        print("  sync --for-real         - Actually sync to ClickUp")
        print("  sync-hot                - Sync only hot leads (high/critical priority)")
        print("  report                  - Show sync log summary")
        sys.exit(1)

    command = sys.argv[1]

    # Check for env vars
    if not os.getenv('CLICKUP_API_TOKEN'):
        print("Warning: CLICKUP_API_TOKEN not set - using test mode")
        print("Set environment variable to enable actual syncing")

    try:
        syncer = CRMSync()
    except ValueError as e:
        print(f"Error: {e}")
        print("\nSet these environment variables:")
        print("  export CLICKUP_API_TOKEN='your_token'")
        print("  export CLICKUP_LIST_ID='your_list_id'")
        sys.exit(1)

    if command == 'sync':
        dry_run = '--dry-run' in sys.argv
        for_real = '--for-real' in sys.argv

        if not dry_run and not for_real:
            print("Specify --dry-run or --for-real")
            sys.exit(1)

        results = syncer.sync_all(dry_run=dry_run)

        mode = "DRY RUN" if dry_run else "LIVE SYNC"
        print(f"\n=== CRM SYNC: {mode} ===\n")

        if len(results) == 0:
            print("No leads to sync")
        else:
            for result in results:
                print(f"Lead {result['lead_id'][:8]}...")
                print(f"  Action: {result.get('action', 'skipped')}")
                print(f"  Reason: {result['reason']}")
                if 'task_id' in result:
                    print(f"  Task: {result['task_id']}")
                print()

            synced_count = len([r for r in results if r.get('synced')])
            print(f"Total: {synced_count} / {len(results)} synced")

    elif command == 'sync-hot':
        results = syncer.sync_all(dry_run=False, priority_filter='high')

        print("\n=== HOT LEADS SYNC ===\n")
        print(f"Synced {len(results)} hot leads")

    elif command == 'report':
        print("\n=== CRM SYNC LOG ===\n")
        print(f"Total Sync Operations: {len(syncer.sync_log)}")

        # Count by action
        by_action = {}
        for entry in syncer.sync_log:
            action = entry.get('action', 'unknown')
            by_action[action] = by_action.get(action, 0) + 1

        if by_action:
            print("\nBy Action:")
            for action, count in sorted(by_action.items()):
                print(f"  {action}: {count}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
