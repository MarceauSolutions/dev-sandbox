"""
Autonomous Execution Scheduler - Maximum Leverage Architecture

Core component for 24/7 self-sustaining operation cycles.
Implements self-triggering task loops, performance monitoring, and zero-human-intervention execution.

Part of the Maximum Leverage Architecture elite system.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import signal
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('execution/autonomous/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    """Task priority levels for autonomous scheduling."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AutonomousTask:
    """Represents an autonomous task in the system."""
    task_id: str
    name: str
    function: Callable
    priority: TaskPriority = TaskPriority.MEDIUM
    interval_seconds: Optional[int] = None  # For recurring tasks
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    max_retries: int = 3
    retry_count: int = 0
    timeout_seconds: int = 300  # 5 minutes default
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class AutonomousScheduler:
    """
    Elite autonomous execution scheduler for maximum leverage operations.

    Features:
    - Self-triggering task loops
    - Priority-based execution
    - Dependency resolution
    - Performance monitoring
    - Automatic failure recovery
    - Zero-human-intervention operation
    """

    def __init__(self):
        self.tasks: Dict[str, AutonomousTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.is_running = False
        self.performance_metrics = {
            "tasks_executed": 0,
            "tasks_failed": 0,
            "average_execution_time": 0.0,
            "uptime_seconds": 0,
            "last_health_check": None
        }

        # Threading for signal handling
        self.main_thread = threading.current_thread()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()

    def register_task(self, task: AutonomousTask) -> bool:
        """
        Register a new autonomous task.

        Args:
            task: The autonomous task to register

        Returns:
            bool: True if registered successfully
        """
        if task.task_id in self.tasks:
            logger.warning(f"Task {task.task_id} already registered, updating...")
            # Update existing task
            existing = self.tasks[task.task_id]
            existing.function = task.function
            existing.priority = task.priority
            existing.interval_seconds = task.interval_seconds
            existing.max_retries = task.max_retries
            existing.timeout_seconds = task.timeout_seconds
            existing.dependencies = task.dependencies
            existing.metadata.update(task.metadata)
            return True

        self.tasks[task.task_id] = task
        logger.info(f"Registered autonomous task: {task.name} ({task.task_id})")
        return True

    def unregister_task(self, task_id: str) -> bool:
        """
        Unregister an autonomous task.

        Args:
            task_id: ID of the task to unregister

        Returns:
            bool: True if unregistered successfully
        """
        if task_id not in self.tasks:
            logger.warning(f"Task {task_id} not found for unregistration")
            return False

        # Cancel if running
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            del self.running_tasks[task_id]

        del self.tasks[task_id]
        logger.info(f"Unregistered autonomous task: {task_id}")
        return True

    async def _execute_task(self, task: AutonomousTask) -> Dict[str, Any]:
        """
        Execute a single autonomous task with timeout and error handling.

        Args:
            task: The task to execute

        Returns:
            Dict with execution results
        """
        start_time = time.time()
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now()

        try:
            # Execute with timeout
            if asyncio.iscoroutinefunction(task.function):
                result = await asyncio.wait_for(
                    task.function(),
                    timeout=task.timeout_seconds
                )
            else:
                # Run sync function in thread pool
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    task.function
                )

            execution_time = time.time() - start_time
            task.status = TaskStatus.COMPLETED
            task.retry_count = 0  # Reset retry count on success

            # Update performance metrics
            self.performance_metrics["tasks_executed"] += 1
            self._update_execution_time(execution_time)

            logger.info(f"Task {task.task_id} completed successfully in {execution_time:.2f}s")

            return {
                "task_id": task.task_id,
                "status": "success",
                "execution_time": execution_time,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            self.performance_metrics["tasks_failed"] += 1
            logger.error(f"Task {task.task_id} timed out after {task.timeout_seconds}s")

            return {
                "task_id": task.task_id,
                "status": "timeout",
                "execution_time": time.time() - start_time,
                "error": f"Task timed out after {task.timeout_seconds} seconds",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            task.status = TaskStatus.FAILED
            self.performance_metrics["tasks_failed"] += 1
            logger.error(f"Task {task.task_id} failed: {str(e)}")

            # Handle retries
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                # Schedule retry with exponential backoff
                retry_delay = 2 ** task.retry_count
                task.next_run = datetime.now() + timedelta(seconds=retry_delay)
                logger.info(f"Scheduling retry {task.retry_count}/{task.max_retries} for task {task.task_id} in {retry_delay}s")

            return {
                "task_id": task.task_id,
                "status": "error",
                "execution_time": time.time() - start_time,
                "error": str(e),
                "retry_count": task.retry_count,
                "timestamp": datetime.now().isoformat()
            }

    def _update_execution_time(self, execution_time: float):
        """Update rolling average execution time."""
        current_avg = self.performance_metrics["average_execution_time"]
        total_tasks = self.performance_metrics["tasks_executed"]

        if total_tasks == 1:
            self.performance_metrics["average_execution_time"] = execution_time
        else:
            # Rolling average
            self.performance_metrics["average_execution_time"] = (
                (current_avg * (total_tasks - 1)) + execution_time
            ) / total_tasks

    def _check_dependencies(self, task: AutonomousTask) -> bool:
        """
        Check if all task dependencies are satisfied.

        Args:
            task: Task to check dependencies for

        Returns:
            bool: True if all dependencies are satisfied
        """
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                logger.warning(f"Task {task.task_id} has unknown dependency: {dep_id}")
                return False

            dep_task = self.tasks[dep_id]
            if dep_task.status not in [TaskStatus.COMPLETED]:
                return False

        return True

    def _schedule_next_run(self, task: AutonomousTask):
        """Schedule the next run for a recurring task."""
        if task.interval_seconds:
            task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)

    async def _scheduler_loop(self):
        """Main scheduler loop - runs every 15 seconds for maximum responsiveness."""
        logger.info("Autonomous scheduler loop started - 24/7 operation initiated")

        while self.is_running:
            try:
                current_time = datetime.now()

                # Find tasks ready to run
                ready_tasks = []
                for task in self.tasks.values():
                    if task.status == TaskStatus.PENDING and self._check_dependencies(task):
                        if task.next_run is None or current_time >= task.next_run:
                            ready_tasks.append(task)

                # Sort by priority (lower number = higher priority)
                ready_tasks.sort(key=lambda t: t.priority.value)

                # Execute ready tasks (limit concurrency to prevent overload)
                max_concurrent = min(len(ready_tasks), 10)  # Max 10 concurrent tasks

                for i in range(max_concurrent):
                    task = ready_tasks[i]
                    if task.task_id not in self.running_tasks:
                        # Create async task
                        coro = self._execute_task(task)
                        asyncio_task = asyncio.create_task(coro)
                        self.running_tasks[task.task_id] = asyncio_task

                        # Schedule next run for recurring tasks
                        self._schedule_next_run(task)

                # Clean up completed tasks
                completed_task_ids = []
                for task_id, asyncio_task in self.running_tasks.items():
                    if asyncio_task.done():
                        completed_task_ids.append(task_id)
                        try:
                            result = asyncio_task.result()
                            self.task_history.append(result)
                        except Exception as e:
                            logger.error(f"Error getting result for task {task_id}: {e}")

                for task_id in completed_task_ids:
                    del self.running_tasks[task_id]

                # Health check every 5 minutes
                if (not self.performance_metrics["last_health_check"] or
                    current_time - self.performance_metrics["last_health_check"] > timedelta(minutes=5)):
                    await self._perform_health_check()

                # Sleep for 15 seconds (high-frequency scheduling)
                await asyncio.sleep(15)

            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)  # Back off on errors

    async def _perform_health_check(self):
        """Perform comprehensive system health check."""
        try:
            self.performance_metrics["last_health_check"] = datetime.now()

            # Check system resources
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            health_status = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "active_tasks": len(self.running_tasks),
                "total_tasks": len(self.tasks),
                "tasks_executed": self.performance_metrics["tasks_executed"],
                "tasks_failed": self.performance_metrics["tasks_failed"],
                "average_execution_time": self.performance_metrics["average_execution_time"],
                "uptime_seconds": self.performance_metrics["uptime_seconds"]
            }

            # Log health status
            logger.info(f"Health check: CPU {cpu_percent:.1f}%, MEM {memory.percent:.1f}%, "
                       f"Tasks: {len(self.running_tasks)} running, {len(self.tasks)} total")

            # Alert on critical conditions
            if cpu_percent > 90:
                logger.warning("High CPU usage detected")
            if memory.percent > 90:
                logger.warning("High memory usage detected")
            if disk.percent > 95:
                logger.error("Critical disk space low")

        except ImportError:
            logger.warning("psutil not available for health monitoring")
        except Exception as e:
            logger.error(f"Health check failed: {e}")

    def start(self):
        """Start the autonomous scheduler."""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        self.is_running = True
        self.performance_metrics["start_time"] = datetime.now()

        logger.info("🚀 Maximum Leverage Autonomous Scheduler starting...")
        logger.info("🎯 Target: 99.9% autonomous operation rate")
        logger.info("⚡ 15-second scheduling cycles for maximum responsiveness")
        logger.info("🔄 Self-sustaining 24/7 operation initiated")

        # Start the scheduler loop
        asyncio.create_task(self._scheduler_loop())

    def stop(self):
        """Stop the autonomous scheduler gracefully."""
        if not self.is_running:
            logger.info("Scheduler stop requested")
            return

        logger.info("🛑 Initiating graceful shutdown of autonomous scheduler...")

        self.is_running = False

        # Cancel all running tasks
        for task_id, asyncio_task in self.running_tasks.items():
            asyncio_task.cancel()
            logger.info(f"Cancelled running task: {task_id}")

        self.running_tasks.clear()

        # Calculate final metrics
        uptime = datetime.now() - self.performance_metrics["start_time"]
        self.performance_metrics["uptime_seconds"] = uptime.total_seconds()

        logger.info("✅ Autonomous scheduler shutdown complete")
        logger.info(f"📊 Final metrics: {self.performance_metrics['tasks_executed']} tasks executed, "
                   f"{self.performance_metrics['tasks_failed']} failed, "
                   f"uptime: {uptime}")

    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status and metrics."""
        return {
            "is_running": self.is_running,
            "active_tasks": len(self.running_tasks),
            "total_tasks": len(self.tasks),
            "performance_metrics": self.performance_metrics,
            "recent_history": self.task_history[-10:] if self.task_history else []
        }

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        return {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status.value,
            "priority": task.priority.value,
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "next_run": task.next_run.isoformat() if task.next_run else None,
            "retry_count": task.retry_count,
            "is_running": task_id in self.running_tasks
        }

# Global scheduler instance
_scheduler_instance = None

def get_scheduler() -> AutonomousScheduler:
    """Get the global autonomous scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = AutonomousScheduler()
    return _scheduler_instance

