"""Launch the browser 3D viewer: ``python -m ncad.viewer [models_dir] [--port N]``.

Serves the glTF/GLB models in ``models_dir`` (default ``out/``) at a local URL.
"""

import argparse
import logging

from ncad.viewer.viewer_server import ViewerServer

logger = logging.getLogger(__name__)


def main() -> None:
    """Parse args and run the viewer server in the foreground."""
    parser = argparse.ArgumentParser(description="ncad browser 3D viewer")
    parser.add_argument("models_dir", nargs="?", default="out", help="directory of glTF/GLB models")
    parser.add_argument("--host", default="127.0.0.1", help="bind address")
    parser.add_argument("--port", type=int, default=8000, help="bind port (0 = ephemeral)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    server = ViewerServer(models_dir=args.models_dir, host=args.host, port=args.port)
    print(f"ncad viewer → {server.base_url}  (serving '{args.models_dir}', Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping…")
        server.stop()


if __name__ == "__main__":
    main()
