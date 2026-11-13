"""Guard against silently missing box2d API.

Every public ``B2_API`` function of the box2d headers pyb2d3 is built against must
either be referenced by the binding code, or be listed in ``NOT_BOUND`` with a reason.
When box2d is updated, new functions make this test fail until they are bound
(or consciously skipped).
"""

import os
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

# intentionally not exposed to python
NOT_BOUND = {
    "b2SetAllocator": "memory allocation hooks make no sense from python",
    "b2SetAssertCallback": "an assert callback would run with box2d in an invalid state",
    "b2InternalAssert": "internal",
    "b2GetMillisecondsAndReset": "needs an in/out pointer; get_ticks + get_milliseconds cover it",
    "b2Hash": "internal hashing helper",
    "b2IsValidPos": "only differs from is_valid_vec2 in double precision builds",
    "b2IsValidWorldTransform": "only differs from is_valid_transform in double precision builds",
    "b2DefaultDebugDraw": "used by the DebugDraw constructor",
    "b2DestroyWorld": "WorldView.destroy",
    "b2DestroyBody": "Body.destroy",
    "b2DestroyShape": "Shape.destroy",
    "b2DestroyChain": "Chain.destroy",
    "b2DestroyJoint": "Joint.destroy",
}


def box2d_include_dirs():
    candidates = []
    if os.environ.get("CONDA_PREFIX"):
        candidates.append(Path(os.environ["CONDA_PREFIX"]) / "include" / "box2d")
    candidates.append(REPO / "build" / "_deps" / "box2d-src" / "include" / "box2d")
    return [c for c in candidates if (c / "box2d.h").exists()]


def public_functions(include_dir):
    names = set()
    for header in include_dir.glob("*.h"):
        text = header.read_text()
        names |= set(re.findall(r"B2_API\s+[^;(]*?\b(b2\w+)\s*\(", text))
    return names


def binding_sources():
    files = list((REPO / "src" / "bind").glob("*.cpp")) + list((REPO / "src" / "bind").glob("*.hpp"))
    files += list((REPO / "include" / "pyb2d3").rglob("*.hpp"))
    return "\n".join(f.read_text() for f in files)


@pytest.mark.skipif(not box2d_include_dirs(), reason="box2d headers not found")
def test_all_public_functions_are_bound():
    functions = public_functions(box2d_include_dirs()[0])
    assert len(functions) > 400  # sanity check of the header parsing
    sources = binding_sources()
    missing = sorted(f for f in functions if f not in NOT_BOUND and not re.search(rf"\b{f}\b", sources))
    assert missing == [], f"{len(missing)} box2d functions are not bound: {missing}"


def test_not_bound_list_is_current():
    dirs = box2d_include_dirs()
    if not dirs:
        pytest.skip("box2d headers not found")
    stale = sorted(set(NOT_BOUND) - public_functions(dirs[0]))
    assert stale == [], f"NOT_BOUND lists functions that no longer exist: {stale}"
