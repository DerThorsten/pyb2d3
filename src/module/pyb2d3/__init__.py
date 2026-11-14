import numpy as np
import random
import math
import sys
import os
from ._pyb2d3 import *  # noqa: F403
from . import _pyb2d3
from functools import partial, partialmethod
from enum import IntEnum
from contextlib import contextmanager
import importlib
import importlib.metadata

try:
    __version__ = importlib.metadata.version("pyb2d3")
except importlib.metadata.PackageNotFoundError:  # in-place build, not installed
    __version__ = "dev"


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


# some constants for query callbacks
STOP_QUERY = False
CONTINUE_QUERY = True


##############################################################################
# def factories:  xxx_def(**kwargs) -> XxxDef with the given attributes set
##############################################################################


def _set_attributes(obj, kwargs):
    for k, v in kwargs.items():
        setattr(obj, k, v)
    return obj


def _make_def_factory(cls):
    def factory(**kwargs):
        return _set_attributes(cls(), kwargs)

    factory.__name__ = factory.__qualname__ = cls.__name__
    factory.__doc__ = f"Create a {cls.__name__} with the given attributes set."
    return factory


world_def = _make_def_factory(WorldDef)
body_def = _make_def_factory(BodyDef)
shape_def = _make_def_factory(ShapeDef)
surface_material = _make_def_factory(SurfaceMaterial)
explosion_def = _make_def_factory(ExplosionDef)
make_filter = _make_def_factory(Filter)
make_query_filter = _make_def_factory(QueryFilter)
query_filter = make_query_filter

dynamic_body_def = partial(body_def, type=BodyType.DYNAMIC)
static_body_def = partial(body_def, type=BodyType.STATIC)
kinematic_body_def = partial(body_def, type=BodyType.KINEMATIC)

# joints: one def factory and one World.create_xxx_joint method per joint type
_joint_names = [
    "distance",
    "filter",
    "motor",
    "mover",
    "pogo",
    "prismatic",
    "revolute",
    "weld",
    "wheel",
]
_joint_def_classes = {name: getattr(_pyb2d3, f"{name.capitalize()}JointDef") for name in _joint_names}

for _name, _cls in _joint_def_classes.items():
    globals()[f"{_name}_joint_def"] = _make_def_factory(_cls)
del _name, _cls


def chain_def(points, materials=None, material=None, is_loop=False, filter=None):
    if material is not None and materials is not None:
        raise ValueError("Either material or materials can be set, not both.")
    if material is not None:
        materials = [material]

    chain = ChainDef()
    chain.points = points  # any iterable of points / numpy array
    chain.is_loop = is_loop
    if materials is not None:
        chain.materials = materials
    if filter is not None:
        chain.filter = filter
    return chain


def _extend_def_classes():
    def update(self, **kwargs):
        return _set_attributes(self, kwargs)

    for cls in [WorldDef, BodyDef, ShapeDef, ExplosionDef, SurfaceMaterial, *_joint_def_classes.values()]:
        cls.update = update


_extend_def_classes()
del _extend_def_classes


##############################################################################
# World
##############################################################################


