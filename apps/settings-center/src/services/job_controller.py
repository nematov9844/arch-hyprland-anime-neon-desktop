import threading
import uuid


class JobController:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.is_busy = False
        self.current_job_id = ""
        self.cancel_requested = False

    def start_job(self) -> str | None:
        with self._lock:
            if self.is_busy:
                return None
            self.is_busy = True
            self.cancel_requested = False
            self.current_job_id = uuid.uuid4().hex
            return self.current_job_id

    def request_cancel(self) -> None:
        with self._lock:
            if self.is_busy:
                self.cancel_requested = True

    def finish_job(self, job_id: str) -> None:
        with self._lock:
            if self.current_job_id != job_id:
                return
            self.is_busy = False
            self.cancel_requested = False
            self.current_job_id = ""

    def should_cancel(self, job_id: str) -> bool:
        with self._lock:
            return self.current_job_id == job_id and self.cancel_requested
