from pyb2d3_sandbox import register_sample, registry


from .mirror import Mirror
from .newtons_cradle import NewtonsCradle
from .raycast import Raycast
from .tumbler import Tumbler
from .jump import Jump
from .soft_bodies import SoftBodies
from .shapes import Shapes
from .coupled_minigolf import CoupledMinigolf
from .joints import Joints
from .goo_game import Level1 as GooGameLevel1
from .chain_builder import ChainBuilder
from .billiard import Billiard
from .meteor import Meteor
from .ragdoll import Ragdoll
from .cast_ray_callback import CastRayCallback
from .text import Text
from .minigolf import Minigolf
from .angry_shapes import AngryShapes
from .tank import TankSample
from .rube_goldberg import RubeGoldberg
from .batch_swarm import BatchSwarm
from .batch_nbody import BatchNBody
from .batch_fountain import BatchFountain
from .batch_vs_loop import BatchVsLoop
from .batch_hourglass import BatchHourglass
from .batch_galton import BatchGalton
from .batch_brazil_nut import BatchBrazilNut
from .batch_earthquake import BatchEarthquake
from .my_sample import MySample
from .batch_many_shapes import BatchManyShapes
from .batch_dam_break import BatchDamBreak
from .batch_dam_break_balls import BatchDamBreakBalls
from .batch_phase import BatchPhaseTransitions
from .batch_ferrofluid import BatchFerrofluid
from .batch_snow_rain import BatchSnowRain
from .batch_boids import BatchBoids
from .batch_predator_prey import BatchPredatorPrey
from .batch_epidemic import BatchEpidemic
from .batch_maxwell_demon import BatchMaxwellDemon
from .batch_galaxies import BatchGalaxyCollision
from .batch_black_hole import BatchBlackHole
from .batch_portals import BatchPortals
from .batch_fireworks import BatchFireworks

# category -> [(sample class, display name)], shown as groups in the sandbox
_categories = {
    # the first sample is the one a sandbox starts with (no sample given)
    "Demos": [
        (Ragdoll, "Ragdoll"),
        (RubeGoldberg, "Rube Goldberg"),
        (Joints, "Joints"),
        (NewtonsCradle, "Newton's Cradle"),
        (SoftBodies, "Soft Bodies"),
        (Shapes, "Shapes"),
        (ChainBuilder, "Chain Builder"),
        (Meteor, "Meteor"),
        (Tumbler, "Tumbler"),
        (Text, "Text"),
    ],
    "Games": [
        (TankSample, "Tank"),
        (AngryShapes, "Angry Shapes"),
        (Billiard, "Billiard"),
        (Minigolf, "Minigolf"),
        (CoupledMinigolf, "Coupled Minigolf"),
        (GooGameLevel1, "Goo Game"),
        (Jump, "Jump"),
    ],
    "Queries": [
        (Raycast, "Raycast"),
        (CastRayCallback, "Cast Ray Callback"),
        (Mirror, "Mirror"),
    ],
    "Batch API": [
        (BatchSwarm, "Swarm"),
        (BatchNBody, "N-Body Gravity"),
        (BatchFountain, "Fountain"),
        (BatchVsLoop, "Loop vs Batch"),
        (BatchMaxwellDemon, "Maxwell's Demon"),
        (BatchManyShapes, "Many Shapes"),
    ],
    "Agents": [
        (BatchBoids, "Boids Flocking"),
        (BatchPredatorPrey, "Predator & Prey"),
        (BatchEpidemic, "Epidemic (SIR)"),
    ],
    "Granular": [
        (BatchHourglass, "Hourglass"),
        (BatchGalton, "Galton Board"),
        (BatchBrazilNut, "Brazil Nut Shaker"),
        (BatchEarthquake, "Earthquake City"),
    ],
    "Fluids & Matter": [
        (BatchDamBreak, "Dam Break"),
        (BatchDamBreakBalls, "Dam Break (Balls)"),
        (BatchPhaseTransitions, "Phase Transitions"),
        (BatchFerrofluid, "Ferrofluid"),
        (BatchSnowRain, "Snow Globe & Rain"),
    ],
    "Fields & Space": [
        (BatchGalaxyCollision, "Galaxy Collision"),
        (BatchBlackHole, "Black Hole"),
        (BatchPortals, "Portals"),
        (BatchFireworks, "Fireworks"),
    ],
    # the starting point for your own sample (edit it in the browser sandbox)
    "Playground": [
        (MySample, "My Sample"),
    ],
}

for _category, _samples in _categories.items():
    for _cls, _name in _samples:
        register_sample(_category, _name)(_cls)

del _category, _samples, _cls, _name

# ports of box2d's own samples (register themselves under box2d's category names)
from . import box2d_samples  # noqa: E402, F401

# every registered sample (incl. the box2d ports), in browser order
all_examples = [entry.cls for entry in registry]
