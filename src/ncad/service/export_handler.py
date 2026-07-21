"""Export route: re-export a model to a chosen format and stream it as a browser download.

`ExportHandler` re-exports the named model (of a given kind) to a target format via the injected
BuildService (which re-runs ncad's export into a temp dir and returns the bytes; nothing is written
to the models dir). The response is a ``Content-Disposition: attachment`` download.
"""

import json

from ncad.service.base_handler import BaseApiHandler
from ncad.viewer.build_service import BuildError


class ExportHandler(BaseApiHandler):
    """POST /api/v1/export -> stream the model re-exported to {format} as a file download."""

    def post(self, *args: str, **kwargs: str) -> None:
        """Export {name, kind, format} to a download; 400 on bad request/BuildError, 500 else."""
        try:
            body = json.loads(self.request.body or b"{}")
            name, kind, fmt = body["name"], body["kind"], body["format"]
        except (ValueError, KeyError, TypeError):
            self.write_error_json(400, "request needs JSON with 'name', 'kind', 'format'")
            return
        try:
            download_name, content_type, data = self._build_service.export_model(name, kind, fmt)
        except BuildError as exc:
            self.write_error_json(400, str(exc))
            return
        except Exception:  # noqa: BLE001 - never raise to the loop; 500
            self.write_error_json(500, "internal export error")
            return
        self.set_header("Content-Type", content_type)
        self.set_header("Content-Disposition", f'attachment; filename="{download_name}"')
        self.safe_finish(data)
