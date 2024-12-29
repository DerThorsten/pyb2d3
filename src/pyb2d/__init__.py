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



def _extend_def_classes():
    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    WorldDef.update = update
    BodyDef.update = update
    ShapeDef.update = update
    
_extend_def_classes()
del _extend_def_classes





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


def make_filter(**kwargs):
    filter = Filter()
    for k, v in kwargs.items():
        setattr(filter, k, v)
    return filter


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

def capsule(**kwargs):
    c = Capsule()
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

def null_joint_def(**kwargs):
    joint =	NullJointDef()
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
    elif isinstance(joint_def, WheelJointDef):
        return create_wheel_joint(world_id, joint_def)
    elif isinstance(joint_def, NullJointDef):
        return create_null_joint(world_id, joint_def)
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




from enum import Enum




class HexColor(Enum):

    AliceBlue = 0xf0f8ff
    AntiqueWhite = 0xfaebd7
    Aquamarine = 0x7fffd4
    Azure = 0xf0ffff
    Beige = 0xf5f5dc
    Bisque = 0xffe4c4
    Black = 0x000000
    BlanchedAlmond = 0xffebcd
    Blue = 0x0000ff
    BlueViolet = 0x8a2be2
    Brown = 0xa52a2a
    Burlywood = 0xdeb887
    CadetBlue = 0x5f9ea0
    Chartreuse = 0x7fff00
    Chocolate = 0xd2691e
    Coral = 0xff7f50
    CornflowerBlue = 0x6495ed
    Cornsilk = 0xfff8dc
    Crimson = 0xdc143c
    Cyan = 0x00ffff
    DarkBlue = 0x00008b
    DarkCyan = 0x008b8b
    DarkGoldenrod = 0xb8860b
    DarkGray = 0xa9a9a9
    DarkGreen = 0x006400
    DarkKhaki = 0xbdb76b
    DarkMagenta = 0x8b008b
    DarkOliveGreen = 0x556b2f
    DarkOrange = 0xff8c00
    DarkOrchid = 0x9932cc
    DarkRed = 0x8b0000
    DarkSalmon = 0xe9967a
    DarkSeaGreen = 0x8fbc8f
    DarkSlateBlue = 0x483d8b
    DarkSlateGray = 0x2f4f4f
    DarkTurquoise = 0x00ced1
    DarkViolet = 0x9400d3
    DeepPink = 0xff1493
    DeepSkyBlue = 0x00bfff
    DimGray = 0x696969
    DodgerBlue = 0x1e90ff
    Firebrick = 0xb22222
    FloralWhite = 0xfffaf0
    ForestGreen = 0x228b22
    Gainsboro = 0xdcdcdc
    GhostWhite = 0xf8f8ff
    Gold = 0xffd700
    Goldenrod = 0xdaa520
    Gray = 0xbebebe
    Gray1 = 0x1a1a1a
    Gray2 = 0x333333
    Gray3 = 0x4d4d4d
    Gray4 = 0x666666
    Gray5 = 0x7f7f7f
    Gray6 = 0x999999
    Gray7 = 0xb3b3b3
    Gray8 = 0xcccccc
    Gray9 = 0xe5e5e5
    Green = 0x00ff00
    GreenYellow = 0xadff2f
    Honeydew = 0xf0fff0
    HotPink = 0xff69b4
    IndianRed = 0xcd5c5c
    Indigo = 0x4b0082
    Ivory = 0xfffff0
    Khaki = 0xf0e68c
    Lavender = 0xe6e6fa
    LavenderBlush = 0xfff0f5
    LawnGreen = 0x7cfc00
    LemonChiffon = 0xfffacd
    LightBlue = 0xadd8e6
    LightCoral = 0xf08080
    LightCyan = 0xe0ffff
    LightGoldenrod = 0xeedd82
    LightGoldenrodYellow = 0xfafad2
    LightGray = 0xd3d3d3
    LightGreen = 0x90ee90
    LightPink = 0xffb6c1
    LightSalmon = 0xffa07a
    LightSeaGreen = 0x20b2aa
    LightSkyBlue = 0x87cefa
    LightSlateBlue = 0x8470ff
    LightSlateGray = 0x778899
    LightSteelBlue = 0xb0c4de
    LightYellow = 0xffffe0
    LimeGreen = 0x32cd32
    Linen = 0xfaf0e6
    Magenta = 0xff00ff
    Maroon = 0xb03060
    MediumAquamarine = 0x66cdaa
    MediumBlue = 0x0000cd
    MediumOrchid = 0xba55d3
    MediumPurple = 0x9370db
    MediumSeaGreen = 0x3cb371
    MediumSlateBlue = 0x7b68ee
    MediumSpringGreen = 0x00fa9a
    MediumTurquoise = 0x48d1cc
    MediumVioletRed = 0xc71585
    MidnightBlue = 0x191970
    MintCream = 0xf5fffa
    MistyRose = 0xffe4e1
    Moccasin = 0xffe4b5
    NavajoWhite = 0xffdead
    NavyBlue = 0x000080
    OldLace = 0xfdf5e6
    Olive = 0x808000
    OliveDrab = 0x6b8e23
    Orange = 0xffa500
    OrangeRed = 0xff4500
    Orchid = 0xda70d6
    PaleGoldenrod = 0xeee8aa
    PaleGreen = 0x98fb98
    PaleTurquoise = 0xafeeee
    PaleVioletRed = 0xdb7093
    PapayaWhip = 0xffefd5
    PeachPuff = 0xffdab9
    Peru = 0xcd853f
    Pink = 0xffc0cb
    Plum = 0xdda0dd
    PowderBlue = 0xb0e0e6
    Purple = 0xa020f0
    RebeccaPurple = 0x663399
    Red = 0xff0000
    RosyBrown = 0xbc8f8f
    RoyalBlue = 0x4169e1
    SaddleBrown = 0x8b4513
    Salmon = 0xfa8072
    SandyBrown = 0xf4a460
    SeaGreen = 0x2e8b57
    Seashell = 0xfff5ee
    Sienna = 0xa0522d
    Silver = 0xc0c0c0
    SkyBlue = 0x87ceeb
    SlateBlue = 0x6a5acd
    SlateGray = 0x708090
    Snow = 0xfffafa
    SpringGreen = 0x00ff7f
    SteelBlue = 0x4682b4
    Tan = 0xd2b48c
    Teal = 0x008080
    Thistle = 0xd8bfd8
    Tomato = 0xff6347
    Turquoise = 0x40e0d0
    Violet = 0xee82ee
    VioletRed = 0xd02090
    Wheat = 0xf5deb3
    White = 0xffffff
    WhiteSmoke = 0xf5f5f5
    Yellow = 0xffff00
    YellowGreen = 0x9acd32
    Box2DRed = 0xdc3132
    Box2DBlue = 0x30aebf
    Box2DGreen = 0x8cc924
    Box2DYellow = 0xffee8c
