import numpy as np
import random
import math
import sys
import os
from ._pyb2d3 import *  # noqa: F403
from . import _pyb2d3
from functools import partial, partialmethod
from enum import Enum
from contextlib import contextmanager
import importlib


@contextmanager
def with_sys_path(path):
    # if path is a file, use its directory
    if os.path.isfile(path):
        path = os.path.dirname(path)
    path = os.path.abspath(path)
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        yield
    finally:
        if path in sys.path:
            sys.path.remove(path)


def add_to_sys_path(path):
    """Add the directory of the given file to the sys.path."""
    # if path is a file, use its directory
    if os.path.isfile(path):
        path = os.path.dirname(path)
    path = os.path.abspath(path)
    if path not in sys.path:
        sys.path.insert(0, path)


def import_local(path, module_name):
    if os.path.isfile(path):
        path = os.path.dirname(path)
    with with_sys_path(path):
        return importlib.import_module(module_name)


# __all__ = [
#     "Vec2",
#     "World",
#     "Body"
#     # defs
#     "WorldDef",
#     "BodyDef",
#     "ShapeDef",
#     "ChainDef",
#     # joints
#     "RevoluteJointDef",
#     "DistanceJointDef",
#     "PrismaticJointDef",
#     "FilterJointDef",
#     "WeldJointDef",
#     "WheelJointDef",
#     "MouseJointDef",
#     "MotorJointDef",
#     # other defs and classes
#     "ExplosionDef",
#     "SurfaceMaterial",
#     "Filter",
#     "QueryFilter",
#     "AABB",
#     "RayResult",
#     # shapes
#     "Circle",
#     "Capsule",
#     "Segment",
#     "ChainSegment",
#     "Polygon",

#     # classes for created things
#     "Shape",
#     "CircleShape",
#     "CapsuleShape",
#     "SegmentShape",
#     "ChainSegmentShape",
#     "PolygonShape",

#     # factories
#     "circle",
#     "capsule",
#     "segment",
#     "chain_segment",
#     "polygon",
#     "chain_def",
#     "box",
#     "chain_box",
#     "aabb",
#     "aabb_arround_point",
#     "rgb_to_hex_color",
#     "rgba_to_hex_color",
#     "hex_color",
#     "random_hex_color",
#     # "HexColor",
#     "BodyFactory",
#     # factory functions
#     "world_def",
#     "body_def",
#     "shape_def",
#     "surface_material",
#     "revolute_joint_def",
#     "distance_joint_def",
#     "prismatic_joint_def",
#     "filter_joint_def",
#     "weld_joint_def",
#     "wheel_joint_def",
#     "mouse_joint_def",
#     "motor_joint_def",
#     "explosion_def",
#     # constants
#     "STOP_QUERY",
#     "CONTINUE_QUERY",
#     # utility functions
#     "make_filter",
#     "make_query_filter",
#     "query_filter",
#     "create_body",
#     "create_joint",
#     "create_shape",
#     "create_explosion",
#     "create_surface_material",
#     "create_chain",
#     "create_polygon",
#     "create_circle",
#     "create_capsule",
#     "create_segment",
#     "create_chain_segment"
# ]

# some constats
STOP_QUERY = False
CONTINUE_QUERY = True

# to auto generate a bunch of stuff
_joint_names = [
    "distance",
    "filter",
    "motor",
    "mouse",
    "prismatic",
    "revolute",
    "wheel",
    "weld",
]


class World(WorldView):
    # only the constructor (and __del__) is allowed to be added to this class.
    # All other methods are added to the WorldView class
    def __init__(self, /, thread_pool=None, **kwargs):
        d = world_def(**kwargs)
        if thread_pool is not None:
            d._install_thread_pool(thread_pool)
            self._threadpool = thread_pool
        world_id = create_world_id(d)

        super().__init__(world_id)

    def __del__(self):
        self.destroy()


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


def chain_def(points, materials=None, material=None, is_loop=False, filter=None):
    if material is not None and materials is not None:
        raise ValueError("Either material or materials can be set, not both.")
    if material is not None:
        materials = [material]

    chain = ChainDef()
    chain.points = np.require(points, dtype=np.float32, requirements="C")
    chain.is_loop = is_loop
    if materials is not None:
        chain.materials = materials
    return chain


def surface_material(**kwargs):
    material = SurfaceMaterial()
    for k, v in kwargs.items():
        setattr(material, k, v)
    return material


def shape_def(**kwargs):
    shape = ShapeDef()
    for k, v in kwargs.items():
        setattr(shape, k, v)
    return shape


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


