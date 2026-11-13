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

Binary size
-----------

The batch API is generated at compile time and adds about 50 KB to the extension module. Build
with ``-DPYB2D3_BATCH_API=OFF`` to leave it out; ``b2d.WITH_BATCH_API`` tells whether a build
has it.
