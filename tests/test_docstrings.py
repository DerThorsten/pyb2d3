"""The docstrings are generated from box2d's header comments (scripts/generate_docstrings.py)."""

import importlib.util
from pathlib import Path

import pytest

import pyb2d3 as b2d

REPO = Path(__file__).resolve().parent.parent


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_docstrings", REPO / "scripts" / "generate_docstrings.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_docstrings_are_current():
    generator = load_generator()
    include_dir = generator.default_include_dir()
    if include_dir is None:
        pytest.skip("box2d headers not found")
    stale = generator.stale_files(include_dir)
    assert not stale, f"run `pixi run docstrings`, out of date: {[str(p) for p in stale]}"


@pytest.mark.parametrize(
    "obj, text",
    [
        (b2d.Body.apply_force, "Apply a force at a world point"),
        (b2d.Body.position, "World position of a body"),
        (b2d.Bodies.apply_force, "Apply a force at a world point"),
        (b2d.BodyDef, "A body definition holds all the data"),
        (b2d.BodyDef.gravity_scale, "Scale the gravity applied to this body"),
        (b2d.ShapeDef.enable_contact_events, "Enable contact events"),
    ],
)
def test_box2d_docs_are_attached(obj, text):
    assert text in (obj.__doc__ or "")


def test_id_parameter_is_dropped():
    # box2d's first parameter (bodyId) is `self` in python
    assert "body_id" not in b2d.Body.apply_force.__doc__
    assert "Args:" in b2d.Body.apply_force.__doc__
