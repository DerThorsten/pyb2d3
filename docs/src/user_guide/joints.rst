Joints
======

Joints constrain two bodies relative to each other.

.. literalinclude:: ../../snippets/joints.py
   :language: python

Joint types
-----------

=====================================  ============================================================
Class                                  Purpose
=====================================  ============================================================
:class:`~pyb2d3.RevoluteJoint`         hinge, optional spring, limit and motor
:class:`~pyb2d3.PrismaticJoint`        slider along an axis, optional spring, limit and motor
:class:`~pyb2d3.WheelJoint`            vehicle wheel: suspension spring along an axis + rotation
:class:`~pyb2d3.DistanceJoint`         keeps a distance, optional spring, limit and motor
:class:`~pyb2d3.WeldJoint`             glues two bodies, optionally soft
:class:`~pyb2d3.MotorJoint`            drives a body towards a target pose / velocity
:class:`~pyb2d3.MoverJoint`            velocity control for character movers
:class:`~pyb2d3.PogoJoint`             ground spring for character movers
:class:`~pyb2d3.FilterJoint`           only disables collision between two bodies
=====================================  ============================================================

Each type has a definition class (:class:`~pyb2d3.RevoluteJointDef`, ...), a factory
(``b2d.revolute_joint_def(...)``) and a creation method on the world
(``world.create_revolute_joint(...)``); ``world.create_joint(def)`` works for all of them.

Common properties
-----------------

All definitions share the fields of :class:`~pyb2d3.JointDef` (available directly on every
def, or via ``def.base``): ``body_a``, ``body_b``, ``local_frame_a``, ``local_frame_b``,
``collide_connected``, ``force_threshold``, ``torque_threshold``, ``constraint_hertz``,
``constraint_damping_ratio``, ``draw_scale`` and ``user_data``.

All joints have ``body_a``, ``body_b``, ``local_frame_a/b``, ``collide_connected``,
``constraint_force``, ``constraint_torque``, ``linear_separation``, ``angular_separation``,
``set_constraint_tuning()``, ``force_threshold`` / ``torque_threshold`` (see joint events in
:doc:`events`), ``wake_bodies()`` and ``destroy()``.

Joints with springs, limits and motors share the same names:

* spring: ``spring_enabled``, ``spring_hertz``, ``spring_damping_ratio``
* limit: ``limit_enabled``, ``set_limits(lower, upper)``, ``lower_limit``, ``upper_limit``
* motor: ``motor_enabled``, ``target_motor_speed``, ``max_motor_force`` / ``max_motor_torque``,
  ``current_motor_force`` / ``current_motor_torque``

Local frames
------------

A joint connects a frame on body A with a frame on body B. The frame origin is the anchor
point; ``local_anchor_a`` / ``local_anchor_b`` are shorthands for ``local_frame_a.p`` /
``local_frame_b.p``. The frame rotation defines the reference angle (revolute, weld) and the
axis (prismatic and wheel joints move along the x-axis of frame A).

Mouse dragging
--------------

:class:`~pyb2d3.MouseDrag` lets the user drag bodies around, the way Box2D's own samples do it:
a kinematic body follows the cursor and pulls the grabbed body with a motor joint. Call
``begin(point)`` on mouse down, ``update(point)`` on mouse move, ``step(time_step)`` before every
world step and ``end()`` on mouse up. ``hertz``, ``damping_ratio`` and ``force_scale`` (the
maximum force as a multiple of the body's weight) tune the feel.
