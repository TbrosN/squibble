"""In-memory registry of active generation jobs."""

from __future__ import annotations

import uuid

from models.job import Job, JobStatus, LineGenerationStatus, LineStatus
from models.script import ScriptLine


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self, script: list[ScriptLine]) -> Job:
        job_id = uuid.uuid4().hex[:12]
        lines = [LineStatus(id=line.id, status=LineGenerationStatus.PENDING) for line in script]
        job = Job(id=job_id, script=script, lines=lines)
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        job.cancel_event.set()
        return True


job_store = JobStore()
