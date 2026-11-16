"""Print a sandbox link that writes a message (the "Demos/Text" sample), encoded so the
link does not show it right away.

    python examples/web/message_link.py "Happy birthday!"
    python examples/web/message_link.py "hi" --base http://localhost:8000/
"""

import argparse
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pyb2d3_sandbox.options import encode_option  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("text", help="the message ('\\n' for a new line)")
    parser.add_argument("--base", default="https://derthorsten.github.io/pyb2d3/sandbox/")
    args = parser.parse_args()
    text = args.text.replace("\\n", "\n")
    print(
        args.base
        + "?"
        + urlencode({"sample": "Demos/Text", "text": encode_option(text)}, safe=":/")
    )


if __name__ == "__main__":
    main()
