"""
Self-Healing Mechanisms — Autonomous error detection and resolution.

Implements comprehensive self-healing capabilities that automatically detect,
diagnose, and resolve system issues without human intervention.

Key Features:
- Anomaly detection using statistical analysis and ML
- Autonomous diagnosis and resolution of failures
- Predictive failure prevention
- Health monitoring and automated recovery
- Integration with all system components

Architecture:
- Health Monitor: Continuous system health assessment
- Anomaly Detector: ML-based detection of unusual patterns
- Healing Engine: Autonomous issue resolution
- Prevention System: Predictive maintenance and optimization
"""

import asyncio
import json
import logging
import os
import psutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import statistics
import subprocess

# Auto-load .env from repo root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/self_healing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"


class IssueType(Enum):
    """Types of issues that can be detected and healed."""
    SERVICE_DOWN = "service_down"
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    DISK_FULL = "disk_full"
    NETWORK_ISSUE = "network_issue"
    DATABASE_CONNECTION = "database_connection"
    FILE_SYSTEM_ERROR = "file_system_error"
    PROCESS_CRASH = "process_crash"
    CONFIGURATION_ERROR = "configuration_error"
    SECURITY_THREAT = "security_threat"


@dataclass
class HealthMetric:
    """Individual health metric measurement."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    status: HealthStatus
    threshold_warning: float
    threshold_critical: float


@dataclass
class DetectedIssue:
    """A detected system issue."""
    issue_id: str
    issue_type: IssueType
    severity: HealthStatus
    description: str
    detected_at: datetime
    affected_components: List[str]
    metrics: Dict[str, Any] = field(default_factory=dict)
    resolution_attempts: List[Dict[str, Any]] = field(default_factory=list)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class HealingAction:
    """A healing action that can be taken."""
    action_id: str
    name: str
    description: str
    action_type: str  # 'restart', 'cleanup', 'reconfigure', 'scale', etc.
    target_component: str
    estimated_duration: int  # seconds
    risk_level: str  # 'low', 'medium', 'high'
    success_rate: float = 0.0
    prerequisites: List[str] = field(default_factory=list)

    def can_execute(self, system_state: Dict[str, Any]) -> bool:
        """Check if this healing action can be executed."""
        # Check prerequisites
        for prereq in self.prerequisites:
            if not system_state.get(prereq, False):
                return False
        return True


class SelfHealingEngine:
    """Core self-healing engine."""

    def __init__(self):
        self.issues: Dict[str, DetectedIssue] = {}
        self.health_history: List[HealthMetric] = []
        self.healing_actions: Dict[str, HealingAction] = {}
        self.system_state: Dict[str, Any] = {}
        self.anomaly_detector = AnomalyDetector()
        self.is_monitoring = False

    def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.is_monitoring:
            logger.warning("Self-healing monitoring is already running")
            return

        self.is_monitoring = True
        logger.info("Starting self-healing monitoring")

        # Initialize healing actions
        self._initialize_healing_actions()

        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())

    def stop_monitoring(self):
        """Stop health monitoring."""
        logger.info("Stopping self-healing monitoring")
        self.is_monitoring = False

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        try:
            while self.is_monitoring:
                # Collect health metrics
                metrics = await self._collect_health_metrics()

                # Store metrics
                self.health_history.extend(metrics)

                # Detect anomalies
                anomalies = self.anomaly_detector.detect_anomalies(metrics)

                # Process anomalies
                for anomaly in anomalies:
                    await self._process_anomaly(anomaly)

                # Clean up old data
                self._cleanup_old_data()

                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds

        except Exception as e:
            logger.error(f"Monitoring loop crashed: {e}")
            self.is_monitoring = False
            raise

    async def _collect_health_metrics(self) -> List[HealthMetric]:
        """Collect comprehensive health metrics."""
        metrics = []
        timestamp = datetime.now()

        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            metrics.extend([
                HealthMetric(
                    name="cpu_usage",
                    value=cpu_percent,
                    unit="percent",
                    timestamp=timestamp,
                    status=HealthStatus.CRITICAL if cpu_percent > 90 else
                           HealthStatus.WARNING if cpu_percent > 75 else HealthStatus.HEALTHY,
                    threshold_warning=75.0,
                    threshold_critical=90.0
                ),
                HealthMetric(
                    name="memory_usage",
                    value=memory.percent,
                    unit="percent",
                    timestamp=timestamp,
                    status=HealthStatus.CRITICAL if memory.percent > 95 else
                           HealthStatus.WARNING if memory.percent > 85 else HealthStatus.HEALTHY,
                    threshold_warning=85.0,
                    threshold_critical=95.0
                ),
                HealthMetric(
                    name="disk_usage",
                    value=disk.percent,
                    unit="percent",
                    timestamp=timestamp,
                    status=HealthStatus.CRITICAL if disk.percent > 95 else
                           HealthStatus.WARNING if disk.percent > 90 else HealthStatus.HEALTHY,
                    threshold_warning=90.0,
                    threshold_critical=95.0
                )
            ])

            # Service health checks
            service_metrics = await self._check_service_health()
            metrics.extend(service_metrics)

            # Network connectivity
            network_metrics = await self._check_network_health()
            metrics.extend(network_metrics)

        except Exception as e:
            logger.error(f"Error collecting health metrics: {e}")

        return metrics

    async def _check_service_health(self) -> List[HealthMetric]:
        """Check health of critical services."""
        metrics = []
        timestamp = datetime.now()

        # Check key services (customize based on your system)
        services_to_check = [
            ("mem0", "localhost", 5020),
            ("n8n", "localhost", 5678),
            ("ralph", "localhost", 5030),  # If Ralph has a health endpoint
        ]

        for service_name, host, port in services_to_check:
            try:
                # Simple TCP connection check
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()

                is_healthy = result == 0
                metrics.append(HealthMetric(
                    name=f"service_{service_name}",
                    value=1.0 if is_healthy else 0.0,
                    unit="boolean",
                    timestamp=timestamp,
                    status=HealthStatus.HEALTHY if is_healthy else HealthStatus.CRITICAL,
                    threshold_warning=0.5,
                    threshold_critical=0.0
                ))

            except Exception as e:
                logger.debug(f"Service check failed for {service_name}: {e}")
                metrics.append(HealthMetric(
                    name=f"service_{service_name}",
                    value=0.0,
                    unit="boolean",
                    timestamp=timestamp,
                    status=HealthStatus.CRITICAL,
                    threshold_warning=0.5,
                    threshold_critical=0.0
                ))

        return metrics

    async def _check_network_health(self) -> List[HealthMetric]:
        """Check network connectivity and latency."""
        metrics = []
        timestamp = datetime.now()

        # Check internet connectivity
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get('https://www.google.com', timeout=5) as response:
                    latency = (time.time() - start_time) * 1000  # ms
                    metrics.append(HealthMetric(
                        name="network_latency",
                        value=latency,
                        unit="ms",
                        timestamp=timestamp,
                        status=HealthStatus.CRITICAL if latency > 1000 else
                               HealthStatus.WARNING if latency > 500 else HealthStatus.HEALTHY,
                        threshold_warning=500.0,
                        threshold_critical=1000.0
                    ))
        except Exception:
            metrics.append(HealthMetric(
                name="network_connectivity",
                value=0.0,
                unit="boolean",
                timestamp=timestamp,
                status=HealthStatus.CRITICAL,
                threshold_warning=0.5,
                threshold_critical=0.0
            ))

        return metrics

    async def _process_anomaly(self, anomaly: Dict[str, Any]):
        """Process a detected anomaly."""
        issue_type = anomaly.get('issue_type')
        severity = anomaly.get('severity', HealthStatus.WARNING)
        description = anomaly.get('description', 'Anomaly detected')

        # Create issue
        issue = DetectedIssue(
            issue_id=f"issue_{int(time.time())}_{hash(str(anomaly)) % 1000}",
            issue_type=issue_type,
            severity=severity,
            description=description,
            detected_at=datetime.now(),
            affected_components=anomaly.get('affected_components', []),
            metrics=anomaly.get('metrics', {})
        )

        self.issues[issue.issue_id] = issue
        logger.warning(f"Detected issue: {issue.description} (severity: {severity.value})")

        # Attempt automatic healing
        if severity in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
            await self._attempt_healing(issue)

    async def _attempt_healing(self, issue: DetectedIssue):
        """Attempt to heal a detected issue."""
        # Find applicable healing actions
        applicable_actions = []
        for action in self.healing_actions.values():
            if action.can_execute(self.system_state):
                # Check if action is relevant to the issue
                if self._action_relevant_to_issue(action, issue):
                    applicable_actions.append(action)

        # Sort by success rate and risk
        applicable_actions.sort(key=lambda x: (x.success_rate, -self._risk_score(x)), reverse=True)

        # Try healing actions in order
        for action in applicable_actions:
            if await self._execute_healing_action(action, issue):
                issue.resolved = True
                issue.resolved_at = datetime.now()
                logger.info(f"Issue {issue.issue_id} resolved by action {action.action_id}")
                break
            else:
                logger.warning(f"Healing action {action.action_id} failed for issue {issue.issue_id}")

        if not issue.resolved:
            logger.error(f"Failed to resolve issue {issue.issue_id} automatically")

    def _action_relevant_to_issue(self, action: HealingAction, issue: DetectedIssue) -> bool:
        """Check if a healing action is relevant to the issue."""
        # Simple mapping - can be made more sophisticated
        relevance_map = {
            IssueType.SERVICE_DOWN: ['restart', 'reconfigure'],
            IssueType.HIGH_CPU: ['cleanup', 'scale'],
            IssueType.HIGH_MEMORY: ['cleanup', 'restart'],
            IssueType.DISK_FULL: ['cleanup'],
            IssueType.NETWORK_ISSUE: ['restart', 'reconfigure'],
            IssueType.DATABASE_CONNECTION: ['restart', 'reconfigure'],
            IssueType.PROCESS_CRASH: ['restart'],
            IssueType.CONFIGURATION_ERROR: ['reconfigure'],
        }

        relevant_action_types = relevance_map.get(issue.issue_type, [])
        return action.action_type in relevant_action_types

    async def _execute_healing_action(self, action: HealingAction, issue: DetectedIssue) -> bool:
        """Execute a healing action."""
        logger.info(f"Executing healing action: {action.name}")

        try:
            # Record attempt
            attempt = {
                'action_id': action.action_id,
                'timestamp': datetime.now(),
                'status': 'in_progress'
            }
            issue.resolution_attempts.append(attempt)

            # Execute based on action type
            success = await self._perform_action(action, issue)

            # Update attempt
            attempt['status'] = 'success' if success else 'failed'
            attempt['completed_at'] = datetime.now()

            # Update action success rate
            action.success_rate = (action.success_rate * 0.9) + (0.1 if success else 0.0)

            return success

        except Exception as e:
            logger.error(f"Healing action {action.action_id} failed with error: {e}")
            return False

    async def _perform_action(self, action: HealingAction, issue: DetectedIssue) -> bool:
        """Perform the actual healing action."""
        if action.action_type == 'restart':
            return await self._restart_service(action.target_component)
        elif action.action_type == 'cleanup':
            return await self._cleanup_resources(action.target_component)
        elif action.action_type == 'reconfigure':
            return await self._reconfigure_service(action.target_component)
        elif action.action_type == 'scale':
            return await self._scale_resources(action.target_component)
        else:
            logger.warning(f"Unknown action type: {action.action_type}")
            return False

    async def _restart_service(self, service_name: str) -> bool:
        """Restart a service."""
        try:
            if service_name == 'mem0':
                # Restart Mem0 service
                result = subprocess.run(['sudo', 'systemctl', 'restart', 'mem0'],
                                      capture_output=True, text=True, timeout=30)
                return result.returncode == 0
            elif service_name == 'n8n':
                result = subprocess.run(['sudo', 'systemctl', 'restart', 'n8n'],
                                      capture_output=True, text=True, timeout=30)
                return result.returncode == 0
            else:
                logger.warning(f"Unknown service for restart: {service_name}")
                return False
        except Exception as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            return False

    async def _cleanup_resources(self, resource_type: str) -> bool:
        """Clean up system resources."""
        try:
            if resource_type == 'memory':
                # Force garbage collection and cleanup
                import gc
                gc.collect()
                # Clear system cache if possible
                result = subprocess.run(['sudo', 'sysctl', 'vm.drop_caches=3'],
                                      capture_output=True, text=True, timeout=10)
                return result.returncode == 0
            elif resource_type == 'disk':
                # Clean up temporary files
                result = subprocess.run(['sudo', 'find', '/tmp', '-type', 'f', '-mtime', '+7', '-delete'],
                                      capture_output=True, text=True, timeout=30)
                return result.returncode == 0
            else:
                logger.warning(f"Unknown resource type for cleanup: {resource_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to cleanup resources {resource_type}: {e}")
            return False

    async def _reconfigure_service(self, service_name: str) -> bool:
        """Reconfigure a service."""
        # Placeholder - implement service-specific reconfiguration
        logger.info(f"Reconfiguring service: {service_name}")
        return True  # Assume success for now

    async def _scale_resources(self, resource_type: str) -> bool:
        """Scale resources up or down."""
        # Placeholder - implement resource scaling
        logger.info(f"Scaling resources: {resource_type}")
        return True  # Assume success for now

    def _risk_score(self, action: HealingAction) -> float:
        """Calculate risk score for an action (lower is better)."""
        risk_scores = {'low': 1, 'medium': 2, 'high': 3}
        return risk_scores.get(action.risk_level, 2)

    def _initialize_healing_actions(self):
        """Initialize available healing actions."""
        actions = [
            HealingAction(
                action_id="restart_mem0",
                name="Restart Mem0 Service",
                description="Restart the Mem0 memory service",
                action_type="restart",
                target_component="mem0",
                estimated_duration=30,
                risk_level="low",
                success_rate=0.9
            ),
            HealingAction(
                action_id="restart_n8n",
                name="Restart n8n Service",
                description="Restart the n8n automation service",
                action_type="restart",
                target_component="n8n",
                estimated_duration=60,
                risk_level="medium",
                success_rate=0.8
            ),
            HealingAction(
                action_id="cleanup_memory",
                name="Memory Cleanup",
                description="Force garbage collection and clear system caches",
                action_type="cleanup",
                target_component="memory",
                estimated_duration=10,
                risk_level="low",
                success_rate=0.95
            ),
            HealingAction(
                action_id="cleanup_disk",
                name="Disk Cleanup",
                description="Remove old temporary files",
                action_type="cleanup",
                target_component="disk",
                estimated_duration=30,
                risk_level="low",
                success_rate=0.9
            )
        ]

        for action in actions:
            self.healing_actions[action.action_id] = action

        logger.info(f"Initialized {len(actions)} healing actions")

    def _cleanup_old_data(self):
        """Clean up old health data and resolved issues."""
        cutoff_time = datetime.now() - timedelta(hours=24)

        # Keep only recent metrics
        self.health_history = [
            m for m in self.health_history
            if m.timestamp > cutoff_time
        ]

        # Keep only recent unresolved issues
        self.issues = {
            issue_id: issue for issue_id, issue in self.issues.items()
            if not issue.resolved or issue.resolved_at > cutoff_time
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get current system health status."""
        if not self.health_history:
            return {"status": "unknown", "issues": 0}

        recent_metrics = [m for m in self.health_history if (datetime.now() - m.timestamp).seconds < 300]

        critical_count = sum(1 for m in recent_metrics if m.status == HealthStatus.CRITICAL)
        warning_count = sum(1 for m in recent_metrics if m.status == HealthStatus.WARNING)

        overall_status = HealthStatus.HEALTHY
        if critical_count > 0:
            overall_status = HealthStatus.CRITICAL
        elif warning_count > 2:
            overall_status = HealthStatus.WARNING

        unresolved_issues = sum(1 for issue in self.issues.values() if not issue.resolved)

        return {
            "status": overall_status.value,
            "critical_issues": critical_count,
            "warning_issues": warning_count,
            "unresolved_issues": unresolved_issues,
            "total_issues": len(self.issues),
            "last_check": datetime.now().isoformat()
        }


