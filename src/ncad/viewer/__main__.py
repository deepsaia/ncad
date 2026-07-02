"""Launch the browser 3D viewer: ``python -m ncad.viewer [models_dir] [--port N]``.

Thin entrypoint that delegates to :class:`ncad.cli.viewer_cli.ViewerCli` so the module
argument path and the ``ncad`` console script share one implementation.
"""

import argparse
import logging

from ncad.cli.viewer_cli import ViewerCli

logger = logging.getLogger(__name__)


class ViewerMain:
    """Parses ``python -m ncad.viewer`` arguments and launches the viewer."""

    def run(self) -> None:
        """Parse args and run the viewer server in the foreground."""
        parser = argparse.ArgumentParser(description="ncad browser 3D viewer")
        parser.add_argument(
            "models_dir", nargs="?", default=None, help="directory of glTF/GLB models"
        )
        parser.add_argument("--host", default="127.0.0.1", help="bind address")
        parser.add_argument("--port", type=int, default=8000, help="bind port (0 = ephemeral)")
        args = parser.parse_args()
        ViewerCli().launch_viewer(args.models_dir, args.host, args.port)


def main() -> None:
    """Console-script / module entrypoint."""
    ViewerMain().run()


if __name__ == "__main__":
    main()
