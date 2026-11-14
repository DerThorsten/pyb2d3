Conventions
===========

pyb2d3 follows Box2D's C API closely, with a few rules that make it feel like Python.

From C functions to Python
--------------------------

Box2D's C API is a set of free functions operating on ids (``b2Body_GetPosition(bodyId)``).
In pyb2d3 the id is wrapped in a small object and the functions become its properties and
methods, named in ``snake_case``:

==========================================  ============================================
C                                           Python
==========================================  ============================================
``b2Body_GetPosition(id)``                  ``body.position``
``b2Body_SetLinearVelocity(id, v)``         ``body.linear_velocity = v``
``b2Body_IsAwake(id)`` / ``SetAwake``       ``body.awake``
``b2Body_ApplyForce(id, f, p, wake)``       ``body.apply_force(f, p, wake=True)``
``b2Shape_GetCircle(id)``                   ``circle_shape.circle``
``b2CreateRevoluteJoint(worldId, &def)``    ``world.create_revolute_joint(...)``
``b2World_CastRayClosest(id, o, t, f)``     ``world.cast_ray_closest(o, t, query_filter=f)``
==========================================  ============================================

* Getter / setter pairs are **properties**; everything that does something or takes
  arguments is a **method**.
* Functions returning several values through pointers return a **tuple**
  (e.g. ``joint.constraint_tuning``).
* Functions returning an id return the **typed Python object** (a ``CircleShape``, a
  ``RevoluteJoint``, ...), or ``None`` for an invalid id.

Handles
-------

:class:`~pyb2d3.Body`, :class:`~pyb2d3.Shape`, :class:`~pyb2d3.Joint`,
:class:`~pyb2d3.Chain` and :class:`~pyb2d3.WorldView` are cheap handles on a Box2D id. Several
Python objects may refer to the same Box2D object; they compare equal and have the same hash,
so they can be used as dict keys::

    same = b2d.Body(body.id)
    assert same == body

* ``.id`` is the id packed into an integer, ``.is_valid`` tells whether the object still exists.
* ``.user_data`` stores an integer (e.g. an index into your own data structures).
* ``.destroy()`` destroys the Box2D object; all handles on it become invalid.

Definitions
-----------

Box2D creates things from definition structs (``b2BodyDef``, ``b2ShapeDef``, ...). pyb2d3 has a
class for each (:class:`~pyb2d3.BodyDef`, :class:`~pyb2d3.ShapeDef`, ...) initialized with
Box2D's defaults, and a factory function taking the fields as keyword arguments::

    body_def = b2d.body_def(type=b2d.BodyType.DYNAMIC, position=(0, 2), linear_damping=0.1)
    shape_def = b2d.shape_def(density=1, material=b2d.surface_material(friction=0.5))

Creation functions accept the keyword arguments directly, too
(``world.create_dynamic_body(position=(0, 2))``). Every def has ``copy()`` and ``update(**kwargs)``.

Vectors and points
------------------

Wherever a 2d vector is expected, :class:`~pyb2d3.Vec2`, a tuple, a list or a length-2 numpy
array can be passed. Returned vectors are :class:`~pyb2d3.Vec2` objects, which behave like
sequences (``x, y = body.position``) and support arithmetic.

Functions taking *many* points (``compute_hull``, ``make_proxy``, ``chain_def(points=...)``, ...)
accept any iterable of such vectors. A C-contiguous ``float32`` numpy array of shape ``(n, 2)``
is used without a copy, other arrays are converted by numpy in one go, so for large data
numpy arrays are the fast path.

Colors are plain ``0xRRGGBB`` integers.
