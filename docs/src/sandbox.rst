Sandbox
=======

``pyb2d3_sandbox`` is a small framework to write interactive samples: it runs the simulation
loop, draws the world, handles mouse dragging, zooming and panning, and shows all registered
samples grouped by category. It lives in the ``examples`` directory of the repository (it is
not a package) and is split into the frontend independent core and frontends:

======================================  =========================================================
Module                                  Frontend
======================================  =========================================================
``pyb2d3_sandbox``                      the core: :class:`SampleBase`, the sample registry
``pyb2d3_sandbox_opengl``               OpenGL + Dear ImGui (sample browser, controls, debug UI)
``pyb2d3_sandbox_pygame``               pygame (PageUp / PageDown switches samples), video export
======================================  =========================================================

The default frontend is OpenGL if installed, otherwise pygame. Set
``PYB2D3_SANDBOX_DEFAULT_FRONTEND=opengl|pygame`` to choose explicitly.

Writing a sample
----------------

.. literalinclude:: ../snippets/sample.py
   :language: python

A sample subclasses ``SampleBase``, builds its scene in ``__init__`` (``self.world`` is
created by the base class) and returns the visible region from ``aabb()``. Optional hooks:

* ``pre_update(dt)`` / ``update(dt)`` / ``post_update(dt)``: around ``world.step``
* ``pre_debug_draw()`` / ``post_debug_draw()``: draw extra things with ``self.debug_draw``
* ``on_mouse_down`` / ``on_mouse_move`` / ``on_mouse_up`` / ``on_click`` / ``on_double_click`` /
  ``on_triple_click`` / ``on_mouse_wheel`` / ``on_key_down`` / ``on_key_up``
* ``is_done()``: end the run (used for videos and tests)
* ``Settings``: a dataclass with the sample's settings (``gravity`` by default)
* ``substeps``: sub-steps per world step for this sample (default: the frontend's setting),
  e.g. ``substeps = 8`` for long chains of joints

Dragging bodies with the mouse is built in (see :class:`pyb2d3.MouseDrag`), clicking on empty
space drags the camera. ``self.frontend.add_widget(...)`` adds sliders, checkboxes, buttons and
radio buttons (``pyb2d3_sandbox.widgets``) to frontends that support them.

Categories
----------

``@register_sample(category, name)`` adds a sample to the registry (the name defaults to the
class name). The OpenGL frontend shows the registry as a tree in its "Samples" panel, pygame
cycles through it with PageUp / PageDown.

``run_sample_browser(start=None)`` starts the browser, optionally with a ``"Category/Name"`` key
or a sample class; ``MySample.run()`` starts a single sample (the other registered samples
are still reachable). The bundled samples, including ports of Box2D's own sample browser
(grouped like there: Bodies, Joints, Shapes, Stacking, Events, Collision, ...), are browsed
with::

    pixi run sandbox                        # first sample
    pixi run sandbox "Games/Billiard"       # a specific one
    python examples/sandbox.py --list       # all sample keys

Testing samples
---------------

``tests/test_samples.py`` runs every registered sample in a headless frontend that fires
random mouse events; samples registered in ``pyb2d3_samples`` are tested automatically.
