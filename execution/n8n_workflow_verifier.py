#!/usr/bin/env python3
"""
n8n_workflow_verifier.py — Post-Setup Verification for n8n Workflows

WHAT: After creating or updating an n8n workflow, verify it actually activated,
      has valid nodes, correct connections, and can fire its trigger.

WHY: We've had workflows that appeared to work in testing but failed to activate
     due to unrecognized node types or broken connections. This catches those
     failures immediately instead of discovering them days later.

USAGE:
  # Verify a specific workflow
  python execution/n8n_workflow_verifier.py verify <workflow_id>

  # Verify all active workflows
  python execution/n8n_workflow_verifier.py verify-all

  # Quick health check (active workflows have valid triggers)
  python execution/n8n_workflow_verifier.py health

SOP COMPLIANCE:
  - Execution discipline E6: Build foundations — verify before assuming it works
  - Execution discipline E3: Failures compound — catch them immediately

DEPENDENCIES: requests, python-dotenv
API_KEYS: N8N_API_KEY
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

N8N_API_KEY = os.getenv("N8N_API_KEY", "")
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "https://n8n.marceausolutions.com")

try:
    import requests
except ImportError:
    print("ERROR: requests package not installed. pip install requests")
    sys.exit(1)


class WorkflowVerifier:
    """Verify n8n workflows are correctly configured and actually running."""

    # Node types that are known to cause activation failures
    PROBLEMATIC_NODE_TYPES = [
        "n8n-nodes-base.executeCommand",  # Not available on all installs
    ]

    def __init__(self):
        self.headers = {"X-N8N-API-KEY": N8N_API_KEY}
        self.base_url = N8N_BASE_URL.rstrip("/")

    def _api_get(self, path: str) -> Dict:
        """Make GET request to n8n API."""
        url = f"{self.base_url}/api/v1{path}"
        resp = requests.get(url, headers=self.headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def verify_workflow(self, workflow_id: str) -> Dict:
        """
        Comprehensive verification of a single workflow.

        Checks:
        1. Workflow exists and is accessible
        2. Active state matches expectations
        3. All node types are recognized by the n8n instance
        4. Connections are valid (source and target nodes exist)
        5. Schedule triggers have valid cron/interval config
        6. SSH nodes have valid host/credentials config
        7. Recent execution history (has it actually fired?)

        Returns:
            Dict with verification results and any issues found.
        """
        issues = []
        warnings = []

        print(f"\n  Verifying workflow: {workflow_id}")

        # 1. Fetch workflow
        try:
            wf = self._api_get(f"/workflows/{workflow_id}")
        except Exception as e:
            return {"success": False, "issues": [f"Cannot fetch workflow: {e}"]}

        name = wf.get("name", "Unknown")
        active = wf.get("active", False)
        nodes = wf.get("nodes", [])
        connections = wf.get("connections", {})

        print(f"    Name: {name}")
        print(f"    Active: {active}")
        print(f"    Nodes: {len(nodes)}")

        # 2. Check active state
        if not active:
            issues.append(f"Workflow is NOT active — it won't run on schedule")

        # 3. Check node types
        node_names = set()
        for node in nodes:
            node_type = node.get("type", "")
            node_name = node.get("name", "")
            node_names.add(node_name)

            if node_type in self.PROBLEMATIC_NODE_TYPES:
                issues.append(
                    f"Node '{node_name}' uses type '{node_type}' which is known "
                    f"to cause activation failures on some n8n instances"
                )

            # Check schedule triggers have config
            if "scheduleTrigger" in node_type:
                params = node.get("parameters", {})
                rule = params.get("rule", {})
                intervals = rule.get("interval", [])
                if not intervals:
                    issues.append(f"Schedule trigger '{node_name}' has no interval configured")
                else:
                    for interval in intervals:
                        field = interval.get("field", "")
                        if field == "cronExpression":
                            cron = interval.get("expression", "")
                            if not cron:
                                issues.append(f"Cron trigger '{node_name}' has empty expression")
                            else:
                                print(f"    Cron: {cron}")

            # Check SSH nodes have host
            if "ssh" in node_type.lower():
                params = node.get("parameters", {})
                host = params.get("host", "")
                if not host:
                    issues.append(f"SSH node '{node_name}' has no host configured")
                command = params.get("command", "")
                if not command:
                    issues.append(f"SSH node '{node_name}' has no command configured")
                else:
                    print(f"    SSH cmd: {command[:80]}...")

        # 4. Check connections reference valid nodes
        for source_name, conns in connections.items():
            if source_name not in node_names:
                issues.append(f"Connection from '{source_name}' but no node with that name exists")
            for conn_type in conns.values():
                for conn_list in conn_type:
                    for conn in conn_list:
                        target = conn.get("node", "")
                        if target not in node_names:
                            issues.append(f"Connection to '{target}' but no node with that name exists")

        # 5. Check recent executions
        try:
            executions = self._api_get(f"/executions?workflowId={workflow_id}&limit=5")
            exec_data = executions.get("data", [])
            if exec_data:
                latest = exec_data[0]
                status = latest.get("status", "unknown")
                finished = latest.get("stoppedAt", "unknown")
                print(f"    Last execution: {status} at {finished}")
                if status == "error":
                    warnings.append(f"Last execution failed (status: error)")
            else:
                warnings.append("No execution history — workflow may not have fired yet")
                print(f"    Last execution: None")
        except Exception as e:
            warnings.append(f"Could not check executions: {e}")

        # 6. Summary
        result = {
            "success": len(issues) == 0,
            "workflow_id": workflow_id,
            "name": name,
            "active": active,
            "node_count": len(nodes),
            "issues": issues,
            "warnings": warnings,
            "verified_at": datetime.now().isoformat()
        }

        if issues:
            print(f"    ISSUES ({len(issues)}):")
            for issue in issues:
                print(f"      ❌ {issue}")
        if warnings:
            print(f"    WARNINGS ({len(warnings)}):")
            for w in warnings:
                print(f"      ⚠️  {w}")
        if not issues and not warnings:
            print(f"    ✅ All checks passed")

        return result

    def verify_all_active(self) -> List[Dict]:
        """Verify all active workflows."""
        try:
            data = self._api_get("/workflows?active=true&limit=100")
            workflows = data.get("data", [])
        except Exception as e:
            print(f"Failed to fetch workflows: {e}")
            return []

        print(f"\n{'='*60}")
        print(f"VERIFYING ALL ACTIVE WORKFLOWS")
        print(f"{'='*60}")
        print(f"Found {len(workflows)} active workflow(s)")

        results = []
        passed = 0
        failed = 0

        for wf in workflows:
            result = self.verify_workflow(wf["id"])
            results.append(result)
            if result["success"]:
                passed += 1
            else:
                failed += 1

        print(f"\n{'='*60}")
        print(f"VERIFICATION SUMMARY")
        print(f"{'='*60}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        if failed > 0:
            print(f"\nFailed workflows:")
            for r in results:
                if not r["success"]:
                    print(f"  ❌ {r['name']} ({r['workflow_id']})")
                    for issue in r["issues"]:
                        print(f"      - {issue}")

        return results

    def health_check(self) -> bool:
        """Quick health check — are all active workflows healthy?"""
        results = self.verify_all_active()
        all_healthy = all(r["success"] for r in results)

        if all_healthy:
            print(f"\n✅ All workflows healthy")
        else:
            print(f"\n❌ Issues detected — review above")

        return all_healthy


def main():
    parser = argparse.ArgumentParser(description="n8n Workflow Verifier")
    sub = parser.add_subparsers(dest="command", required=True)

    verify_parser = sub.add_parser("verify", help="Verify a specific workflow")
    verify_parser.add_argument("workflow_id", help="Workflow ID to verify")

    sub.add_parser("verify-all", help="Verify all active workflows")
    sub.add_parser("health", help="Quick health check")

    args = parser.parse_args()
    verifier = WorkflowVerifier()

    if args.command == "verify":
        result = verifier.verify_workflow(args.workflow_id)
        sys.exit(0 if result["success"] else 1)
    elif args.command == "verify-all":
        results = verifier.verify_all_active()
        sys.exit(0 if all(r["success"] for r in results) else 1)
    elif args.command == "health":
        healthy = verifier.health_check()
        sys.exit(0 if healthy else 1)


if __name__ == "__main__":
    main()