# Convenience functions for tower integration
def register_autonomous_task(task_id: str, name: str, function: Callable,
                           priority: TaskPriority = TaskPriority.MEDIUM,
                           interval_seconds: Optional[int] = None,
                           dependencies: List[str] = None,
                           max_retries: int = 3,
                           timeout_seconds: int = 300) -> bool:
    """
    Register an autonomous task with the global scheduler.

    Args:
        task_id: Unique task identifier
        name: Human-readable task name
        function: Function to execute
        priority: Task priority level
        interval_seconds: Interval for recurring tasks (None for one-time)
        dependencies: List of task IDs this task depends on
        max_retries: Maximum retry attempts on failure
        timeout_seconds: Task timeout in seconds

    Returns:
        bool: True if registered successfully
    """
    scheduler = get_scheduler()
    task = AutonomousTask(
        task_id=task_id,
        name=name,
        function=function,
        priority=priority,
        interval_seconds=interval_seconds,
        dependencies=dependencies or [],
        max_retries=max_retries,
        timeout_seconds=timeout_seconds
    )
    return scheduler.register_task(task)

def start_autonomous_scheduler():
    """Start the global autonomous scheduler."""
    scheduler = get_scheduler()
    scheduler.start()

def stop_autonomous_scheduler():
    """Stop the global autonomous scheduler."""
    scheduler = get_scheduler()
    scheduler.stop()

# Auto-start on import (for development/testing)
if __name__ != "__main__":
    logger.info("Autonomous scheduler module loaded - call start_autonomous_scheduler() to begin 24/7 operation")

if __name__ == "__main__":
    # Test the autonomous scheduler
    print("Testing Maximum Leverage Autonomous Scheduler...")

    # Example autonomous tasks
    async def example_task():
        print("Executing example autonomous task")
        await asyncio.sleep(1)
        return "Task completed successfully"

    def sync_example_task():
        print("Executing sync example task")
        time.sleep(0.5)
        return "Sync task completed"

    # Register test tasks
    register_autonomous_task(
        "test_async_task",
        "Test Async Task",
        example_task,
        interval_seconds=30  # Run every 30 seconds
    )

    register_autonomous_task(
        "test_sync_task",
        "Test Sync Task",
        sync_example_task,
        interval_seconds=60  # Run every minute
    )

    # Start scheduler
    start_autonomous_scheduler()

    print("Autonomous scheduler started. Press Ctrl+C to stop.")

    # Keep running until interrupted
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nStopping autonomous scheduler...")
        stop_autonomous_scheduler()
        print("Scheduler stopped.")