def filter_joint_def(**kwargs):
    joint = FilterJointDef()
    for k, v in kwargs.items():
        setattr(joint, k, v)
    return joint


def weld_joint_def(**kwargs):
    joint = WeldJointDef()
    for k, v in kwargs.items():
        setattr(joint, k, v)
    return joint


def wheel_joint_def(**kwargs):
    joint = WheelJointDef()
    for k, v in kwargs.items():
        setattr(joint, k, v)
    return joint


def mouse_joint_def(**kwargs):
    joint = MouseJointDef()
    for k, v in kwargs.items():
        setattr(joint, k, v)
    return joint


def motor_joint_def(**kwargs):
    joint = MotorJointDef()
    for k, v in kwargs.items():
        setattr(joint, k, v)
    return joint


def explosion_def(**kwargs):
    explosion = ExplosionDef()
    for k, v in kwargs.items():
        setattr(explosion, k, v)
    return explosion


_shape_def_f = shape_def
_surface_material_f = surface_material


class BodyFactory(object):
    def __init__(self, world, **kwargs):
        self.world = world
        self.body_def = body_def(**kwargs)

        self._material = _surface_material_f()
        self._shape_def = _shape_def_f()
        self._s = []

    def surface_material(self, **kwargs):
        self._material = _surface_material_f(**kwargs)
        self._shape_def.material = self._material
        return self

    def shape(self, material=None, **kwargs):
        if material is not None:
            self._shape_def = _shape_def_f(**kwargs)
            self._shape_def.material = self.material
        else:
            self._shape_def = _shape_def_f(**kwargs)
            self._material = self._shape_def.material
        return self

    def static(self):
        self.body_def.type = BodyType.STATIC
        return self

    def dynamic(self):
        self.body_def.type = BodyType.DYNAMIC
        return self

    def kinematic(self):
        self.body_def.type = BodyType.KINEMATIC
        return self

    def create(self):
        body = self.world.create_body(self.body_def)
        body.create_shapes(self._shape_def, self._s)
        return body

    def add_circle(self, *args, **kwargs):
        self._s.append(circle(*args, **kwargs))
        return self

    def add_capsule(self, *args, **kwargs):
        capsule = make_capsule(*args, **kwargs)
        self._s.append(capsule)
        return self

    def add_polygon(self, *args, **kwargs):
        self._s.append(polygon(*args, **kwargs))
        return self

    def add_box(self, *args, **kwargs):
        self._s.append(box(*args, **kwargs))
        return self

    # chain all properties of body_def st.
    # we can use this factory.position((0, 0)).type(BodyType.DYNAMIC).create()
    def __getattr__(self, name):
        if hasattr(self.body_def, name):

            def setter(value):
                setattr(self.body_def, name, value)
                return self

            return setter
        raise AttributeError(
            f"'{self.__class__.__name__}/{self.body_def.__class__.__name__}' object has no attribute '{name}'"
        )


