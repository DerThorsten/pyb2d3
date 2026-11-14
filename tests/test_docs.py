"""Every code example of the documentation lives in docs/snippets and is executed here,
so the docs cannot silently go out of date."""

import runpy
from pathlib import Path

import pytest

from .headless_test_frontend import run_in_headless_test_frontend

SNIPPETS = sorted((Path(__file__).resolve().parent.parent / "docs" / "snippets").glob("*.py"))


def test_snippets_found():
    assert len(SNIPPETS) >= 10


@pytest.mark.parametrize("path", SNIPPETS, ids=[p.stem for p in SNIPPETS])
def test_snippet_runs(path, capsys):
    namespace = runpy.run_path(str(path), run_name="docs_snippet")

    # the sandbox snippet defines a sample: run it in the headless test frontend
    if path.stem == "sample":
        sample = namespace["FallingBoxes"]
        assert sample.sample_category == "My Samples"
        run_in_headless_test_frontend(sample_class=sample, sample_settings=sample.Settings())
