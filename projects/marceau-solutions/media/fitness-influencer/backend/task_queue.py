#!/usr/bin/env python3
"""
Background Task Queue for Fitness Influencer AI v2.0

Provides async job processing using Redis and RQ (Redis Queue).
Replaces synchronous video processing with background jobs.

Usage:
    from backend.task_queue import TaskQueue

    queue = TaskQueue()
    job = queue.submit_job("video_caption", {"video_url": "...", "style": "trending"})
    status = queue.get_status(job.job_id)
"""

import os
import uuid
import time
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

try:
    from redis import Redis
    from rq import Queue, Worker
    from rq.job import Job
    RQ_AVAILABLE = True
except ImportError:
    RQ_AVAILABLE = False
    Redis = None
    Queue = None
    Worker = None
    Job = None

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Supported job types."""
    VIDEO_CAPTION = "video_caption"
    VIDEO_FILLER_REMOVAL = "video_filler_removal"
    VIDEO_REFRAME = "video_reframe"
    VIDEO_EXPORT = "video_export"
    VIDEO_JUMPCUT = "video_jumpcut"
    LONG_TO_SHORTS = "long_to_shorts"
    IMAGE_GENERATION = "image_generation"
    TRANSCRIPTION = "transcription"


@dataclass
class JobResult:
    """Result of a submitted job."""
    job_id: str
    status: str
    job_type: str
    created_at: str
    estimated_time: int  # seconds
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class JobStatusResult:
    """Status check result."""
    job_id: str
    status: str
    progress: int
    estimated_remaining: int  # seconds
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Estimated processing times by job type (in seconds)
ESTIMATED_TIMES = {
    JobType.VIDEO_CAPTION: 120,  # 2 minutes
    JobType.VIDEO_FILLER_REMOVAL: 180,  # 3 minutes
    JobType.VIDEO_REFRAME: 90,  # 1.5 minutes
    JobType.VIDEO_EXPORT: 60,  # 1 minute
    JobType.VIDEO_JUMPCUT: 300,  # 5 minutes
    JobType.LONG_TO_SHORTS: 240,  # 4 minutes
    JobType.IMAGE_GENERATION: 30,  # 30 seconds
    JobType.TRANSCRIPTION: 60,  # 1 minute
}


class InMemoryQueue:
    """
    Fallback in-memory queue when Redis is not available.
    Useful for development and testing without Redis.
    """

    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, Dict[str, Any]] = {}
        logger.warning("Using in-memory queue (Redis not available). Jobs will not persist across restarts.")

    def submit(
        self,
        job_type: str,
        params: Dict[str, Any],
        user_id: Optional[str] = None,
        priority: int = 5
    ) -> JobResult:
        """Submit a job to the in-memory queue."""
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()

        job_data = {
            "job_id": job_id,
            "job_type": job_type,
            "params": params,
            "user_id": user_id,
            "priority": priority,
            "status": JobStatus.QUEUED.value,
            "progress": 0,
            "created_at": now.isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }

        self.jobs[job_id] = job_data

        estimated = ESTIMATED_TIMES.get(JobType(job_type), 60)

        return JobResult(
            job_id=job_id,
            status=JobStatus.QUEUED.value,
            job_type=job_type,
            created_at=now.isoformat(),
            estimated_time=estimated
        )

    def get_status(self, job_id: str) -> Optional[JobStatusResult]:
        """Get job status."""
        job = self.jobs.get(job_id)
        if not job:
            return None

        estimated = ESTIMATED_TIMES.get(JobType(job["job_type"]), 60)
        remaining = max(0, estimated - int(job.get("progress", 0) * estimated / 100))

        return JobStatusResult(
            job_id=job_id,
            status=job["status"],
            progress=job.get("progress", 0),
            estimated_remaining=remaining,
            result=job.get("result"),
            error=job.get("error")
        )

    def update_progress(self, job_id: str, progress: int) -> bool:
        """Update job progress."""
        if job_id not in self.jobs:
            return False
        self.jobs[job_id]["progress"] = progress
        self.jobs[job_id]["status"] = JobStatus.PROCESSING.value
        return True

    def complete_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Mark job as complete."""
        if job_id not in self.jobs:
            return False
        self.jobs[job_id]["status"] = JobStatus.COMPLETE.value
        self.jobs[job_id]["progress"] = 100
        self.jobs[job_id]["result"] = result
        self.jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        return True

    def fail_job(self, job_id: str, error: str) -> bool:
        """Mark job as failed."""
        if job_id not in self.jobs:
            return False
        self.jobs[job_id]["status"] = JobStatus.FAILED.value
        self.jobs[job_id]["error"] = error
        self.jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
        return True

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        if job_id not in self.jobs:
            return False
        if self.jobs[job_id]["status"] == JobStatus.PROCESSING.value:
            return False  # Can't cancel processing job
        self.jobs[job_id]["status"] = JobStatus.CANCELLED.value
        return True

    def list_jobs(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List jobs with optional filtering."""
        jobs = list(self.jobs.values())

        if user_id:
            jobs = [j for j in jobs if j.get("user_id") == user_id]
        if status:
            jobs = [j for j in jobs if j.get("status") == status]

        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return jobs[:limit]


class RedisQueue:
    """
    Production Redis-backed queue using RQ.
    Provides persistent job storage and distributed processing.
    """

    def __init__(self, redis_url: Optional[str] = None):
        if not RQ_AVAILABLE:
            raise ImportError("Redis and RQ are not installed. Run: pip install redis rq")

        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = Redis.from_url(redis_url)
        self.queue = Queue(connection=self.redis)
        self.high_priority = Queue("high", connection=self.redis)
        self.low_priority = Queue("low", connection=self.redis)

        # Job metadata storage
        self.job_prefix = "fitness:job:"

        logger.info(f"Connected to Redis at {redis_url}")

    def _get_queue(self, priority: int) -> Queue:
        """Get appropriate queue based on priority."""
        if priority <= 2:
            return self.high_priority
        elif priority >= 8:
            return self.low_priority
        return self.queue

    def _store_job_meta(self, job_id: str, data: Dict[str, Any]) -> None:
        """Store job metadata in Redis."""
        key = f"{self.job_prefix}{job_id}"
        self.redis.setex(key, 86400 * 7, json.dumps(data))  # 7 day TTL

    def _get_job_meta(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job metadata from Redis."""
        key = f"{self.job_prefix}{job_id}"
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    def submit(
        self,
        job_type: str,
        params: Dict[str, Any],
        user_id: Optional[str] = None,
        priority: int = 5,
        timeout: int = 600  # 10 minute default timeout
    ) -> JobResult:
        """Submit a job to Redis queue."""
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Store metadata
        meta = {
            "job_id": job_id,
            "job_type": job_type,
            "params": params,
            "user_id": user_id,
            "priority": priority,
            "status": JobStatus.QUEUED.value,
            "progress": 0,
            "created_at": now.isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }
        self._store_job_meta(job_id, meta)

        # Enqueue the job
        queue = self._get_queue(priority)
        queue.enqueue(
            "backend.worker.process_job",
            job_id=job_id,
            job_type=job_type,
            params=params,
            job_id=job_id,  # RQ job ID
            job_timeout=timeout
        )

        estimated = ESTIMATED_TIMES.get(JobType(job_type), 60)

        return JobResult(
            job_id=job_id,
            status=JobStatus.QUEUED.value,
            job_type=job_type,
            created_at=now.isoformat(),
            estimated_time=estimated
        )

    def get_status(self, job_id: str) -> Optional[JobStatusResult]:
        """Get job status from Redis."""
        meta = self._get_job_meta(job_id)
        if not meta:
            return None

        # Also check RQ job status
        try:
            rq_job = Job.fetch(job_id, connection=self.redis)
            if rq_job.is_finished:
                meta["status"] = JobStatus.COMPLETE.value
                meta["progress"] = 100
            elif rq_job.is_failed:
                meta["status"] = JobStatus.FAILED.value
                meta["error"] = str(rq_job.exc_info) if rq_job.exc_info else "Unknown error"
            elif rq_job.is_started:
                meta["status"] = JobStatus.PROCESSING.value
        except Exception:
            pass  # Job not found in RQ, use stored meta

        estimated = ESTIMATED_TIMES.get(JobType(meta["job_type"]), 60)
        remaining = max(0, estimated - int(meta.get("progress", 0) * estimated / 100))

        return JobStatusResult(
            job_id=job_id,
            status=meta["status"],
            progress=meta.get("progress", 0),
            estimated_remaining=remaining,
            result=meta.get("result"),
            error=meta.get("error")
        )

    def update_progress(self, job_id: str, progress: int) -> bool:
        """Update job progress."""
        meta = self._get_job_meta(job_id)
        if not meta:
            return False
        meta["progress"] = progress
        meta["status"] = JobStatus.PROCESSING.value
        if not meta.get("started_at"):
            meta["started_at"] = datetime.utcnow().isoformat()
        self._store_job_meta(job_id, meta)
        return True

    def complete_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Mark job as complete."""
        meta = self._get_job_meta(job_id)
        if not meta:
            return False
        meta["status"] = JobStatus.COMPLETE.value
        meta["progress"] = 100
        meta["result"] = result
        meta["completed_at"] = datetime.utcnow().isoformat()
        self._store_job_meta(job_id, meta)
        return True

    def fail_job(self, job_id: str, error: str) -> bool:
        """Mark job as failed."""
        meta = self._get_job_meta(job_id)
        if not meta:
            return False
        meta["status"] = JobStatus.FAILED.value
        meta["error"] = error
        meta["completed_at"] = datetime.utcnow().isoformat()
        self._store_job_meta(job_id, meta)
        return True

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job."""
        meta = self._get_job_meta(job_id)
        if not meta:
            return False
        if meta["status"] == JobStatus.PROCESSING.value:
            return False  # Can't cancel processing job easily

        # Try to remove from queue
        try:
            rq_job = Job.fetch(job_id, connection=self.redis)
            rq_job.cancel()
        except Exception:
            pass

        meta["status"] = JobStatus.CANCELLED.value
        self._store_job_meta(job_id, meta)
        return True

    def list_jobs(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List jobs with optional filtering."""
        # Scan for job keys
        pattern = f"{self.job_prefix}*"
        jobs = []

        for key in self.redis.scan_iter(match=pattern, count=100):
            data = self.redis.get(key)
            if data:
                job = json.loads(data)
                if user_id and job.get("user_id") != user_id:
                    continue
                if status and job.get("status") != status:
                    continue
                jobs.append(job)

        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return jobs[:limit]


class TaskQueue:
    """
    Main task queue interface.
    Automatically selects Redis or in-memory queue based on availability.
    """

    def __init__(self, redis_url: Optional[str] = None, force_memory: bool = False):
        """
        Initialize task queue.

        Args:
            redis_url: Redis connection URL (defaults to REDIS_URL env var)
            force_memory: Force in-memory queue even if Redis available
        """
        self._queue = None

        if force_memory:
            self._queue = InMemoryQueue()
        else:
            redis_url = redis_url or os.getenv("REDIS_URL")
            if redis_url and RQ_AVAILABLE:
                try:
                    self._queue = RedisQueue(redis_url)
                except Exception as e:
                    logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory queue.")
                    self._queue = InMemoryQueue()
            else:
                self._queue = InMemoryQueue()

    def submit_job(
        self,
        job_type: str,
        params: Dict[str, Any],
        user_id: Optional[str] = None,
        priority: int = 5
    ) -> JobResult:
        """
        Submit a job for background processing.

        Args:
            job_type: Type of job (from JobType enum)
            params: Job parameters
            user_id: Optional user ID for tracking
            priority: Priority 1-10 (1=highest)

        Returns:
            JobResult with job_id and status
        """
        return self._queue.submit(job_type, params, user_id, priority)

    def get_status(self, job_id: str) -> Optional[JobStatusResult]:
        """Get job status by ID."""
        return self._queue.get_status(job_id)

    def update_progress(self, job_id: str, progress: int) -> bool:
        """Update job progress (0-100)."""
        return self._queue.update_progress(job_id, progress)

    def complete_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Mark job as complete with result."""
        return self._queue.complete_job(job_id, result)

    def fail_job(self, job_id: str, error: str) -> bool:
        """Mark job as failed with error."""
        return self._queue.fail_job(job_id, error)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job."""
        return self._queue.cancel_job(job_id)

    def list_jobs(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List jobs with optional filtering."""
        return self._queue.list_jobs(user_id, status, limit)

    @property
    def is_redis(self) -> bool:
        """Check if using Redis backend."""
        return isinstance(self._queue, RedisQueue)


# Global queue instance
_queue_instance: Optional[TaskQueue] = None


def get_queue() -> TaskQueue:
    """Get or create the global queue instance."""
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = TaskQueue()
    return _queue_instance


def submit_job(
    job_type: str,
    params: Dict[str, Any],
    user_id: Optional[str] = None,
    priority: int = 5
) -> JobResult:
    """Convenience function to submit a job."""
    return get_queue().submit_job(job_type, params, user_id, priority)


def get_status(job_id: str) -> Optional[JobStatusResult]:
    """Convenience function to get job status."""
    return get_queue().get_status(job_id)


def cancel_job(job_id: str) -> bool:
    """Convenience function to cancel a job."""
    return get_queue().cancel_job(job_id)
