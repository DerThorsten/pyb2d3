World
=====

A :class:`~pyb2d3.World` owns all bodies, shapes and joints and advances the simulation.

.. literalinclude:: ../../snippets/quickstart.py
   :language: python

Creating a world
----------------

The keyword arguments of :class:`~pyb2d3.World` are the fields of :class:`~pyb2d3.WorldDef`
(``gravity``, ``enable_sleep``, ``contact_hertz``, ``maximum_linear_speed``, ...)::

    world = b2d.World(gravity=(0, -10), enable_sleep=True, user_data=42)

The world is destroyed when the Python object is garbage collected, or explicitly with
``world.destroy()``. :class:`~pyb2d3.WorldView` is a non-owning view of a world, e.g. the
one returned by ``body.world``.

Stepping
--------

``world.step(time_step, sub_step_count=4)`` advances the simulation. Use a fixed time step
(e.g. ``1 / 60``); more sub-steps make the simulation stiffer and more accurate. The GIL is
released while stepping.

Settings and statistics
-----------------------

World settings are properties that can be changed at any time::

    world.gravity = (0, -5)
    world.sleeping_enabled = False
    world.continuous_enabled = True
    world.restitution_threshold = 1.0
    world.max_linear_speed = 100
    world.set_contact_tuning(hertz=30, damping_ratio=10, push_speed=3)

Statistics: ``world.awake_body_count``, ``world.counters``, ``world.profile``,
``world.bounds`` and ``world.state_hash``, a hash of the full simulation state (useful to
check determinism).

Multithreading
--------------

Box2D can solve large worlds on several threads. Pass a :class:`~pyb2d3.ThreadPool`::

    pool = b2d.ThreadPool()          # all cores, or ThreadPool(n)
    world = b2d.World(gravity=(0, -10), thread_pool=pool)

Callbacks during the step
-------------------------

Python callbacks can customize the simulation. They run *during* ``world.step`` (possibly on
a worker thread; they take the GIL), so they slow down stepping. Exceptions raised in them
cannot propagate through Box2D and are reported via :func:`sys.unraisablehook`.

* ``world.set_custom_filter_callback(fn)``: ``fn(shape_a, shape_b) -> bool`` decides whether
  two shapes collide. Only called for shapes created with ``enable_custom_filtering=True``.
* ``world.set_pre_solve_callback(pre_solve=fn)``: ``fn(shape_a, shape_b, manifold)`` for shapes
  with ``enable_pre_solve_events=True``. ``pre_continuous`` can be set the same way.
* ``world.set_friction_callback(fn)`` / ``world.set_restitution_callback(fn)``: mixing rules
  ``fn(value_a, material_a, value_b, material_b) -> float``, where ``material_*`` is the
  ``user_material_id`` of the shapes' surface materials.

Pass ``None`` to remove a callback.

.. warning::

   The friction and restitution callbacks are **shared by all worlds**. Box2D installs them per
   world but calls them without any context (not even the world), so pyb2d3 keeps a single
   python callback for all worlds:

   * setting a callback on one world replaces it for every world that has one installed,
   * clearing it (``None``) on one world makes those worlds fall back to Box2D's default rules
     (friction ``sqrt(a * b)``, restitution ``max(a, b)``).

   Clear the callbacks when you are done with a world (e.g. at the end of a sample). If
   different worlds need different rules, encode the world in ``user_material_id`` and
   branch on it inside the one callback.

Units
-----

Box2D works in meters, kilograms and seconds and is tuned for objects between 0.1 and 10
meters. If your game uses other units (e.g. pixels), call
``b2d.set_length_units_per_meter(...)`` once, before creating any world.
