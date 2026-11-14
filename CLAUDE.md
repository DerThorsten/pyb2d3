pyb2d3 are python bindings with nanobind for box2d >= 3

box2d 3 is a **C** library for 2D physics simulation. 
box2d 3 has this somewhat python-unfriendly API, so pyb2d3 is a thin wrapper around it to make it more pythonic.

The problem is, its all just free c functions like

b2Joint_GetConstraintForce(id)

where id ist an opaque handle to a joint.

## Architecture

- `include/pyb2d3/core/handle.hpp`: `pyb2d3::Handle<IdT>` base class for all id wrappers
  (id packing, validity, user data via `IdTraits`).
- `include/pyb2d3/wrapper_structs.hpp`: thin handle types (`Body`, `Shape` + subclasses,
  `Joint` + subclasses, `Chain`, `WorldView`, `Contact`). Only non 1:1 logic lives here.
- `include/pyb2d3/core/binder.hpp`: `pyb2d3::Binder` binds box2d C functions *directly*:
  `Binder(cls).rw<b2Body_GetMass, ...>("name")`, `.ro<...>`, `.def<b2Body_ApplyForce>(...)`.
  Do NOT write one-line forwarding member functions. With a batch class
  (`Binder(cls, batch_cls)`) the numpy batch versions (`Bodies`, `Shapes`, `Joints`) are
  generated automatically for array-friendly value types. `-DPYB2D3_BATCH_API=OFF` compiles them out.
- `src/bind/<domain>.cpp`: one binding file per domain (world, body, shape, chain, joint,
  joint_defs, defs, events, collision, math, vec2, dynamic_tree, recording, debug_draw, base),
  declared in `src/bind/bind.hpp`, registered in `src/bind/module.cpp`.
- `src/module/pyb2d3/__init__.py`: pure python conveniences (def factories, `World`,
  `BodyFactory`, `MouseDrag`, batch indexing, ...).
- Tests: `tests/test_<domain>.py`. `tests/test_api_coverage.py` fails if a public box2d
  function is neither bound nor listed in its `NOT_BOUND` table. `tests/test_samples.py` runs
  every registered sample headless and drives all of its widgets.
- `examples/` (not packages, put on `sys.path` by tests/docs/`examples/sandbox.py`): the
  sandbox core `pyb2d3_sandbox`, the frontends `pyb2d3_sandbox_opengl` / `pyb2d3_sandbox_pygame`
  (pygame also renders the docs videos), the samples `pyb2d3_samples` and in
  `pyb2d3_samples/box2d` the ports of box2d's sample browser (one module per `sample_*.cpp`).
- `pixi.toml` is the dev environment and task runner: `pixi run build|test|install|wheel|test-installed|docs|
  docs-quick|docs-serve|sandbox|sandbox-pygame|smoke-opengl|emscripten`. `smoke-opengl` runs every sample
  in the real OpenGL frontend (the headless tests draw with pygame, OpenGL needs a window).
- Docstrings are generated from box2d's `///` header comments: `pixi run docstrings`
  (scripts/generate_docstrings.py) writes `include/pyb2d3/generated/docstrings.hpp`
  (`docs::doc<&b2Fn>`, attached by `Binder`; direct `m.def(..., &b2Fn, ...)` bindings pass it as
  last argument) and `src/module/pyb2d3/_docstrings.py` (struct / field docs). Never edit them by
  hand; rerun after adding bindings (`tests/test_docstrings.py` checks they are current).
- No repetition: shared behaviour goes into base classes / binder helpers
  (e.g. `bind_spring`, `bind_limit`, `bind_motor` in `src/bind/joint.cpp`).


## Shell commands (for Claude)

This environment blocks reads outside the working directory and asks for
permission on any Bash command it cannot statically analyze. Therefore:

- Use literal absolute paths in Bash commands. Do not use shell variables
  (`S=...; cd $S`), `for` loops, or `$(...)` to build paths.
- Do not `cd` into computed directories; one command per target.
- Temporary files (e.g. cloned box2d sources for API diffs) go in the session
  scratchpad, addressed by literal absolute path.
- Change files only with the Edit / Write tools. Never `sed -i`, `awk`, `perl -i`
  or heredoc redirects to modify files (they cannot be checked, show no diff,
  and BSD sed on macOS silently ignores GNU syntax like `\b`).
- No process substitution `<(...)`, `$(...)`, or `;`/`&&` chains of several
  commands: one plain command per call.
- Don't read outside the repo (`~`, `which`, other envs) to discover the setup;
  ask the user instead.
- Build / test with pixi from the repo root: `pixi run build`, `pixi run test`,
  `pixi run python -m pytest tests/test_x.py ...`.
