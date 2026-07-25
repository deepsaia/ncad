"""Job routes: poll a build job's status, or cancel it.

`JobStatusHandler` returns the job's status projection (stage/progress, plus result on done or
error on failed/cancelled); `JobCancelHandler` cancels a queued/running job. Both read the injected
JobManager. Mirrors the JSON-envelope contract of the other API handlers.
"""

from urllib.parse import unquote

from ncad.service.base_handler import BaseApiHandler


class JobStatusHandler(BaseApiHandler):
    """GET /api/v1/jobs/<id> -> the job's status dict, or 404 if unknown/evicted."""

    def get(self, *args: str, **kwargs: str) -> None:
        """Return the job status projection; 404 if the id is unknown or has been evicted."""
        job = self._job_manager.get(unquote(args[0]))
        if job is None:
            self.write_error_json(404, "unknown job")
            return
        self.write_json(200, job.to_status_dict())


class JobCancelHandler(BaseApiHandler):
    """POST /api/v1/jobs/<id>/cancel -> cancel a queued/running job."""

    def post(self, *args: str, **kwargs: str) -> None:
        """Cancel the job; 404 if unknown, else 200 with whether it was cancelled."""
        job_id = unquote(args[0])
        cancelled = self._job_manager.cancel(job_id)
        if not cancelled and self._job_manager.get(job_id) is None:
            self.write_error_json(404, "unknown job")
            return
        self.write_json(200, {"cancelled": cancelled})
