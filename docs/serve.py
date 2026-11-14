"""Serve the built documentation and open it in the browser (``pixi run docs-serve``).

    python docs/serve.py [--port 8000] [--no-browser]

Build the docs first with ``pixi run docs-quick`` (or ``pixi run docs`` for the sample videos).
"""

import argparse
import functools
import http.server
import sys
import threading
import webbrowser
from pathlib import Path

html_dir = Path(__file__).resolve().parent / "_build" / "html"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true", help="only serve, don't open a browser")
    args = parser.parse_args()

    if not (html_dir / "index.html").exists():
        sys.exit(f"no built docs in {html_dir}, run `pixi run docs-quick` first")

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(html_dir))
    server = http.server.ThreadingHTTPServer(("localhost", args.port), handler)
    url = f"http://localhost:{server.server_port}/"
    print(f"serving {html_dir} at {url} (ctrl+c to stop)")
    if not args.no_browser:
        # the server socket is already listening, so the page loads right away
        threading.Timer(0.2, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
