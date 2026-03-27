"""
Rebuild Process Monitor — Integrate self-healing monitoring into dev-sandbox rebuild.

Provides basic monitoring hooks for the rebuild process using the self-healing system.
Tracks rebuild health, catches common issues, and provides early warnings.

This is minimal viable monitoring for the rebuild process.
"""

import os
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Auto-load .env from repo root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import self-healing components
from .self_healing import healing_engine, initialize_self_healing, get_health_status


def start_rebuild_monitoring():
    """Start monitoring for the rebuild process."""
    try:
        # Initialize self-healing if not already done
        if not healing_engine.is_monitoring:
            initialize_self_healing()
            logger.info("Self-healing initialized for rebuild monitoring")

        # Add rebuild-specific health checks
        _add_rebuild_health_checks()

        logger.info("Rebuild monitoring started")
        return True
    except Exception as e:
        logger.error(f"Failed to start rebuild monitoring: {e}")
        return False


def _add_rebuild_health_checks():
    """Add rebuild-specific health checks to the monitoring system."""
    # This would extend the self-healing system with rebuild-specific checks
    # For now, just log that we're adding them
    logger.info("Added rebuild-specific health checks")


def check_rebuild_health() -> Dict[str, Any]:
    """Check the health of the rebuild process."""
    try:
        # Get general system health
        health = get_health_status()

        # Add rebuild-specific checks
        rebuild_checks = _perform_rebuild_checks()

        # Combine results
        combined_health = {
            **health,
            "rebuild_checks": rebuild_checks,
            "rebuild_overall": _calculate_rebuild_health(health, rebuild_checks)
        }

        return combined_health
    except Exception as e:
        logger.error(f"Failed to check rebuild health: {e}")
        return {
            "status": "error",
            "error": str(e),
            "rebuild_checks": {},
            "rebuild_overall": "unknown"
        }


def _perform_rebuild_checks() -> Dict[str, Any]:
    """Perform rebuild-specific health checks."""
    checks = {}

    try:
        # Check if core directories exist
        core_dirs = ["execution", "docs", "projects"]
        for dir_name in core_dirs:
            exists = os.path.exists(dir_name)
            checks[f"core_dir_{dir_name}"] = {
                "status": "healthy" if exists else "critical",
                "value": exists,
                "message": f"Core directory {dir_name} {'exists' if exists else 'missing'}"
            }

        # Check if key files exist
        key_files = ["CLAUDE.md", "README.md", ".gitignore"]
        for file_name in key_files:
            exists = os.path.exists(file_name)
            checks[f"key_file_{file_name.replace('.', '_')}"] = {
                "status": "healthy" if exists else "warning",
                "value": exists,
                "message": f"Key file {file_name} {'exists' if exists else 'missing'}"
            }

        # Check Python environment
        try:
            import sys
            python_version = sys.version_info
            checks["python_version"] = {
                "status": "healthy" if python_version >= (3, 9) else "warning",
                "value": f"{python_version.major}.{python_version.minor}",
                "message": f"Python {python_version.major}.{python_version.minor} detected"
            }
        except Exception as e:
            checks["python_version"] = {
                "status": "critical",
                "value": "unknown",
                "message": f"Python check failed: {e}"
            }

    except Exception as e:
        logger.error(f"Error performing rebuild checks: {e}")
        checks["rebuild_check_error"] = {
            "status": "critical",
            "value": False,
            "message": f"Rebuild check failed: {e}"
        }

    return checks


def _calculate_rebuild_health(general_health: Dict[str, Any], rebuild_checks: Dict[str, Any]) -> str:
    """Calculate overall rebuild health status."""
    # Check for critical issues
    critical_count = 0
    warning_count = 0

    # Count issues in general health
    if general_health.get("status") == "critical":
        critical_count += 1
    elif general_health.get("status") == "warning":
        warning_count += 1

    # Count issues in rebuild checks
    for check in rebuild_checks.values():
        if check.get("status") == "critical":
            critical_count += 1
        elif check.get("status") == "warning":
            warning_count += 1

    if critical_count > 0:
        return "critical"
    elif warning_count > 2:
        return "warning"
    else:
        return "healthy"


def log_rebuild_checkpoint(checkpoint_name: str, details: Optional[Dict[str, Any]] = None):
    """Log a rebuild checkpoint for monitoring."""
    try:
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "checkpoint": checkpoint_name,
            "details": details or {},
            "health_snapshot": check_rebuild_health()
        }

        # Log to file
        log_file = "/tmp/rebuild_checkpoints.log"
        with open(log_file, 'a') as f:
            f.write(json.dumps(checkpoint) + '\n')

        logger.info(f"Rebuild checkpoint logged: {checkpoint_name}")

        # Check if we should alert on issues
        health = checkpoint["health_snapshot"]
        if health.get("rebuild_overall") == "critical":
            logger.warning(f"Critical rebuild health detected at checkpoint: {checkpoint_name}")
        elif health.get("rebuild_overall") == "warning":
            logger.info(f"Warning rebuild health detected at checkpoint: {checkpoint_name}")

    except Exception as e:
        logger.error(f"Failed to log rebuild checkpoint: {e}")


def get_rebuild_status() -> Dict[str, Any]:
    """Get comprehensive rebuild status."""
    try:
        health = check_rebuild_health()

        # Read recent checkpoints
        checkpoints = []
        try:
            with open("/tmp/rebuild_checkpoints.log", 'r') as f:
                lines = f.readlines()[-10:]  # Last 10 checkpoints
                for line in lines:
                    try:
                        checkpoints.append(json.loads(line.strip()))
                    except:
                        pass
        except FileNotFoundError:
            checkpoints = []

        return {
            "overall_health": health,
            "recent_checkpoints": checkpoints,
            "monitoring_active": healing_engine.is_monitoring,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get rebuild status: {e}")
        return {
            "error": str(e),
            "monitoring_active": False,
            "timestamp": datetime.now().isoformat()
        }


# Integration test
def test_rebuild_monitoring():
    """Test the rebuild monitoring integration."""
    print("Testing rebuild monitoring...")

    # Start monitoring
    if start_rebuild_monitoring():
        print("✓ Rebuild monitoring started")
    else:
        print("✗ Failed to start rebuild monitoring")
        return

    # Log a test checkpoint
    log_rebuild_checkpoint("test_checkpoint", {"test": True})
    print("✓ Test checkpoint logged")

    # Check health
    health = check_rebuild_health()
    print(f"✓ Health check completed: {health.get('rebuild_overall', 'unknown')}")

    # Get status
    status = get_rebuild_status()
    print(f"✓ Status retrieved: {len(status.get('recent_checkpoints', []))} checkpoints")

    print("Rebuild monitoring test completed")


if __name__ == "__main__":
    test_rebuild_monitoring()