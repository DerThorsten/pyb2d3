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
from .billard import Billard
from .meteor import Meteor
from .ragdoll import Ragdoll
from .cast_ray_callback import CastRayCallback
from .text import Text

all_examples = [
    Ragdoll,
    Meteor,
    Mirror,
    NewtonsCradle,
    Raycast,
    Tumbler,
    Jump,
    SoftBodies,
    Shapes,
    CoupledMinigolf,
    Joints,
    GooGameLevel1,
    ChainBuilder,
    Billard,
    CastRayCallback,
    Text,
]
