Batch API (numpy)
=================

Every property access or method call crosses the Python / C++ boundary, which costs a few
hundred nanoseconds. For thousands of bodies per frame that adds up. The batch API does the
same work for many objects in **one** call and reads / writes numpy arrays.

.. literalinclude:: ../../snippets/batch.py
   :language: python

Batches
-------

:class:`~pyb2d3.Bodies`, :class:`~pyb2d3.Shapes` and :class:`~pyb2d3.Joints` are arrays of ids.
Create them from a list of objects or from an id array (``Bodies(ids)``); ``batch.ids`` is the
``uint64`` id array. Indexing works like numpy: an integer returns a single object, a slice,
index array or boolean mask returns a new batch.

What is batched
---------------

Every property and method of :class:`~pyb2d3.Body`, :class:`~pyb2d3.Shape` and
:class:`~pyb2d3.Joint` whose values are numbers, booleans, vectors, rotations or transforms is
available on the batch class under the same name:

* numbers / booleans / enums become ``(n,)`` arrays,
* vectors and rotations ``(n, 2)`` arrays (rotations as ``cos, sin``),
* transforms ``(n, 4)`` arrays (``x, y, cos, sin``).

Every argument can be a single value (broadcast to all objects) or one value per object.
Methods without a result return ``None``.

Creating batches
----------------

A batch can be built from any iterable of bodies, from an id array, one body at a time with
``append``, or from the results of a world query. The body move events already come as a
batch: ``world.get_body_events().bodies`` holds every body that moved during the last step.

.. literalinclude:: ../../snippets/batch_create.py
   :language: python

Reading and writing properties
------------------------------

Reading a property returns a fresh numpy array, writing one takes an array with one row per
body or a single value that is broadcast. ``set_transform`` takes rotations as ``(cos, sin)``
rows, the same layout ``bodies.rotation`` returns.

.. literalinclude:: ../../snippets/batch_properties.py
   :language: python

Calling methods
---------------

A batch method calls the box2d function once per body. Each argument is either one value per
body or a single value for all of them, and the two can be mixed freely in one call.

.. literalinclude:: ../../snippets/batch_methods.py
   :language: python

Transforming points
-------------------

``world_point``, ``local_point``, ``world_vector`` and ``local_vector`` transform one point
per body, or the same local point on every body. That is all a renderer needs to place sprites
or draw outlines, and ``local_point`` turns "which bodies are under the mouse" into a mask.

.. literalinclude:: ../../snippets/batch_transforms.py
   :language: python

Indexing, masks and iteration
-----------------------------

Batches index like numpy arrays. Sub batches share nothing but the ids, so selecting with a
mask and then writing a property only touches the selected bodies.

.. literalinclude:: ../../snippets/batch_indexing.py
   :language: python

Numpy math on whole worlds
--------------------------

With positions, velocities and masses as arrays, force fields and statistics are a few lines of
numpy: here a swirling radial field and the total kinetic energy of 1000 bodies.

.. literalinclude:: ../../snippets/batch_numpy_math.py
   :language: python

Shapes and joints
-----------------

:class:`~pyb2d3.Shapes` batch material properties and per-shape queries,
:class:`~pyb2d3.Joints` the runtime values every joint type has, e.g. the constraint forces.
Single items come back as their concrete type (``CapsuleShape``, ``RevoluteJoint``, ...).

.. literalinclude:: ../../snippets/batch_shapes_joints.py
   :language: python

When is it worth it?
--------------------

A single call into the extension is fast; what costs is the Python work around it: the loop,
temporary ``Vec2`` objects and arithmetic on Python floats. The batch API pays this once per
batch instead of once per body, so it wins as soon as you touch more than a handful of bodies
per frame (typically 10x to 30x for a few thousand bodies). For a few objects, or for logic that
differs per body, plain properties are just as good and easier to read.

.. literalinclude:: ../../snippets/batch_timing.py
   :language: python

The *Batch API* samples in the sandbox (``pixi run sandbox``) show it in action: swarms, an
n-body simulation, a particle fountain and a live loop vs. batch comparison.

Binary size
-----------

The batch API is generated at compile time and adds about 50 KB to the extension module. Build
with ``-DPYB2D3_BATCH_API=OFF`` to leave it out; ``b2d.WITH_BATCH_API`` tells whether a build
has it.
