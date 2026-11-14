"""Python ports of the samples of box2d's sample browser.

Ported from https://github.com/erincatto/box2d/tree/v3.2.0/samples

Copyright (c) 2022 Erin Catto, MIT license (see LICENSE in this directory).

Each module mirrors one ``sample_<category>.cpp`` file and registers its samples
under box2d's category names, so they show up grouped in the sandbox.
"""

from . import bodies  # noqa: F401
from . import joints  # noqa: F401
from . import shapes  # noqa: F401
from . import restitution  # noqa: F401
from . import stacking  # noqa: F401
from . import events  # noqa: F401
from . import continuous  # noqa: F401
from . import robustness  # noqa: F401
from . import collision  # noqa: F401
from . import geometry  # noqa: F401
from . import world  # noqa: F401
from . import issues  # noqa: F401
