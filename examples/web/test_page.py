"""Load the built sandbox page in headless chromium: a cold load, then a reload (the
archives from pyjs' cache, pyjs >= 5.1). Prints the loading times, fails on errors.

    pixi run -e web-test web-test      # builds the page, installs chromium, runs this
    python examples/web/test_page.py build/web_sandbox [--sample "Games/Bridge Builder"]
"""

import argparse
import functools
import http.server
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

READY = "pyb2d3 sandbox loading times"  # main.js logs it when the sandbox runs


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass  # no line per request


def serve(directory):
    """serve `directory` on a free local port in a thread, returns the url"""
    handler = functools.partial(QuietHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}/"


def load(page, url, timeout):
    """open `url`, wait until the sandbox runs: (seconds, the steps' times, problems)"""
    problems, steps = [], {}

    def on_console(message):
        if message.type == "error":
            problems.append(f"console error: {message.text}")
        if message.text.startswith(READY) and len(message.args) > 1:
            steps.update(message.args[1].json_value())

    page.on("console", on_console)
    page.on("pageerror", lambda error: problems.append(f"page error: {error}"))

    def on_request_failed(request):
        # ERR_ABORTED: cancelled by the next navigation / closing the browser (e.g. the
        # code editor's background preload), not a failure of the page
        if "ERR_ABORTED" not in (request.failure or ""):
            problems.append(f"request failed: {request.url} {request.failure}")

    page.on("requestfailed", on_request_failed)
    start = time.perf_counter()
    page.goto(url)
    status = ""
    while not steps and time.perf_counter() - start < timeout:
        status = page.inner_text("#status")
        if status.startswith("error"):
            problems.append(f"status: {status}")
            break
        page.wait_for_timeout(200)
    if not steps and not problems:
        problems.append(f"not running after {timeout:.0f} s, status: {status!r}")
    page.remove_listener("console", on_console)
    return time.perf_counter() - start, steps, problems


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("page", type=Path, help="the built page directory")
    parser.add_argument("--sample", default="Games/Bridge Builder", help="the start sample")
    parser.add_argument("--timeout", type=float, default=240.0, help="seconds per load")
    parser.add_argument("--query", default="", help='more query parameters, e.g. "text=b64:aGk"')
    parser.add_argument("--screenshot", type=Path, help="save a screenshot after the last load")
    args = parser.parse_args()

    url = serve(args.page) + f"?sample={args.sample}" + (f"&{args.query}" if args.query else "")
    failed = False
    with sync_playwright() as p:
        # webgl without a gpu: swiftshader
        browser = p.chromium.launch(args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader"])
        page = browser.new_context().new_page()  # one context: the reload sees the cache
        for label in ("cold", "reload (cache)"):
            seconds, steps, problems = load(page, url, args.timeout)
            print(f"{label}: {seconds:.1f} s, steps (s since start): {steps}")
            for problem in problems:
                print(f"   {problem}")
            failed |= bool(problems)
        if args.screenshot:
            page.wait_for_timeout(2000)  # let the sample run a bit
            page.screenshot(path=str(args.screenshot))
        browser.close()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