class World(WorldView):
    # only the constructor (and __del__) is allowed to be added to this class.
    # All other methods are added to the WorldView class
    def __init__(self, /, thread_pool=None, _world_id=None, **kwargs):
        if _world_id is None:
            d = world_def(**kwargs)
            if thread_pool is not None:
                d._install_thread_pool(thread_pool)
            _world_id = create_world_id(d)
        # keep the thread pool alive as long as the world
        self._threadpool = thread_pool
        super().__init__(_world_id)

    @classmethod
    def from_snapshot(cls, image, worker_count=0):
        """Create a new world from an image produced by `WorldView.get_snapshot()`."""
        return cls(_world_id=create_world_id_from_snapshot(image, worker_count))

    def __del__(self):
        self.destroy()


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
        self._shape_def = _shape_def_f(**kwargs)
        if material is not None:
            self._material = material
            self._shape_def.material = material
        else:
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
        self._s.append(capsule(*args, **kwargs))
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
    _body_def_func = body_def

    def create_body(self, body_def=None, **kwargs):
        if body_def is None:
            body_def = _body_def_func(**kwargs)
        else:
            _set_attributes(body_def, kwargs)
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

    _mk_explosion_def = explosion_def

    def explode(self, explosion_def=None, **kwargs):
        if explosion_def is None:
            explosion_def = _mk_explosion_def(**kwargs)
        else:
            _set_attributes(explosion_def, kwargs)
        return self._explode(explosion_def)

    WorldView.explode = explode

    def body_factory(self):
        return BodyFactory(self)

    WorldView.body_factory = body_factory

    def dynamic_body_at_point(self, point, query_filter=None):
        if query_filter is None:
            query_filter = QueryFilter()
        return self.body_at_point(point, query_filter, dynamic_only=True)

    WorldView.dynamic_body_at_point = dynamic_body_at_point

    # create_xxx_joint(def) / create_xxx_joint(body_a, body_b, **kwargs) / create_xxx_joint(**kwargs)
    def make_create_joint(joint_name):
        def_func = globals()[f"{joint_name}_joint_def"]
        raw_function = getattr(WorldView, f"_create_{joint_name}_joint")

        def create_joint(self, *args, **kwargs):
            if len(args) == 0:
                return raw_function(self, def_func(**kwargs))
            if len(args) == 1:
                if kwargs:
                    raise ValueError("if only one argument is given, it should be a joint_def, no kwargs allowed")
                return raw_function(self, args[0])
            if len(args) == 2:
                return raw_function(self, def_func(body_a=args[0], body_b=args[1], **kwargs))
            raise ValueError(
                """the un-named arguments can be either:
                1. a joint_def (and no kwargs)
                2. two bodies (and additional kwargs)
                3. just kwargs"""
            )

        create_joint.__name__ = f"create_{joint_name}_joint"
        return create_joint

    for joint_name in _joint_names:
        setattr(WorldView, f"create_{joint_name}_joint", make_create_joint(joint_name))

    _def_type_to_name = {cls: name for name, cls in _joint_def_classes.items()}

    def create_joint(self, joint_def):
        name = _def_type_to_name.get(type(joint_def))
        if name is None:
            raise ValueError(f"joint def {joint_def} not recognized")
        return getattr(self, f"create_{name}_joint")(joint_def)

    WorldView.create_joint = create_joint


_extend_world()
del _extend_world


def _extend_body():
    _creators = {
        Circle: "create_circle_shape",
        Polygon: "create_polygon_shape",
        Capsule: "create_capsule_shape",
        Segment: "create_segment_shape",
        ChainSegment: "create_chain_segment_shape",
    }

    def create_shape(self, shape_def, shape):
        creator = _creators.get(type(shape))
        if creator is None:
            raise ValueError(f"shape {shape} not recognized")
        return getattr(self, creator)(shape_def, shape)

    Body.create_shape = create_shape

    def create_shapes(self, shape_def, shapes):
        return [self.create_shape(shape_def, shape) for shape in shapes]

    Body.create_shapes = create_shapes


_extend_body()
del _extend_body


def _extend_ray_result():
    def reflect_vector(D, P1, P2):
        L = P2 - P1
        L_unit = L / np.linalg.norm(L)
        proj = np.dot(D, L_unit) * L_unit
        R = 2 * proj - D
        R_length = np.linalg.norm(R)
        if R_length > 0:
            R = R / R_length
        return -R

    def compute_normal(self, ray_direction):
        shape = self.shape
        if not isinstance(shape, ChainSegmentShape):
            return self.normal
        body = shape.body
        segment = shape.segment
        p0_world = body.world_point(segment.point1)
        p1_world = body.world_point(segment.point2)
        return reflect_vector(ray_direction, np.array(p0_world), np.array(p1_world))

    RayResult.compute_normal = compute_normal


_extend_ray_result()
del _extend_ray_result


##############################################################################
# batch api:  Bodies / Shapes / Joints are arrays of ids
##############################################################################


def _extend_batch_api():
    def typed(cls):
        # shapes / joints come back as their concrete type (CircleShape, RevoluteJoint, ...)
        if hasattr(cls, "cast"):
            return lambda i: cls(int(i)).cast()
        return lambda i: cls(int(i))

    for batch_cls, single_cls in [(Bodies, Body), (Shapes, Shape), (Joints, Joint)]:

        def __iter__(self, _make=typed(single_cls)):
            return map(_make, self.ids)

        def __getitem__(self, index, _make=typed(single_cls), _batch=batch_cls):
            ids = self.ids
            if isinstance(index, (int, np.integer)):
                return _make(ids[index])
            return _batch(ids[index])

        def __repr__(self):
            return f"{type(self).__name__}(n={len(self)})"

        batch_cls.__iter__ = __iter__
        batch_cls.__getitem__ = __getitem__
        batch_cls.__repr__ = __repr__


