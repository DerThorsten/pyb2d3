import numpy as np  # type: ignore
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
    joint = NullJointDef()
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

    def draw_solid_polygon(self, transform, vertices, radius, color):
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

    AliceBlue = 0xF0F8FF
    AntiqueWhite = 0xFAEBD7
    Aquamarine = 0x7FFFD4
    Azure = 0xF0FFFF
    Beige = 0xF5F5DC
    Bisque = 0xFFE4C4
    Black = 0x000000
    BlanchedAlmond = 0xFFEBCD
    Blue = 0x0000FF
    BlueViolet = 0x8A2BE2
    Brown = 0xA52A2A
    Burlywood = 0xDEB887
    CadetBlue = 0x5F9EA0
    Chartreuse = 0x7FFF00
    Chocolate = 0xD2691E
    Coral = 0xFF7F50
    CornflowerBlue = 0x6495ED
    Cornsilk = 0xFFF8DC
    Crimson = 0xDC143C
    Cyan = 0x00FFFF
    DarkBlue = 0x00008B
    DarkCyan = 0x008B8B
    DarkGoldenrod = 0xB8860B
    DarkGray = 0xA9A9A9
    DarkGreen = 0x006400
    DarkKhaki = 0xBDB76B
    DarkMagenta = 0x8B008B
    DarkOliveGreen = 0x556B2F
    DarkOrange = 0xFF8C00
    DarkOrchid = 0x9932CC
    DarkRed = 0x8B0000
    DarkSalmon = 0xE9967A
    DarkSeaGreen = 0x8FBC8F
    DarkSlateBlue = 0x483D8B
    DarkSlateGray = 0x2F4F4F
    DarkTurquoise = 0x00CED1
    DarkViolet = 0x9400D3
    DeepPink = 0xFF1493
    DeepSkyBlue = 0x00BFFF
    DimGray = 0x696969
    DodgerBlue = 0x1E90FF
    Firebrick = 0xB22222
    FloralWhite = 0xFFFAF0
    ForestGreen = 0x228B22
    Gainsboro = 0xDCDCDC
    GhostWhite = 0xF8F8FF
    Gold = 0xFFD700
    Goldenrod = 0xDAA520
    Gray = 0xBEBEBE
    Gray1 = 0x1A1A1A
    Gray2 = 0x333333
    Gray3 = 0x4D4D4D
    Gray4 = 0x666666
    Gray5 = 0x7F7F7F
    Gray6 = 0x999999
    Gray7 = 0xB3B3B3
    Gray8 = 0xCCCCCC
    Gray9 = 0xE5E5E5
    Green = 0x00FF00
    GreenYellow = 0xADFF2F
    Honeydew = 0xF0FFF0
    HotPink = 0xFF69B4
    IndianRed = 0xCD5C5C
    Indigo = 0x4B0082
    Ivory = 0xFFFFF0
    Khaki = 0xF0E68C
    Lavender = 0xE6E6FA
    LavenderBlush = 0xFFF0F5
    LawnGreen = 0x7CFC00
    LemonChiffon = 0xFFFACD
    LightBlue = 0xADD8E6
    LightCoral = 0xF08080
    LightCyan = 0xE0FFFF
    LightGoldenrod = 0xEEDD82
    LightGoldenrodYellow = 0xFAFAD2
    LightGray = 0xD3D3D3
    LightGreen = 0x90EE90
    LightPink = 0xFFB6C1
    LightSalmon = 0xFFA07A
    LightSeaGreen = 0x20B2AA
    LightSkyBlue = 0x87CEFA
    LightSlateBlue = 0x8470FF
    LightSlateGray = 0x778899
    LightSteelBlue = 0xB0C4DE
    LightYellow = 0xFFFFE0
    LimeGreen = 0x32CD32
    Linen = 0xFAF0E6
    Magenta = 0xFF00FF
    Maroon = 0xB03060
    MediumAquamarine = 0x66CDAA
    MediumBlue = 0x0000CD
    MediumOrchid = 0xBA55D3
    MediumPurple = 0x9370DB
    MediumSeaGreen = 0x3CB371
    MediumSlateBlue = 0x7B68EE
    MediumSpringGreen = 0x00FA9A
    MediumTurquoise = 0x48D1CC
    MediumVioletRed = 0xC71585
    MidnightBlue = 0x191970
    MintCream = 0xF5FFFA
    MistyRose = 0xFFE4E1
    Moccasin = 0xFFE4B5
    NavajoWhite = 0xFFDEAD
    NavyBlue = 0x000080
    OldLace = 0xFDF5E6
    Olive = 0x808000
    OliveDrab = 0x6B8E23
    Orange = 0xFFA500
    OrangeRed = 0xFF4500
    Orchid = 0xDA70D6
    PaleGoldenrod = 0xEEE8AA
    PaleGreen = 0x98FB98
    PaleTurquoise = 0xAFEEEE
    PaleVioletRed = 0xDB7093
    PapayaWhip = 0xFFEFD5
    PeachPuff = 0xFFDAB9
    Peru = 0xCD853F
    Pink = 0xFFC0CB
    Plum = 0xDDA0DD
    PowderBlue = 0xB0E0E6
    Purple = 0xA020F0
    RebeccaPurple = 0x663399
    Red = 0xFF0000
    RosyBrown = 0xBC8F8F
    RoyalBlue = 0x4169E1
    SaddleBrown = 0x8B4513
    Salmon = 0xFA8072
    SandyBrown = 0xF4A460
    SeaGreen = 0x2E8B57
    Seashell = 0xFFF5EE
    Sienna = 0xA0522D
    Silver = 0xC0C0C0
    SkyBlue = 0x87CEEB
    SlateBlue = 0x6A5ACD
    SlateGray = 0x708090
    Snow = 0xFFFAFA
    SpringGreen = 0x00FF7F
    SteelBlue = 0x4682B4
    Tan = 0xD2B48C
    Teal = 0x008080
    Thistle = 0xD8BFD8
    Tomato = 0xFF6347
    Turquoise = 0x40E0D0
    Violet = 0xEE82EE
    VioletRed = 0xD02090
    Wheat = 0xF5DEB3
    White = 0xFFFFFF
    WhiteSmoke = 0xF5F5F5
    Yellow = 0xFFFF00
    YellowGreen = 0x9ACD32
    Box2DRed = 0xDC3132
    Box2DBlue = 0x30AEBF
    Box2DGreen = 0x8CC924
    Box2DYellow = 0xFFEE8C
