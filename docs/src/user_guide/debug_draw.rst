Debug Draw
==========

Box2D can describe the world as drawing primitives. Subclass :class:`~pyb2d3.DebugDraw`,
implement the methods you need and pass it to ``world.draw``.

.. literalinclude:: ../../snippets/debug_draw.py
   :language: python

Methods
-------

All coordinates are world coordinates, colors are ``0xRRGGBB`` integers.

==============================================================  =========================================================
``draw_polygon(points, color)``                                 polygon outline, ``points`` is an ``(n, 2)`` array
``draw_solid_polygon(transform, points, radius, color)``        filled (rounded) polygon, ``points`` in the local frame
``draw_circle(center, radius, color)``                          circle outline
``draw_solid_circle(transform, radius, color)``                 filled circle centered at ``transform.p``
``draw_solid_capsule(p1, p2, radius, color)``                   filled capsule
``draw_segment(p1, p2, color)``                                 line
``draw_transform(transform)``                                   a coordinate frame
``draw_point(p, size, color)``                                  point, ``size`` in pixels
``draw_string(p, string, color)``                               text
``draw_aabb(aabb, color)``                                      bounding box
``begin_draw()`` / ``end_draw()``                               called around ``world.draw`` (``call_begin_end=False``
                                                                to skip)
==============================================================  =========================================================

Flags
-----

``drawing_bounds`` (only shapes inside are drawn), ``draw_shapes``, ``draw_joints``,
``draw_joint_extras``, ``draw_bounds``, ``draw_mass``, ``draw_body_names``, ``draw_contacts``,
``draw_contact_normals``, ``draw_contact_forces``, ``draw_friction_forces``,
``draw_contact_features``, ``draw_graph_colors``, ``draw_islands``, ``draw_anchor_a``,
``draw_chain_normals``, ``force_scale`` and ``joint_scale``.

Ready-made frontends (OpenGL, pygame, ...) are part of the :doc:`../sandbox`.