# add pure python methods to various classes
def _extend_world():
    # avoid name conflicts
    _body_def_func = body_def

    ##########################
    # extend word
    #########################
    def create_body(self, body_def=None, **kwargs):
        if body_def is None:
            body_def = _body_def_func(**kwargs)
        for k, v in kwargs.items():
            setattr(body_def, k, v)
        return self.create_body_from_def(body_def)

    WorldView.create_body = create_body
    WorldView.create_dynamic_body = partialmethod(WorldView.create_body, type=BodyType.DYNAMIC)
    WorldView.create_static_body = partialmethod(WorldView.create_body, type=BodyType.STATIC)
    WorldView.create_kinematic_body = partialmethod(WorldView.create_body, type=BodyType.KINEMATIC)

    def draw(self, debug_draw, call_begin_end=True):
        if call_begin_end:
            debug_draw.begin_draw()
        self._draw(debug_draw)
        if call_begin_end:
            debug_draw.end_draw()

    WorldView.draw = draw

    ##########################
    # explode
    ##########################
    _mk_explosion_def = explosion_def

    def explode(self, explosion_def=None, **kwargs):
        if explosion_def is None:
            explosion_def = _mk_explosion_def(**kwargs)
        for k, v in kwargs.items():
            setattr(explosion_def, k, v)
        return self._explode(explosion_def)

    WorldView.explode = explode

    def overlap_aabb(self, aabb, callback, query_filter=None, wrap_callback=True):
        if query_filter is None:
            query_filter = QueryFilter()

        if wrap_callback:

            def wrapped_cb(shape):
                res = callback(shape)
                if res is None:
                    return True
                else:
                    return bool(res)

        else:
            wrapped_cb = callback
        return self._overlap_aabb(aabb, query_filter, wrapped_cb)

    WorldView.overlap_aabb = overlap_aabb

    def cast_ray(self, origin, translation, callback, query_filter=None):
        if query_filter is None:
            query_filter = QueryFilter()

        def wrapped_cb(shape, point, normal, fraction):
            res = callback(shape, point, normal, fraction)
            if res is None:
                return 1
            else:
                return float(res)

        return self._cast_ray(origin, translation, query_filter, wrapped_cb)

    WorldView.cast_ray = cast_ray

    def body_factory(self):
        return BodyFactory(self)

    WorldView.body_factory = body_factory

    def helper(joint_name):
        # def_cls = getattr(_pyb2d3, f"{joint_name.capitalize()}JointDef")
        def_func = globals()[f"{joint_name}_joint_def"]
        raw_function = getattr(WorldView, f"_create_{joint_name}_joint")

        def create_joint(self, *args, **kwargs):
            na = len(args)
            nk = len(kwargs)

            if na == 0:
                return raw_function(self, def_func(**kwargs))
            elif na == 1:
                if nk > 0:
                    raise ValueError(
                        "if only one argument is given, it should be a joint_def, no kwargs allowed"
                    )
                return raw_function(self, args[0])
            elif na == 2:
                return raw_function(self, def_func(body_a=args[0], body_b=args[1], **kwargs))
            else:
                raise ValueError(
                    """ the un-named arguments can be either:
                1. a joint_def (and no kwargs)
                2. two bodies (and and additional kwargs)
                3. just kwargs"""
                )

        create_joint.__name__ = f"create_{joint_name}_joint"
        return create_joint

    for joint_name in _joint_names:
        setattr(WorldView, f"create_{joint_name}_joint", helper(joint_name))

    def create_joint(self, joint_def):
        if isinstance(joint_def, RevoluteJointDef):
            return self.create_revolute_joint(joint_def)
        elif isinstance(joint_def, DistanceJointDef):
            return self.create_distance_joint(joint_def)
        elif isinstance(joint_def, PrismaticJointDef):
            return self.create_prismatic_joint(joint_def)
        elif isinstance(joint_def, WheelJointDef):
            return self.create_wheel_joint(joint_def)
        elif isinstance(joint_def, NullJointDef):
            return self.create_null_joint(joint_def)
        elif isinstance(joint_def, PulleyJointDef):
            return self.create_pulley_joint(joint_def)
        elif isinstance(joint_def, WeldJointDef):
            return self.create_gear_joint(joint_def)
        elif isinstance(joint_def, MouseJointDef):
            return self.create_mouse_joint(joint_def)
        else:
            raise ValueError(f"joint {joint_def} not recognized")

    WorldView.create_joint = create_joint


_extend_world()
del _extend_world


def _extend_body():
    def create_shape(self, shape_def, shape):
        if isinstance(shape, Circle):
            return self.create_circle_shape(shape_def, shape)
        elif isinstance(shape, Polygon):
            return self.create_polygon_shape(shape_def, shape)
        elif isinstance(shape, Capsule):
            return self.create_capsule_shape(shape_def, shape)
        elif isinstance(shape, Segment):
            return self.create_segment_shape(shape_def, shape)
        else:
            raise ValueError(f"shape {shape} not recognized")

    Body.create_shape = create_shape

    def create_shapes(self, shape_def, shapes):
        res = []
        for shape in shapes:
            res.append(self.create_shape(shape_def, shape))
        return res

    Body.create_shapes = create_shapes


_extend_body()
del _extend_body


def _extend_ray_result():
    def reflect_vector(D, P1, P2):
        # Line direction
        L = P2 - P1
        L_unit = L / np.linalg.norm(L)

        # Projection of D onto L
        proj_length = np.dot(D, L_unit)
        proj = proj_length * L_unit

        # Reflection formula
        R = 2 * proj - D

        # normalize the reflected vector
        R_length = np.linalg.norm(R)
        if R_length > 0:
            R = R / R_length

        R *= -1

        return R

    def compute_normal(self, ray_direction):
        shape = self.shape
        if not isinstance(shape, ChainSegmentShape):
            return self.normal
        else:
            body = self.shape.body
            segment = shape.segment
            p0 = segment.point1
            p1 = segment.point2

            # get points in world coordinates
            p0_world = body.world_point(p0)
            p1_world = body.world_point(p1)

            return reflect_vector(
                ray_direction,
                np.array(p0_world),
                np.array(p1_world),
            )

    RayResult.compute_normal = compute_normal


