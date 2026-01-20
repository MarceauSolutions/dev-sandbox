#!/usr/bin/env python3
"""
Docket System - Intelligent request queue and task management.

Usage:
    python -m src.docket status
    python -m src.docket add "description" --priority high
    python -m src.docket next
    python -m src.docket complete req_001
    python -m src.docket block req_002 --reason "waiting for approval"
    python -m src.docket sequence
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys


class DocketManager:
    """Manages intelligent request queue with prioritization and dependencies."""

    PRIORITY_LEVELS = ['urgent', 'high', 'normal', 'low']
    STATUS_TYPES = ['pending', 'in_progress', 'blocked', 'complete']

    def __init__(self, docket_path: Optional[Path] = None):
        if docket_path:
            self.docket_path = docket_path
        else:
            self.docket_path = Path(__file__).parent.parent / "output" / "DOCKET.json"

        self.docket_path.parent.mkdir(parents=True, exist_ok=True)
        self.docket = self._load_docket()

    def _load_docket(self) -> Dict[str, Any]:
        """Load docket from file or create new."""
        if self.docket_path.exists():
            with open(self.docket_path, 'r') as f:
                return json.load(f)
        else:
            return {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "total_requests": 0,
                    "completed_requests": 0
                },
                "requests": []
            }

    def _save_docket(self):
        """Save docket to file."""
        self.docket['metadata']['last_updated'] = datetime.now().isoformat()
        with open(self.docket_path, 'w') as f:
            json.dump(self.docket, f, indent=2)

    def _generate_request_id(self) -> str:
        """Generate next request ID."""
        existing_ids = [req['request_id'] for req in self.docket['requests']]
        if not existing_ids:
            return "req_001"

        # Extract numeric part and increment
        max_num = max(int(rid.split('_')[1]) for rid in existing_ids)
        return f"req_{str(max_num + 1).zfill(3)}"

    def add_request(
        self,
        description: str,
        priority: str = 'normal',
        user_message: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        ralph_decision: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a new request to the docket.

        Args:
            description: Brief description of the request
            priority: urgent/high/normal/low
            user_message: Full user request text (optional)
            dependencies: List of request_ids this depends on (optional)
            ralph_decision: Ralph decision engine output (optional)

        Returns:
            request_id of the new request
        """
        if priority not in self.PRIORITY_LEVELS:
            raise ValueError(f"Priority must be one of: {self.PRIORITY_LEVELS}")

        request_id = self._generate_request_id()

        request = {
            "request_id": request_id,
            "description": description,
            "user_message": user_message or description,
            "priority": priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "dependencies": dependencies or [],
            "blocked_reason": None,
            "ralph_decision": ralph_decision or {}
        }

        self.docket['requests'].append(request)
        self.docket['metadata']['total_requests'] += 1
        self._save_docket()

        return request_id

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific request by ID."""
        for req in self.docket['requests']:
            if req['request_id'] == request_id:
                return req
        return None

    def update_status(self, request_id: str, status: str, reason: Optional[str] = None):
        """Update the status of a request."""
        if status not in self.STATUS_TYPES:
            raise ValueError(f"Status must be one of: {self.STATUS_TYPES}")

        req = self.get_request(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found")

        req['status'] = status
        req['updated_at'] = datetime.now().isoformat()

        if status == 'blocked' and reason:
            req['blocked_reason'] = reason
        elif status == 'complete':
            self.docket['metadata']['completed_requests'] += 1
            req['completed_at'] = datetime.now().isoformat()

        self._save_docket()

    def complete_request(self, request_id: str):
        """Mark a request as complete."""
        self.update_status(request_id, 'complete')

    def block_request(self, request_id: str, reason: str):
        """Block a request with a reason."""
        self.update_status(request_id, 'blocked', reason)

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Get all pending requests."""
        return [req for req in self.docket['requests'] if req['status'] == 'pending']

    def get_blocked_requests(self) -> List[Dict[str, Any]]:
        """Get all blocked requests."""
        return [req for req in self.docket['requests'] if req['status'] == 'blocked']

    def get_in_progress_requests(self) -> List[Dict[str, Any]]:
        """Get all in-progress requests."""
        return [req for req in self.docket['requests'] if req['status'] == 'in_progress']

    def get_next_request(self) -> Optional[Dict[str, Any]]:
        """
        Get the next recommended request based on priority and dependencies.

        Returns:
            Next request to work on, or None if no actionable requests
        """
        pending = self.get_pending_requests()
        if not pending:
            return None

        # Filter out requests with unmet dependencies
        actionable = []
        for req in pending:
            if not req['dependencies']:
                actionable.append(req)
            else:
                # Check if all dependencies are complete
                deps_met = all(
                    self.get_request(dep_id)['status'] == 'complete'
                    for dep_id in req['dependencies']
                    if self.get_request(dep_id)
                )
                if deps_met:
                    actionable.append(req)

        if not actionable:
            return None

        # Sort by priority
        priority_order = {p: i for i, p in enumerate(self.PRIORITY_LEVELS)}
        actionable.sort(key=lambda r: priority_order[r['priority']])

        return actionable[0]

    def print_status(self):
        """Pretty print docket status."""
        print("\n" + "="*70)
        print("DOCKET STATUS")
        print("="*70)

        metadata = self.docket['metadata']
        print(f"\nTotal Requests: {metadata['total_requests']}")
        print(f"Completed: {metadata['completed_requests']}")
        print(f"Pending: {len(self.get_pending_requests())}")
        print(f"In Progress: {len(self.get_in_progress_requests())}")
        print(f"Blocked: {len(self.get_blocked_requests())}")

        # Pending requests
        pending = self.get_pending_requests()
        if pending:
            print("\n" + "-"*70)
            print("PENDING REQUESTS:")
            print("-"*70)
            for req in pending:
                self._print_request(req)

        # In progress
        in_progress = self.get_in_progress_requests()
        if in_progress:
            print("\n" + "-"*70)
            print("IN PROGRESS:")
            print("-"*70)
            for req in in_progress:
                self._print_request(req)

        # Blocked
        blocked = self.get_blocked_requests()
        if blocked:
            print("\n" + "-"*70)
            print("BLOCKED:")
            print("-"*70)
            for req in blocked:
                self._print_request(req)
                if req['blocked_reason']:
                    print(f"  Reason: {req['blocked_reason']}")

        print("\n" + "="*70 + "\n")

    def _print_request(self, req: Dict[str, Any]):
        """Print a single request."""
        priority_emoji = {
            'urgent': '🔥',
            'high': '⚡',
            'normal': '📋',
            'low': '💤'
        }

        print(f"\n{priority_emoji.get(req['priority'], '•')} [{req['request_id']}] {req['description']}")
        print(f"  Priority: {req['priority'].upper()}")

        if req['dependencies']:
            deps_status = []
            for dep_id in req['dependencies']:
                dep = self.get_request(dep_id)
                if dep:
                    status = '✅' if dep['status'] == 'complete' else '⏳'
                    deps_status.append(f"{status} {dep_id}")
            if deps_status:
                print(f"  Dependencies: {', '.join(deps_status)}")

        if req.get('ralph_decision') and req['ralph_decision'].get('use_ralph'):
            rd = req['ralph_decision']
            print(f"  Ralph: {rd.get('estimated_stories', '?')} stories, {rd.get('estimated_time', '?')}")

    def get_optimized_sequence(self) -> List[Dict[str, Any]]:
        """
        Calculate optimized task sequence based on dependencies and priorities.

        Returns:
            List of requests in recommended execution order
        """
        pending = self.get_pending_requests()
        if not pending:
            return []

        # Build dependency graph
        sequence = []
        processed = set()

        def can_execute(req):
            """Check if all dependencies are processed."""
            if not req['dependencies']:
                return True
            return all(dep_id in processed for dep_id in req['dependencies'])

        # Sort by priority for tie-breaking
        priority_order = {p: i for i, p in enumerate(self.PRIORITY_LEVELS)}
        pending_sorted = sorted(pending, key=lambda r: priority_order[r['priority']])

        # Process requests in dependency order
        while pending_sorted:
            made_progress = False

            for req in pending_sorted[:]:
                if can_execute(req):
                    sequence.append(req)
                    processed.add(req['request_id'])
                    pending_sorted.remove(req)
                    made_progress = True

            if not made_progress and pending_sorted:
                # Circular dependency detected
                print("\n⚠️  WARNING: Circular dependency detected!")
                print("Remaining requests cannot be executed:")
                for req in pending_sorted:
                    print(f"  - {req['request_id']}: depends on {req['dependencies']}")
                break

        return sequence

    def find_parallelizable_tasks(self, sequence: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Find tasks that can run in parallel (no shared dependencies).

        Returns:
            List of groups of request_ids that can run in parallel
        """
        parallel_groups = []

        # Group tasks that are at the same "level" (no dependencies on each other)
        levels = {}
        for req in sequence:
            level = len(req['dependencies'])
            if level not in levels:
                levels[level] = []
            levels[level].append(req['request_id'])

        # Only mark as parallel if multiple tasks at same level AND truly independent
        for level, req_ids in levels.items():
            if len(req_ids) > 1:
                # Verify they're truly independent (don't depend on each other)
                independent = []
                for rid in req_ids:
                    req = self.get_request(rid)
                    # Check if this req depends on any other in this level
                    depends_on_group = any(other_rid in req['dependencies'] for other_rid in req_ids if other_rid != rid)
                    if not depends_on_group:
                        independent.append(rid)

                if len(independent) > 1:
                    parallel_groups.append(independent)

        return parallel_groups

    def print_sequence(self):
        """Pretty print the optimized execution sequence."""
        sequence = self.get_optimized_sequence()

        if not sequence:
            print("\n✅ No pending requests. Docket is clear!\n")
            return

        print("\n" + "="*70)
        print("OPTIMIZED EXECUTION SEQUENCE")
        print("="*70)

        # Find parallelizable tasks
        parallel_groups = self.find_parallelizable_tasks(sequence)

        # Print sequence
        for i, req in enumerate(sequence, 1):
            # Check if this is part of a parallel group
            in_parallel = False
            for group in parallel_groups:
                if req['request_id'] in group:
                    group_ids = ', '.join(group)
                    if req['request_id'] == group[0]:  # Only print once per group
                        print(f"\n{i}. PARALLEL: {group_ids}")
                        for gid in group:
                            greq = self.get_request(gid)
                            print(f"   ├─ {greq['description']}")
                    in_parallel = True
                    break

            if not in_parallel:
                self._print_request(req)

                # Show what this blocks
                blocks = [r for r in sequence if req['request_id'] in r['dependencies']]
                if blocks:
                    block_ids = [r['request_id'] for r in blocks]
                    print(f"  Blocks: {', '.join(block_ids)}")

        print("\n" + "="*70 + "\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Docket management system")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Status command
    subparsers.add_parser('status', help='Show docket status')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add new request')
    add_parser.add_argument('description', help='Request description')
    add_parser.add_argument('--priority', choices=DocketManager.PRIORITY_LEVELS, default='normal')
    add_parser.add_argument('--depends-on', nargs='+', help='Request IDs this depends on')

    # Next command
    subparsers.add_parser('next', help='Show next recommended request')

    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Mark request as complete')
    complete_parser.add_argument('request_id', help='Request ID to complete')

    # Block command
    block_parser = subparsers.add_parser('block', help='Block a request')
    block_parser.add_argument('request_id', help='Request ID to block')
    block_parser.add_argument('--reason', required=True, help='Reason for blocking')

    # Start command (mark as in_progress)
    start_parser = subparsers.add_parser('start', help='Start working on a request')
    start_parser.add_argument('request_id', help='Request ID to start')

    # Sequence command
    subparsers.add_parser('sequence', help='Show optimized execution sequence')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    docket = DocketManager()

    if args.command == 'status':
        docket.print_status()

    elif args.command == 'add':
        request_id = docket.add_request(
            description=args.description,
            priority=args.priority,
            dependencies=args.depends_on
        )
        print(f"\n✅ Added to docket: {request_id}")
        print(f"Description: {args.description}")
        print(f"Priority: {args.priority.upper()}\n")

    elif args.command == 'next':
        next_req = docket.get_next_request()
        if next_req:
            print("\n" + "="*70)
            print("NEXT RECOMMENDED REQUEST:")
            print("="*70)
            docket._print_request(next_req)
            print("\n" + "="*70 + "\n")
        else:
            print("\n✅ No pending requests! Docket is clear.\n")

    elif args.command == 'complete':
        docket.complete_request(args.request_id)
        print(f"\n✅ Marked {args.request_id} as complete\n")

        # Show next
        next_req = docket.get_next_request()
        if next_req:
            print("Next up:")
            docket._print_request(next_req)
            print()

    elif args.command == 'block':
        docket.block_request(args.request_id, args.reason)
        print(f"\n⏸️  Blocked {args.request_id}")
        print(f"Reason: {args.reason}\n")

    elif args.command == 'start':
        docket.update_status(args.request_id, 'in_progress')
        print(f"\n▶️  Started working on {args.request_id}\n")

    elif args.command == 'sequence':
        docket.print_sequence()


if __name__ == '__main__':
    main()
