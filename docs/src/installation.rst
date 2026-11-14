Installation
============

pyb2d3 is published on PyPI and conda-forge.

.. code-block:: bash

    pip install pyb2d3

.. code-block:: bash

    conda install -c conda-forge pyb2d3    # or mamba / micromamba / pixi add pyb2d3

The only runtime dependency is numpy.

Sandbox and samples
-------------------

The interactive sandbox, its OpenGL and pygame frontends and the samples are not packages,
they live in the ``examples`` directory of the repository. Run them from a checkout with
`pixi <https://pixi.sh>`_:

.. code-block:: bash

    git clone https://github.com/derthorsten/pyb2d3.git
    cd pyb2d3
    pixi run sandbox                     # OpenGL frontend
    pixi run sandbox "Joints/Ragdoll"    # start at a sample
    pixi run sandbox-pygame              # pygame frontend

See :doc:`sandbox`.

From source
-----------

See :doc:`developer`.
