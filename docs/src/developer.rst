Developer Guide
===============

Building from source
--------------------

The development environment (compilers, box2d, nanobind, test, docs and sandbox dependencies)
and the common commands are defined in ``pixi.toml``:

.. code-block:: bash

    pixi run build            # build in place: copies _pyb2d3 into src/module/pyb2d3
    pixi run test             # build + run the tests (they pick up the in-place build)
    pixi run install          # build with pip and install the package into the environment
    pixi run test-installed   # install + run the tests against the installed package
    pixi run wheel            # build a wheel with pip into dist/
    pixi run docs-quick       # docs without the sample videos (docs/_build/html)
    pixi run docs             # docs incl. the sample videos (rendered with pygame)
    pixi run docs-serve       # serve the built docs on localhost and open the browser
    pixi run sandbox          # browse the samples (OpenGL), sandbox-pygame for pygame
    pixi run smoke-opengl     # run every sample a few frames in the OpenGL frontend
    pixi run emscripten       # build the emscripten-forge package (emscripten-forge/6x)

``pixi shell`` opens a shell in the environment, e.g. to run ``pytest -k joints`` directly.
The in-place build directory is ``.pixi/build``.

CMake options:

=========================  ======================================================================
``FETCH_BOX2D``            download and build box2d (``ON``) or use an installed one (``OFF``)
``PYB2D3_BATCH_API``       build the numpy batch API (default ``ON``, about 50 KB)
``PYB2D3_NO_THREADING``    disable the thread pool (e.g. for emscripten)
=========================  ======================================================================

nanobind is located through the Python interpreter, ``-Dnanobind_DIR`` is not needed.

Architecture
------------

Box2D's C API consists of free functions on opaque ids. The bindings wrap the ids in small
handle types and bind the C functions **directly**, without writing a C++ method for each:

``include/pyb2d3/core/handle.hpp``
    ``pyb2d3::Handle<IdT>``: base class of all id wrappers (packing ids into integers, validity,
    user data via ``IdTraits``).

``include/pyb2d3/wrapper_structs.hpp``
    The handle types ``Body``, ``Shape`` (+ one subclass per geometry), ``Joint`` (+ one subclass
    per joint type), ``Chain``, ``WorldView`` and ``Contact``. Only logic that is not a 1:1
    forward of a C function lives here.

``include/pyb2d3/core/binder.hpp``
    ``pyb2d3::Binder`` turns C functions into properties and methods::

        Binder(cls)
            .ro<b2Body_GetMass>("mass")
            .rw<b2Body_GetLinearDamping, b2Body_SetLinearDamping>("linear_damping")
            .def<b2Body_ApplyTorque>("apply_torque", nb::arg("torque"), nb::arg("wake") = true);

    Given a batch class (``Binder(cls, batch_cls)``), every property and method with
    array-friendly types is mirrored on the batch class at compile time (``batch_value<T>``
    describes how a type maps onto an array row).

``include/pyb2d3/core/points.hpp``
    The ``Points`` argument type: any iterable of points, with a zero copy path for numpy.

``include/pyb2d3/py_converter.hpp``
    Type casters between Box2D ids and the typed Python objects.

``src/bind/<domain>.cpp``
    One binding file per domain (``world``, ``body``, ``shape``, ``chain``, ``joint``,
    ``joint_defs``, ``defs``, ``events``, ``collision``, ``math``, ``vec2``, ``dynamic_tree``,
    ``recording``, ``debug_draw``, ``base``), registered in ``src/bind/module.cpp``.
    Behaviour shared by several classes lives in one helper (e.g. ``bind_spring``,
    ``bind_limit`` and ``bind_motor`` in ``joint.cpp``).

``src/module/pyb2d3/__init__.py``
    Pure Python conveniences: def factories, ``World``, ``BodyFactory``, ``MouseDrag``, batch
    indexing, geometry helpers.

``examples/``
    Not part of the package: the sandbox core (``pyb2d3_sandbox``), its frontends
    (``pyb2d3_sandbox_opengl``, ``pyb2d3_sandbox_pygame``), the samples (``pyb2d3_samples``,
    with the ports of Box2D's own samples in ``pyb2d3_samples/box2d``) and the launcher
    ``sandbox.py``.

Releasing
---------

The ``wheels`` workflow (``.github/workflows/publish.yaml``) builds and tests the wheels
(Linux x86_64 / aarch64, Windows, macOS arm64; one stable ABI wheel per platform for
CPython 3.12+) and the sdist on every pull request and on ``main``. To publish:

1. bump ``version`` in ``pyproject.toml`` and merge,
2. push a matching tag: ``git tag v0.12.0 && git push origin v0.12.0``.

The upload job checks that the tag matches the version and publishes to PyPI via trusted
publishing (GitHub environment ``pypi``).

Docstrings
----------

The docstrings are generated from Box2D's own ``///`` header comments by
``scripts/generate_docstrings.py`` (``pixi run docstrings``), with the C names translated to
pyb2d3 names (``b2Body_GetMass`` → ``Body.mass``, ``b2BodyDef::gravityScale`` →
``BodyDef.gravity_scale``) and ``@param`` / ``@return`` / ``@note`` turned into ``Args:`` /
``Returns:`` / ``Note:`` sections:

* ``include/pyb2d3/generated/docstrings.hpp``: ``pyb2d3::docs::doc<&b2Fn>`` per bound function.
  ``Binder`` attaches it automatically, direct bindings pass it as last argument
  (``m.def("make_rot", &b2MakeRot, nb::arg("radians"), docs::doc<&b2MakeRot>)``).
* ``src/module/pyb2d3/_docstrings.py``: docs of the bound structs and their fields, applied to
  the classes and properties on import.

Both are committed. ``tests/test_docstrings.py`` fails if they are out of date, i.e. after
adding bindings or updating Box2D, rerun ``pixi run docstrings``.

Adding bindings
---------------

1. Find the domain file in ``src/bind`` and add a line to the ``Binder`` chain (``ro``, ``rw`` or
   ``def``). A lambda on ``binder.cls()`` is only needed when the C function does not map 1:1
   (output pointers, arrays, callbacks).
2. Add a test to the matching ``tests/test_<domain>.py``.
3. Run ``pixi run docstrings`` so the new binding gets Box2D's documentation.

Tests
-----

``tests/test_<domain>.py`` test the bindings domain by domain, ``tests/test_samples.py`` runs
all sample scenes, ``tests/test_docs.py`` executes every documentation snippet.

``tests/test_api_coverage.py`` parses the Box2D headers and fails if a public function is
neither used by the bindings nor listed (with a reason) in its ``NOT_BOUND`` table. After a
Box2D update it lists exactly what is missing.
