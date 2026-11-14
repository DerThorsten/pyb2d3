Queries
=======

The world can be queried for shapes in a region, along a ray or along the path of a moving
shape.

.. literalinclude:: ../../snippets/queries.py
   :language: python

Overview
--------

.. list-table::
   :header-rows: 1

   * - Method
     - Callback
   * - ``overlap_aabb(aabb, callback)``
     - ``callback(shape)``: return ``False`` to stop
   * - ``overlap_shape(proxy, callback)``
     - ``callback(shape)``
   * - ``cast_ray(origin, translation, callback)``
     - ``callback(shape, point, normal, fraction)``: return the new max fraction
       (``-1`` ignore, ``0`` stop, ``fraction`` clip, ``1`` continue)
   * - ``cast_ray_closest(origin, translation)``
     - none, returns a :class:`~pyb2d3.RayResult`
   * - ``cast_shape(proxy, translation, callback)``
     - like ``cast_ray``
   * - ``cast_mover(mover, translation)``
     - none, returns the fraction the capsule can move
   * - ``collide_mover(mover, callback)``
     - ``callback(shape, plane_result)``
   * - ``shape_at_point(point)``, ``body_at_point(point)``
     - none, pass ``dynamic_only=True`` to skip static bodies

A callback returning ``None`` continues the query. All queries take a ``query_filter``
(:func:`pyb2d3.make_query_filter`) and an ``origin``: AABBs and proxies are relative to the
origin (``(0, 0)`` by default). Exceptions raised in a query callback stop the query and are
re-raised.

Shape proxies
-------------

A :class:`~pyb2d3.ShapeProxy` is a convex point cloud with a radius:
``b2d.make_proxy([(0, 0)], radius=0.5)`` is a circle, ``b2d.make_proxy(box_points)`` a box.

Character movers
----------------

``cast_mover`` and ``collide_mover`` together with ``solve_planes`` and ``clip_vector``
implement kinematic character controllers, see Box2D's
`character mover <https://box2d.org/posts/2025/01/character-mover/>`_ article.
