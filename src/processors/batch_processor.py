"""In-memory batch queue processor for long-running jobs."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Condition, Thread
from typing import Callable, Deque, Dict, List, Optional


@dataclass
class QueueJob:
    job_id: str
    enqueued_at: str


class BatchProcessor:
    """Threaded FIFO processor with queue-position inspection."""

    def __init__(self, worker_count: int, job_handler: Callable[[str], None], name: str = "batch"):
        self.worker_count = max(1, int(worker_count or 1))
        self.job_handler = job_handler
        self.name = name
        self._queue: Deque[QueueJob] = deque()
        self._in_progress: Dict[str, str] = {}
        self._threads: List[Thread] = []
        self._running = False
        self._cv = Condition()

    def start(self) -> None:
        with self._cv:
            if self._running:
                return
            self._running = True
            for index in range(self.worker_count):
                thread = Thread(target=self._worker_loop, name=f"{self.name}-worker-{index+1}", daemon=True)
                self._threads.append(thread)
                thread.start()

    def stop(self) -> None:
        with self._cv:
            self._running = False
            self._cv.notify_all()

    def submit(self, job_id: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._cv:
            self._queue.append(QueueJob(job_id=job_id, enqueued_at=now))
            position = len(self._queue)
            self._cv.notify()
            return position

    def queue_size(self) -> int:
        with self._cv:
            return len(self._queue)

    def get_position(self, job_id: str) -> Optional[int]:
        with self._cv:
            for index, job in enumerate(self._queue, start=1):
                if job.job_id == job_id:
                    return index
            return None

    def in_progress_count(self) -> int:
        with self._cv:
            return len(self._in_progress)

    def snapshot(self) -> Dict[str, int]:
        with self._cv:
            return {
                "workers": self.worker_count,
                "queued": len(self._queue),
                "running": len(self._in_progress),
            }

    def _worker_loop(self) -> None:
        while True:
            with self._cv:
                while self._running and not self._queue:
                    self._cv.wait()
                if not self._running and not self._queue:
                    return
                queued = self._queue.popleft()
                self._in_progress[queued.job_id] = datetime.now(timezone.utc).isoformat()

            try:
                self.job_handler(queued.job_id)
            finally:
                with self._cv:
                    self._in_progress.pop(queued.job_id, None)
