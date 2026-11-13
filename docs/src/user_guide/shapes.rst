Shapes and Chains
=================

Shapes give bodies their geometry, mass and material. A body can have any number of shapes.

.. literalinclude:: ../../snippets/shapes.py
   :language: python

Geometry
--------

.. list-table::
   :header-rows: 1

   * - Geometry
     - Factory
     - Shape class
   * - :class:`~pyb2d3.Circle`
     - ``circle(center, radius)``
     - :class:`~pyb2d3.CircleShape`
   * - :class:`~pyb2d3.Capsule`
     - ``capsule(center1, center2, radius)``
     - :class:`~pyb2d3.CapsuleShape`
   * - :class:`~pyb2d3.Segment`
     - ``segment(point1, point2)``
     - :class:`~pyb2d3.SegmentShape`
   * - :class:`~pyb2d3.Polygon`
     - ``box(hx, hy, center, rotation, radius)``, ``polygon(points, radius, position, rotation)``
     - :class:`~pyb2d3.PolygonShape`
   * - :class:`~pyb2d3.ChainSegment`
     - ``chain_segment(segment, ghost1, ghost2)``, or created by chains
     - :class:`~pyb2d3.ChainSegmentShape`

Polygons are convex with at most ``b2d.MAX_POLYGON_VERTICES`` (8) vertices; ``polygon``
computes the convex hull of the given points. The lower level functions ``compute_hull``,
``make_polygon``, ``make_box``, ``make_offset_box``, ... are available as well.

Shape properties
----------------

``friction``, ``restitution``, ``density`` / ``set_density(d)``, ``surface_material``,
``user_material``, ``filter``, ``is_sensor``, the event flags (``contact_events_enabled``,
``sensor_events_enabled``, ``hit_events_enabled``, ``pre_solve_events_enabled``) and queries
like ``test_point``, ``cast_ray``, ``closest_point``, ``bounds`` and ``compute_mass_data()``.
``shape.body`` is the owning body, ``shape.cast()`` returns the typed shape.

Collision filtering
-------------------

Shapes collide when ``(a.category_bits & b.mask_bits) != 0`` and
``(b.category_bits & a.mask_bits) != 0``. Shapes with the same negative ``group_index`` never
collide, the same positive ``group_index`` always collide. For anything more complicated use a
custom filter callback (see :doc:`world`).

Chains
------

A chain is a sequence of one-sided segments, the best way to model terrain: bodies sliding
over it do not catch on the internal vertices. Segments collide only on their right side
(seen in the direction of the points), loops (``is_loop=True``) should therefore be
counter-clockwise for the inside and clockwise for the outside.

For open chains, Box2D needs "ghost" points before the first and after the last point. By
default they continue the first and last segment; set ``chain_def.ghost1`` /
``chain_def.ghost2`` to choose them explicitly.

Each segment can have its own material (``materials=[...]``, one per segment) or all share one
(``material=...``). :class:`~pyb2d3.PathBuilder` helps to build point lists from lines and arcs.

Low level collision
-------------------

Functions working on raw geometry, without a world, mirror Box2D's ``collision.h``:
``compute_*_mass``, ``compute_*_bounds``, ``point_in_*``, ``cast_ray_*``, ``cast_shape_*``,
``compute_shape_distance``, ``compute_time_of_impact``, the ``collide_*`` manifold functions and
:class:`~pyb2d3.DynamicTree`, Box2D's bounding volume hierarchy.
