import sys


from pyb2d3_sandbox import SampleBase,SampleRegistry,register_sample,registry  # noqa: F401


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

# category -> [(sample class, display name)], shown as groups in the sandbox
_categories = {
    "Games": [
        (TankSample, "Tank"),
        (AngryShapes, "Angry Shapes"),
        (Billiard, "Billiard"),
        (Minigolf, "Minigolf"),
        (CoupledMinigolf, "Coupled Minigolf"),
        (GooGameLevel1, "Goo Game"),
        (Jump, "Jump"),
    ],
    "Demos": [
        (Joints, "Joints"),
        (Ragdoll, "Ragdoll"),
        (NewtonsCradle, "Newton's Cradle"),
        (SoftBodies, "Soft Bodies"),
        (Shapes, "Shapes"),
        (ChainBuilder, "Chain Builder"),
        (Meteor, "Meteor"),
        (Tumbler, "Tumbler"),
        (Text, "Text"),
    ],
    "Queries": [
        (Raycast, "Raycast"),
        (CastRayCallback, "Cast Ray Callback"),
        (Mirror, "Mirror"),
    ],
}

for _category, _samples in _categories.items():
    for _cls, _name in _samples:
        register_sample(_category, _name)(_cls)

all_examples = [cls for samples in _categories.values() for cls, _ in samples]

del _category, _samples, _cls, _name

# ports of box2d's own samples (register themselves under box2d's category names)
from . import box2d


def iterate_module_classes(module):
    """Iterate over all classes in a module."""
    for name, obj in module.__dict__.items():
        # if the object is a class, check if it is a subclass of box2d.Sample and yield it
        if isinstance(obj, type) and issubclass(obj, SampleBase) and obj is not SampleBase:
            yield obj
        # if the object is a module, recursively iterate over its classes
        elif isinstance(obj, type(sys)) and obj.__name__.startswith(module.__name__):
            yield from iterate_module_classes(obj)


# get all classes from box2d and add them to all_examples
# itertate over all classes in the box2d module
for cls in iterate_module_classes(box2d):

    # only take those whoe are in the registry (i.e. those that have been registered with a category and name)
    if cls in registry:

        all_examples.append(cls)

print(f"Registered {len(all_examples)} examples in pyb2d3_samples (including box2d samples).")