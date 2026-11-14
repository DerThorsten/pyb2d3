Events and Contacts
===================

Box2D collects events during a step; read them after ``world.step``. They are valid until the
next step.

.. literalinclude:: ../../snippets/events.py
   :language: python

Event types
-----------

=====================================  ==========================================================  ==============================================
Method                                 Events                                                      Enabled by
=====================================  ==========================================================  ==============================================
``world.get_contact_events()``         ``begin_events()``, ``end_events()``, ``hit_events()``      shape def ``enable_contact_events``
                                                                                                   (default on), ``enable_hit_events``
``world.get_sensor_events()``          ``begin_events()``, ``end_events()``                        sensor shape ``is_sensor`` +
                                                                                                   ``enable_sensor_events`` on both shapes
``world.get_body_events()``            ``move_events()`` and the arrays ``bodies``,                bodies that moved
                                       ``transforms``, ``fell_asleep``
``world.get_joint_events()``           ``events()``                                                joint ``force_threshold`` / ``torque_threshold``
=====================================  ==========================================================  ==============================================

Hit events are reported when the approach speed exceeds ``world.hit_event_threshold``.

Contacts
--------

``body.contact_data`` and ``shape.contact_data`` list the current contacts with their
:class:`~pyb2d3.Manifold` (contact points, normal and impulses). Contact begin / end events
carry a :class:`~pyb2d3.Contact` handle; ``contact.data`` returns the same information while
the contact exists. Sensors list their overlaps in ``shape.sensor_overlaps``.

Rendering many bodies
---------------------

``world.get_body_events()`` only reports bodies that actually moved. Its array properties
``bodies`` (a :class:`~pyb2d3.Bodies` batch), ``transforms`` (``(n, 4)`` with
``x, y, cos, sin``) and ``fell_asleep`` are the cheapest way to sync a renderer with the
simulation.
