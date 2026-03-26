"""
Maximum Leverage Autonomous Framework

This module provides the core autonomous execution capabilities for the elite system.
Includes self-triggering task loops, performance monitoring, and zero-human-intervention operation.

Key Components:
- AutonomousScheduler: Core scheduling engine
- Tower Loops: Self-sustaining operation for each tower
- Performance Monitoring: Real-time system health and optimization
- Self-Healing: Autonomous problem detection and resolution

Usage:
    from execution.autonomous import start_maximum_leverage_system
    start_maximum_leverage_system()  # Initiates 24/7 autonomous operation
"""

from .scheduler import (
    AutonomousScheduler,
    register_autonomous_task,
    start_autonomous_scheduler,
    stop_autonomous_scheduler,
    get_scheduler,
    TaskPriority,
    TaskStatus
)

from .tower_loops import (
    register_tower_autonomous_loops,
    start_maximum_leverage_system,
    get_system_status,
    TOWER_TASKS
)

__all__ = [
    # Scheduler components
    'AutonomousScheduler',
    'register_autonomous_task',
    'start_autonomous_scheduler',
    'stop_autonomous_scheduler',
    'get_scheduler',
    'TaskPriority',
    'TaskStatus',

    # Tower autonomous loops
    'register_tower_autonomous_loops',
    'start_maximum_leverage_system',
    'get_system_status',
    'TOWER_TASKS'
]

__version__ = "1.0.0-elite"