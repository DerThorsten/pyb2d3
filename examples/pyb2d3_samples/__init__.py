"""The pyb2d3 samples. Each sample registers itself with ``@register_sample(category, name)``;
the import order below is the order of the sample browser (the first sample is the one a
sandbox starts with when no sample is given)."""

# ruff: noqa: E402, F401
import importlib.util

from pyb2d3_sandbox import registry

# Demos
from . import ragdoll, rube_goldberg, joints, newtons_cradle, soft_bodies, shapes
from . import chain_builder, meteor, tumbler

if importlib.util.find_spec("PIL"):  # pillow is not installed in the web sandbox
    from . import text

# Games
from . import tank, angry_shapes, billiard, minigolf, coupled_minigolf, goo_game, jump
from . import bridge_builder

# Queries
from . import raycast, cast_ray_callback, mirror

# Batch API
from . import batch_swarm, batch_nbody, batch_fountain, batch_vs_loop, batch_maxwell_demon
from . import batch_many_shapes

# Agents
from . import batch_boids, batch_predator_prey, batch_epidemic

# Granular
from . import batch_hourglass, batch_galton, batch_brazil_nut, batch_earthquake

# Fluids & Matter
from . import batch_dam_break, batch_dam_break_balls, batch_phase, batch_ferrofluid
from . import batch_snow_globe, batch_rain

# Fields & Space
from . import batch_galaxies, batch_black_hole, batch_portals, batch_fireworks

# Playground: the starting point for your own sample (edit it in the browser sandbox)
from . import my_sample

# ports of box2d's own samples
from . import box2d_samples

# every registered sample (incl. the box2d ports), in browser order
all_examples = [entry.cls for entry in registry]