_extend_ray_result()
del _extend_ray_result


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


def transform(p=None, q=None):
    t = Transform()
    if p is not None:
        t.p = p
    if q is not None:
        t.q = q
    return t


def make_filter(**kwargs):
    filter = Filter()
    for k, v in kwargs.items():
        setattr(filter, k, v)
    return filter


def make_query_filter(**kwargs):
    query_filter = QueryFilter()
    for k, v in kwargs.items():
        setattr(query_filter, k, v)
    return query_filter


def query_filter(**kwargs):
    """Create a QueryFilter object with the given keyword arguments."""
    return make_query_filter(**kwargs)


def circle(center=(0, 0), radius=1):
    c = Circle()
    c.center = center
    c.radius = radius
    return c


def capsule(center1, center2, radius):
    c = Capsule()
    c.center1 = center1
    c.center2 = center2
    c.radius = radius
    return c


def segment(point1, point2):
    s = Segment()
    s.point1 = point1
    s.point2 = point2
    return s


def chain_segment(segment, ghost1, ghost2):
    c = ChainSegment()
    c.segment = segment
    c.ghost1 = ghost1
    c.ghost2 = ghost2
    return c


def polygon(points=None, hull=None, radius=None, position=None, rotation=None):
    if int(hull is not None) + int(points is not None) != 1:
        raise ValueError("either hull or points should be provided, but not both")
    if hull is None:
        n_points = len(points)
        if n_points < 3 or n_points > 8:
            raise ValueError("the number of points should be between 3 and 8, but got {n_points}")
        points = np.require(points, dtype=np.float32, requirements="C")
        hull = compute_hull(points)

    if position and rotation is not None:
        if radius is None:
            radius = 0.0
        return b2d._make_polygon(hull, radius)
    else:
        if position is None:
            position = (0, 0)
        if rotation is None:
            rotation = 0.0

        if radius is None:
            return _pyb2d3._make_offset_polygon(hull, position, rotation)
        else:
            return _pyb2d3._make_offset_rounded_polygon(hull, position, rotation, radius)


def box(hx, hy, center=None, rotation=None, radius=None):
    if center is None and rotation is None:
        if radius is None:
            return _pyb2d3._make_box(hx, hy)
        else:
            return _pyb2d3._make_rounded_box(hx, hy, radius)
    else:
        if center is None:
            center = (0, 0)
        if rotation is None:
            rotation = 0.0

        if radius is None:
            return _pyb2d3._make_offset_box(hx, hy, center, rotation)
        else:
            return _pyb2d3._make_offset_rounded_box(hx, hy, radius, center, rotation)


def chain_box(hx, hy, center=(0, 0), angle=None):
    """Create a chain shape that represents a box centered at `center` with half-width `hx` and half-height `hy`."""
    points = np.array(
        [
            (center[0] - hx, center[1] - hy),
            (center[0] - hx, center[1] + hy),
            (center[0] + hx, center[1] + hy),
            (center[0] + hx, center[1] - hy),
        ]
    )
    if angle is not None:
        # rotate the points around the center
        cos_angle = np.cos(angle)
        sin_angle = np.sin(angle)
        rotation_matrix = np.array([[cos_angle, -sin_angle], [sin_angle, cos_angle]])
        points = np.dot(points - center, rotation_matrix) + center
    return chain_def(points=points, is_loop=True)


def aabb(lower_bound, upper_bound):
    aabb = AABB()
    aabb.lower_bound = lower_bound
    aabb.upper_bound = upper_bound
    return aabb


def aabb_arround_point(point, radius):
    lower_bound = (point[0] - radius, point[1] - radius)
    upper_bound = (point[0] + radius, point[1] + radius)
    return aabb(lower_bound, upper_bound)


def ensure_hex_color(color):
    """Ensure color is a hex integer"""
    if isinstance(color, int):
        return color
    elif isinstance(color, tuple) and len(color) == 3:
        return rgb_to_hex_color(*color)
    else:
        raise ValueError("Color must be an int or a tuple of (R, G, B) values.")


def rgb_to_hex_color(r, g, b):
    """Convert RGB values to a hexadecimal integer."""
    # since we have 8 bits left, lets fill them with 255
    return (r << 16) | (g << 8) | b


def rgba_to_hex_color(r, g, b, a):
    """Convert RGBA values to a hexadecimal integer."""
    # since we have 8 bits left, lets fill them with 255
    return (r << 24) | (g << 16) | (b << 8) | a


