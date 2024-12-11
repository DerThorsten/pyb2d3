import numpy as np # type: ignore
from ._pyb2d import *
from .compound_shape import CompoundShape
from functools import partial
# Factory functions
def world_def(**kwargs):
    world = WorldDef()
    for k, v in kwargs.items():
        setattr(world, k, v)
    return world

def body_def(**kwargs):
    body = BodyDef()
    for k, v in kwargs.items():
        setattr(body, k, v)
    return body

# shorthand for body types
dynamic_body_def = partial(body_def, type=BodyType.DYNAMIC)
static_body_def = partial(body_def, type=BodyType.STATIC)
kinematic_body_def = partial(body_def, type=BodyType.KINEMATIC)


def create_body(world_id, *args, **kwargs):
    if body_def in kwargs:
        if len(kwargs) > 1 or len(args) > 0:
            raise ValueError("there should be only one body_def")
        bd = kwargs["body_def"]
    else:   
        if len(args) == 1:
                if not isinstance(args[0], BodyDef):
                    raise ValueError("args[0] should be a BodyDef")
                if len(kwargs) > 0:
                    raise ValueError("there should be only one body_def")
                bd = args[0]
        elif len(args) > 1:
            raise ValueError("there should be only one body_def")
        else:
            bd = body_def(**kwargs)
    return create_body_from_def(world_id, bd)

# shorthand for create_body
create_dynamic_body = partial(create_body, type=BodyType.DYNAMIC)
create_static_body = partial(create_body, type=BodyType.STATIC)
create_kinematic_body = partial(create_body, type=BodyType.KINEMATIC)


def shape_def(**kwargs):
    shape = ShapeDef()
    for k, v in kwargs.items():
        setattr(shape, k, v)
    return shape


def circle(**kwargs):
    c = Circle()
    for k, v in kwargs.items():
        setattr(c, k, v)
    return c



def create_shape(body_id, shape_def, shape):
    
    if isinstance(shape, Circle):
        return create_circle_shape(body_id, shape_def, shape)
    elif isinstance(shape, Polygon):
        return create_polygon_shape(body_id, shape_def, shape)
    elif isinstance(shape, Capsule):
        return create_capsule_shape(body_id, shape_def, shape)
    elif isinstance(shape, Segment):
        return create_segment_shape(body_id, shape_def, shape)  
    elif isinstance(shape, CompoundShape):
        shape_ids = []
        for sub_shape, sub_shape_def in shape.shapes:
            if sub_shape_def is None: 
                sub_shape_def = shape_def
            shape_id = create_shape(body_id, shape_def=sub_shape_def, shape=sub_shape)
            shape_ids.append(shape_id)
        return shape_ids
    else:
        raise ValueError(f"shape {shape} not recognized")






# joints
def revolute_joint_def(**kwargs):
    joint = RevoluteJointDef()
    for k, v in kwargs.items():
        setattr(joint, k, v)
    return joint

def distance_joint_def(**kwargs):
    joint = DistanceJointDef()
    for k, v in kwargs.items():
        setattr(joint, k, v)
    return joint

def prismatic_joint_def(**kwargs):
    joint = PrismaticJointDef()
    for k, v in kwargs.items():
        setattr(joint, k, v)
    return joint

def pulley_joint_def(**kwargs):
    joint = PulleyJointDef()
    for k, v in kwargs.items():
        setattr(joint, k, v)
    return joint

def gear_joint_def(**kwargs):
    joint = GearJointDef()
    for k, v in kwargs.items():
        setattr(joint, k, v)
    return joint

def wheel_joint_def(**kwargs):
    joint = WheelJointDef()
    for k, v in kwargs.items():
        setattr(joint, k, v)
    return joint


def create_joint(world_id, joint_def):
    if isinstance(joint_def, RevoluteJointDef):
        return create_revolute_joint(world_id, joint_def)
    elif isinstance(joint_def, DistanceJointDef):
        return create_distance_joint(world_id, joint_def)
    elif isinstance(joint_def, PrismaticJointDef):
        return create_prismatic_joint(world_id, joint_def)
    elif isinstance(joint_def, PulleyJointDef):
        return create_pulley_joint(world_id, joint_def)
    elif isinstance(joint_def, GearJointDef):
        return create_gear_joint(world_id, joint_def)
    elif isinstance(joint_def, WheelJointDef):
        return create_wheel_joint(world_id, joint_def)
    else:
        raise ValueError(f"joint {joint_def} not recognized")




class DebugDraw(DebugDrawBase):
    def __init__(self):
        super().__init__(self)


    def draw_polygon(self, vertices, color):
        pass

    def draw_solid_polygon(self, transform, vertices, radius,  color):
        pass

    def draw_circle(self, center, radius, color):
        pass

    def draw_solid_circle(self, transform, radius, color):
        pass
    
    def draw_solid_capsule(self, p1, p2, radius, color):
        pass

    def draw_segment(self, p1, p2, color):
        pass

    def draw_transform(self, transform):
        pass

    def draw_point(self, p, size, color):
        pass

    def draw_string(self, x, y, string):
        pass

    def draw_aabb(self, aabb, color):
        pass