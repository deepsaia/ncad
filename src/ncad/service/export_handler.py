"""Export route: re-export a model to a chosen format and stream it as a browser download.

`ExportHandler` offloads the re-export to the build pool (via JobManager.arun_direct) and awaits it
directly (no job record: there is nothing to poll and the response is bytes, not JSON). The worker
returns the bytes base64-encoded (they must cross the process boundary + JSON-serialize); the
handler decodes them into a ``Content-Disposition: attachment`` download.
"""

import base64
import json

from ncad.service.base_handler import BaseApiHandler


class ExportHandler(BaseApiHandler):
    """POST /api/v1/export -> stream the model re-exported to {format} as a file download."""

    async def post(self, *args: str, **kwargs: str) -> None:  # pyrefly: ignore[bad-override]
        """Export {name, kind, format} to a download; 400 on bad request/failure."""
        try:
            body = json.loads(self.request.body or b"{}")
            name, kind, fmt = body["name"], body["kind"], body["format"]
        except (ValueError, KeyError, TypeError):
            self.write_error_json(400, "request needs JSON with 'name', 'kind', 'format'")
            return
        out = await self._job_manager.arun_direct(
            "export", {"name": name, "kind": kind, "format": fmt})
        if not out.get("ok"):
            self.write_error_json(400, out.get("error", "export failed"))
            return
        result = out["result"]
        self.set_header("Content-Type", result["content_type"])
        self.set_header("Content-Disposition",
                        f'attachment; filename="{result["download_name"]}"')
        self.safe_finish(base64.b64decode(result["data_b64"]))
