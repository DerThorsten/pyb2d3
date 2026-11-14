Bodies
======

A :class:`~pyb2d3.Body` has a position, rotation and velocity. Its mass comes from the shapes
attached to it.

* **static** bodies never move (ground, walls),
* **kinematic** bodies move with a velocity you set and are not affected by forces,
* **dynamic** bodies are fully simulated.

.. literalinclude:: ../../snippets/bodies.py
   :language: python

Overview
--------

==============================  ==================================================================
Pose                            ``position``, ``rotation``, ``angle``, ``transform``,
                                ``set_transform(position, rotation)``,
                                ``set_target_transform(target, time_step)``
Frames                          ``local_point``, ``world_point``, ``local_vector``, ``world_vector``,
                                ``local_point_velocity``, ``world_point_velocity``
Velocity                        ``linear_velocity``, ``angular_velocity``, ``speed``
Forces                          ``apply_force``, ``apply_force_to_center``, ``apply_torque``,
                                ``apply_linear_impulse``, ``apply_linear_impulse_to_center``,
                                ``apply_angular_impulse``, ``clear_forces``
Mass                            ``mass``, ``rotational_inertia``, ``local_center``, ``world_center``,
                                ``mass_data``, ``update_mass_from_shapes()``
Behaviour                       ``type``, ``linear_damping``, ``angular_damping``, ``gravity_scale``,
                                ``bullet``, ``motion_locks``, ``fixed_rotation``, ``enabled``,
                                ``safety_factor``, ``contact_recycling_enabled``
Sleep                           ``awake``, ``sleep_enabled``, ``sleep_threshold``, ``wake_touching()``
Attached objects                ``shapes``, ``shape_count``, ``joints``, ``joint_count``,
                                ``contact_data``, ``create_shape(...)``, ``create_chain(...)``
Extents                         ``compute_bounds()``, ``min_extent``, ``max_extent``,
                                ``max_extent_from_origin``
==============================  ==================================================================

All of these are also available on many bodies at once, see :doc:`batch`.

Body definition
---------------

The fields of :class:`~pyb2d3.BodyDef`: ``type``, ``position``, ``rotation``,
``linear_velocity``, ``angular_velocity``, ``linear_damping``, ``angular_damping``,
``gravity_scale``, ``sleep_threshold``, ``safety_factor``, ``name``, ``user_data``,
``motion_locks`` (``fixed_rotation`` is a shorthand for ``motion_locks.angular_z``),
``enable_sleep``, ``is_awake``, ``is_bullet``, ``is_enabled``, ``allow_fast_rotation`` and
``enable_contact_recycling``.