_extend_batch_api()
del _extend_batch_api


##############################################################################
# mouse dragging (box2d >= 3.2 has no mouse joint: kinematic body + motor joint)
##############################################################################


class MouseDrag(object):
    """Drag a body with the mouse, the way box2d's own samples do it.

    A kinematic "mouse body" follows the cursor and pulls the grabbed body
    with a motor joint (a spring plus some angular friction).

    Usage::

        drag = MouseDrag(world)
        drag.begin(point)          # on mouse down, returns the grabbed body or None
        drag.update(point)         # on mouse move
        drag.step(time_step)       # once per world step, before world.step(...)
        drag.end()                 # on mouse up
    """

    def __init__(self, world, hertz=7.5, damping_ratio=1.0, force_scale=100.0, angular_friction=0.25):
        self.world = world
        self.hertz = hertz
        self.damping_ratio = damping_ratio
        self.force_scale = force_scale
        self.angular_friction = angular_friction

        self.body = None  # the grabbed body
        self.joint = None
        self._mouse_body = None
        self._target = None

    @property
    def active(self):
        return self.joint is not None and self.joint.is_valid

    def begin(self, point, body=None):
        self.end()
        if body is None:
            body = self.world.dynamic_body_at_point(point)
        if body is None:
            return None

        self._target = (float(point[0]), float(point[1]))
        self._mouse_body = self.world.create_kinematic_body(position=self._target, enable_sleep=False)

        mass_data = body.mass_data
        g = float(np.linalg.norm(self.world.gravity))
        mg = mass_data.mass * (g if g > 0 else 10.0)

        joint_def = motor_joint_def(
            body_a=self._mouse_body,
            body_b=body,
            linear_hertz=self.hertz,
            linear_damping_ratio=self.damping_ratio,
            max_spring_force=self.force_scale * mg,
        )
        joint_def.local_anchor_b = body.local_point(point)
        if mass_data.mass > 0:
            # acts like angular friction
            lever = math.sqrt(mass_data.rotational_inertia / mass_data.mass)
            joint_def.max_velocity_torque = self.angular_friction * lever * mg

        self.joint = self.world.create_motor_joint(joint_def)
        self.body = body
        return body

    def update(self, point):
        self._target = (float(point[0]), float(point[1]))

    def step(self, time_step):
        if self.joint is None:
            return
        if not self.joint.is_valid:
            # the world or the grabbed body was destroyed
            self.end()
            return
        if time_step > 0:
            self._mouse_body.set_target_transform(transform(p=self._target), time_step, True)

    def end(self):
        if self.joint is not None and self.joint.is_valid:
            self.joint.destroy()
        if self._mouse_body is not None and self._mouse_body.is_valid:
            self._mouse_body.destroy()
        self.joint = None
        self.body = None
        self._mouse_body = None


##############################################################################
# geometry helpers
##############################################################################


def transform(p=None, q=None):
    t = Transform()
    if p is not None:
        t.p = p
    if q is not None:
        t.q = q
    return t


def circle(center=(0, 0), radius=1):
    return Circle(center, radius)


def capsule(center1, center2, radius):
    return Capsule(center1, center2, radius)


make_capsule = capsule


def segment(point1, point2):
    return Segment(point1, point2)


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
        hull = compute_hull(points)  # any iterable of points / numpy array
        if hull.count == 0:
            raise ValueError(
                "could not compute a convex hull: polygons need 3 to 8 points that are not collinear"
            )

    if position is None and rotation is None:
        return make_polygon(hull, 0.0 if radius is None else radius)

    position = (0, 0) if position is None else position
    rotation = 0.0 if rotation is None else rotation
    if radius is None:
        return make_offset_polygon(hull, position, rotation)
    return make_offset_rounded_polygon(hull, position, rotation, radius)