def hex_color(*args):
    """Create a HexColor object from RGB values."""
    if len(args) == 1:
        return args[0]  # assume it's already a hex color integer
    elif len(args) == 3:
        return (args[0] << 16) | (args[1] << 8) | args[2]
    else:
        raise ValueError("hex_color expects either a single integer or three RGB values.")


def random_hex_color():
    """Generate a random hexadecimal color integer."""
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return rgb_to_hex_color(r, g, b)


# ignore in doc
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


def extend_batch_api():
    IdClasses = [(Bodies, Body)]

    for batch_cls, single_cls in IdClasses:

        def __iter__(self):
            return map(single_cls, self.id_iter())

        batch_cls.__iter__ = __iter__


extend_batch_api()
del extend_batch_api


class PathBuilder(object):
    def __init__(self, start):
        self.points = [start]

    def chain_def(self, is_loop=False, material=None, reverse=False):
        points = np.require(self.points, dtype=np.float32, requirements="C")
        if reverse:
            points = points[::-1]
        return chain_def(points, is_loop=is_loop, material=material)

    def _point(self, **point_args):
        assert len(point_args) == 1, "Only one of point, delta, left, right, up, down must be given"
        last_point = self.points[-1]
        if "point" in point_args:
            return point_args["point"]
        elif "delta" in point_args:
            return (
                last_point[0] + point_args["delta"][0],
                last_point[1] + point_args["delta"][1],
            )
        elif "left" in point_args:
            return (last_point[0] - point_args["left"], last_point[1])
        elif "right" in point_args:
            return (last_point[0] + point_args["right"], last_point[1])
        elif "up" in point_args:
            return (last_point[0], last_point[1] + point_args["up"])
        elif "down" in point_args:
            return (last_point[0], last_point[1] - point_args["down"])
        else:
            raise ValueError("No valid point or delta provided")

    def line_to(self, **point_args):
        self.points.append(self._point(**point_args))

    def arc_to(self, /, radius, clockwise=True, segments=10, major_arc=False, **point_args):
        from_point = self.points[-1]
        to_point = self._point(**point_args)

        dx = to_point[0] - from_point[0]
        dy = to_point[1] - from_point[1]
        chord_length = math.hypot(dx, dy)

        if radius < chord_length / 2:
            raise ValueError("Radius too small to form an arc between the points")

        # Midpoint of the chord
        mx = (from_point[0] + to_point[0]) / 2
        my = (from_point[1] + to_point[1]) / 2

        # Distance from midpoint to circle center (h)
        h = math.sqrt(radius**2 - (chord_length / 2) ** 2)

        # Perpendicular unit vector to the chord
        perp_dx = -dy / chord_length
        perp_dy = dx / chord_length

        # Compute both possible centers
        center1 = (mx + h * perp_dx, my + h * perp_dy)
        center2 = (mx - h * perp_dx, my - h * perp_dy)

        # Compute angles from centers to points
        def arc_angle(center):
            a1 = math.atan2(from_point[1] - center[1], from_point[0] - center[0])
            a2 = math.atan2(to_point[1] - center[1], to_point[0] - center[0])
            delta = (a2 - a1) % (2 * math.pi)
            return delta if clockwise else (2 * math.pi - delta)

        # Select center that gives the minor arc in the desired direction
        angle1 = arc_angle(center1)
        # angle2 = arc_angle(center2)

        if (angle1 <= math.pi) == major_arc:
            center = center1
            start_angle = math.atan2(from_point[1] - center[1], from_point[0] - center[0])
            end_angle = math.atan2(to_point[1] - center[1], to_point[0] - center[0])
        else:
            center = center2
            start_angle = math.atan2(from_point[1] - center[1], from_point[0] - center[0])
            end_angle = math.atan2(to_point[1] - center[1], to_point[0] - center[0])

        # Normalize angle span to always go minor arc direction
        if clockwise:
            if end_angle > start_angle:
                end_angle -= 2 * math.pi
        else:
            if end_angle < start_angle:
                end_angle += 2 * math.pi

        # Generate arc points
        for i in range(1, segments + 1):
            t = i / segments
            angle = start_angle + (end_angle - start_angle) * t
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            self.points.append((x, y))

        # helpfull
        return center


def ray_cast_input(origin=(0, 0), translation=(0, 0), max_fraction=1.0):
    return b2RayCastInput(origin, translation, max_fraction)


class DebugDraw(DebugDrawBase):
    def __init__(self):
        super().__init__(self)

    def draw_polygon(self, points, color):
        pass

    def draw_solid_polygon(self, transform, points, radius, color):
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