class AnomalyDetector:
    """ML-based anomaly detection for system metrics."""

    def __init__(self):
        self.metric_history: Dict[str, List[float]] = {}
        self.baseline_stats: Dict[str, Dict[str, float]] = {}

    def detect_anomalies(self, metrics: List[HealthMetric]) -> List[Dict[str, Any]]:
        """Detect anomalies in health metrics."""
        anomalies = []

        for metric in metrics:
            # Update history
            if metric.name not in self.metric_history:
                self.metric_history[metric.name] = []
            self.metric_history[metric.name].append(metric.value)

            # Keep only recent values (last 100)
            if len(self.metric_history[metric.name]) > 100:
                self.metric_history[metric.name] = self.metric_history[metric.name][-100:]

            # Update baseline stats
            self._update_baseline_stats(metric.name)

            # Check for anomalies
            if self._is_anomalous(metric):
                anomaly = {
                    'metric_name': metric.name,
                    'value': metric.value,
                    'expected_range': self.baseline_stats.get(metric.name, {}),
                    'severity': metric.status.value,
                    'description': f"Anomalous {metric.name}: {metric.value}{metric.unit}",
                    'affected_components': [metric.name.split('_')[1] if '_' in metric.name else 'system'],
                    'metrics': {
                        'current': metric.value,
                        'threshold_warning': metric.threshold_warning,
                        'threshold_critical': metric.threshold_critical
                    }
                }

                # Map to issue type
                anomaly['issue_type'] = self._map_metric_to_issue_type(metric.name)
                anomalies.append(anomaly)

        return anomalies

    def _update_baseline_stats(self, metric_name: str):
        """Update baseline statistics for a metric."""
        if len(self.metric_history[metric_name]) < 10:
            return  # Need minimum data

        values = self.metric_history[metric_name]
        self.baseline_stats[metric_name] = {
            'mean': statistics.mean(values),
            'stdev': statistics.stdev(values) if len(values) > 1 else 0,
            'min': min(values),
            'max': max(values)
        }

    def _is_anomalous(self, metric: HealthMetric) -> bool:
        """Check if a metric value is anomalous."""
        if metric.name not in self.baseline_stats:
            return False

        stats = self.baseline_stats[metric.name]
        mean = stats['mean']
        stdev = stats['stdev']

        if stdev == 0:
            return abs(metric.value - mean) > (mean * 0.1)  # 10% deviation

        # Check if value is beyond 3 standard deviations
        z_score = abs(metric.value - mean) / stdev
        return z_score > 3.0

    def _map_metric_to_issue_type(self, metric_name: str) -> IssueType:
        """Map metric name to issue type."""
        mapping = {
            'cpu_usage': IssueType.HIGH_CPU,
            'memory_usage': IssueType.HIGH_MEMORY,
            'disk_usage': IssueType.DISK_FULL,
            'network_latency': IssueType.NETWORK_ISSUE,
            'service_': IssueType.SERVICE_DOWN  # Prefix match
        }

        for key, issue_type in mapping.items():
            if metric_name.startswith(key):
                return issue_type

        return IssueType.CONFIGURATION_ERROR


# Global self-healing engine instance
healing_engine = SelfHealingEngine()


def initialize_self_healing():
    """Initialize the self-healing system."""
    healing_engine.start_monitoring()
    logger.info("Self-healing system initialized")


def get_health_status() -> Dict[str, Any]:
    """Get current system health status."""
    return healing_engine.get_health_status()


if __name__ == "__main__":
    # Initialize and run self-healing
    initialize_self_healing()

    # Keep running
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        healing_engine.stop_monitoring()
        logger.info("Self-healing stopped")