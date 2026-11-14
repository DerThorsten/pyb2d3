pyb2d3
======

Python bindings for `Box2D <https://box2d.org>`_ v3.2, the 2D physics engine.

* the complete public Box2D API, typed and Pythonic: properties instead of getter / setter
  functions, objects instead of ids
* a numpy batch API to simulate and read out thousands of bodies with a few calls
* snapshots, recording and deterministic replay
* a sandbox with OpenGL, pygame and Jupyter frontends to build interactive samples

.. code-block:: bash

    pip install pyb2d3

.. literalinclude:: snippets/quickstart.py
   :language: python

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   src/installation.rst
   src/user_guide/index.rst
   src/sandbox.rst
   src/api.rst
   src/samples/index.rst
   src/developer.rst
   src/about_the_docs.rst


.. include:: src/samples/sample_videos.rst