def box(hx, hy, center=None, rotation=None, radius=None):
    if center is None and rotation is None:
        if radius is None:
            return make_box(hx, hy)
        return make_rounded_box(hx, hy, radius)

    center = (0, 0) if center is None else center
    rotation = 0.0 if rotation is None else rotation
    if radius is None:
        return make_offset_box(hx, hy, center, rotation)
    return make_offset_rounded_box(hx, hy, center, rotation, radius)


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
        cos_angle = np.cos(angle)
        sin_angle = np.sin(angle)
        rotation_matrix = np.array([[cos_angle, -sin_angle], [sin_angle, cos_angle]])
        points = np.dot(points - center, rotation_matrix) + center
    return chain_def(points=points, is_loop=True)


def aabb(lower_bound, upper_bound):
    return AABB(lower_bound, upper_bound)


def aabb_arround_point(point, radius):
    lower_bound = (point[0] - radius, point[1] - radius)
    upper_bound = (point[0] + radius, point[1] + radius)
    return aabb(lower_bound, upper_bound)


def ray_cast_input(origin=(0, 0), translation=(0, 0), max_fraction=1.0):
    return RayCastInput(origin, translation, max_fraction)


##############################################################################
# colors
##############################################################################


def ensure_hex_color(color):
    """A color as 0xRRGGBB int: accepts ints (incl. HexColor members) and (r, g, b) tuples."""
    if isinstance(color, int):
        return int(color)
    if isinstance(color, (tuple, list)) and len(color) == 3:
        return rgb_to_hex_color(*(int(c) for c in color))
    raise ValueError(f"a color must be an int (e.g. b2d.HexColor.Red) or an (r, g, b) tuple, got {color!r}")


def rgb_to_hex_color(r, g, b):
    """Convert RGB values to a hexadecimal integer."""
    return (r << 16) | (g << 8) | b


def rgba_to_hex_color(r, g, b, a):
    """Convert RGBA values to a hexadecimal integer."""
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
# an IntEnum: members are plain 0xRRGGBB ints, usable wherever a color is expected
class HexColor(IntEnum):
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


##############################################################################
# path builder for chains
##############################################################################


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

        def arc_angle(center):
            a1 = math.atan2(from_point[1] - center[1], from_point[0] - center[0])
            a2 = math.atan2(to_point[1] - center[1], to_point[0] - center[0])
            delta = (a2 - a1) % (2 * math.pi)
            return delta if clockwise else (2 * math.pi - delta)

        # Select center that gives the minor arc in the desired direction
        angle1 = arc_angle(center1)

        center = center1 if (angle1 <= math.pi) == major_arc else center2
        start_angle = math.atan2(from_point[1] - center[1], from_point[0] - center[0])
        end_angle = math.atan2(to_point[1] - center[1], to_point[0] - center[0])

        # Normalize angle span to always go minor arc direction
        if clockwise:
            if end_angle > start_angle:
                end_angle -= 2 * math.pi
        else:
            if end_angle < start_angle:
                end_angle += 2 * math.pi

        for i in range(1, segments + 1):
            t = i / segments
            angle = start_angle + (end_angle - start_angle) * t
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            self.points.append((x, y))

        return center


##############################################################################
# debug draw
##############################################################################


class DebugDraw(DebugDrawBase):
    """Base class for python debug draws. All coordinates are world coordinates."""

    def __init__(self):
        super().__init__(self)

    def begin_draw(self):
        pass

    def end_draw(self):
        pass

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

    def draw_string(self, p, string, color):
        pass

    def draw_aabb(self, aabb, color):
        pass


def _apply_box2d_docs():
    """Docs of the box2d structs and their fields, generated from box2d's header comments
    (scripts/generate_docstrings.py). Functions get theirs when they are bound in C++."""
    from ._docstrings import CLASS_DOCS, FIELD_DOCS

    for name, doc in CLASS_DOCS.items():
        cls = getattr(_pyb2d3, name, None)
        if isinstance(cls, type) and not cls.__doc__:
            cls.__doc__ = doc
    for (name, attr), doc in FIELD_DOCS.items():
        prop = getattr(_pyb2d3, name, type).__dict__.get(attr)
        if isinstance(prop, property):
            prop.__doc__ = doc


_apply_box2d_docs()
del _apply_box2d_docs
