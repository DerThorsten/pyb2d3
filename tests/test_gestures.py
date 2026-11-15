"""Pointer gestures of the browser sandbox (pyb2d3_sandbox_webgl.gestures), driven with
fake pointer events: one finger drags bodies / pans like a mouse, two fingers on empty
space pinch-zoom and pan, never while a finger is on a body."""

import pyb2d3 as b2d
from pyb2d3_sandbox import SampleBase
from pyb2d3_sandbox_webgl.gestures import PointerGestures, movable_body_at


class Scene(SampleBase):
    """a dynamic box at (5, 5), a kinematic box at (10, 5), static ground below y = 0;
    records the mouse events it gets"""

    def __init__(self, frontend, settings):
        super().__init__(frontend, settings)
        self.calls = []
        ground = self.world.create_static_body(position=(0, -1))
        ground.create_shape(b2d.shape_def(), b2d.box(50, 1))
        self.box = self.world.create_dynamic_body(position=(5, 5), gravity_scale=0.0)
        self.box.create_shape(b2d.shape_def(density=1), b2d.box(1, 1))
        self.kinematic = self.world.create_kinematic_body(position=(10, 5))
        self.kinematic.create_shape(b2d.shape_def(), b2d.box(1, 1))

    def aabb(self):
        return b2d.aabb((-20, -2), (20, 20))

    def on_mouse_down(self, event):
        self.calls.append("down")
        super().on_mouse_down(event)

    def on_mouse_move(self, event):
        self.calls.append("move")
        super().on_mouse_move(event)

    def on_mouse_up(self, event):
        self.calls.append("up")
        super().on_mouse_up(event)

    def on_mouse_leave(self, event):
        self.calls.append("leave")
        super().on_mouse_leave(event)


class Host:
    """the frontend side of PointerGestures; screen = world coordinates (identity)"""

    def __init__(self):
        self.sample = Scene(self, Scene.Settings())
        self.zooms = []  # (x, y, factor)
        self.pans = []  # (dx, dy) by the fingers
        self.camera_drags = []  # world deltas by the sample's own camera drag

    def screen_to_world(self, x, y):
        return b2d.Vec2(x, y)

    def on_primary_down(self, x, y):
        self.sample.on_mouse_down(b2d_mouse_down(x, y))

    def zoom_at(self, x, y, factor):
        self.zooms.append((x, y, factor))

    def pan_screen(self, dx, dy):
        self.pans.append((dx, dy))

    def drag_camera(self, delta):  # (FrontendBase, used by SampleBase's camera drag)
        self.camera_drags.append(tuple(delta))


def b2d_mouse_down(x, y):
    from pyb2d3_sandbox.frontend_base import MouseDownEvent

    return MouseDownEvent(world_position=b2d.Vec2(x, y))


def setup():
    host = Host()
    return host, host.sample, PointerGestures(host)


def test_movable_body_at():
    host = Host()
    world = host.sample.world
    assert movable_body_at(world, (5, 5)) == host.sample.box
    assert movable_body_at(world, (10, 5)) == host.sample.kinematic
    assert movable_body_at(world, (0, -1)) is None  # static ground
    assert movable_body_at(world, (-10, 10)) is None  # empty space


def test_one_finger_drags_a_body():
    host, sample, g = setup()
    g.down(1, 5, 5, "touch")
    assert sample._mouse_drag.active and sample._mouse_drag.body == sample.box
    g.move(1, 6, 5)
    g.up(1, 6, 5)
    assert sample.calls == ["down", "move", "up"]
    assert not sample._mouse_drag.active


def test_one_finger_on_empty_space_pans():
    host, sample, g = setup()
    g.down(1, -10, 10, "touch")
    g.move(1, -9, 10)
    assert host.camera_drags  # the sample's camera drag (as with the mouse)
    assert not host.zooms


def test_two_fingers_on_empty_space_pinch_zoom_and_pan():
    host, sample, g = setup()
    g.down(1, -10, 10, "touch")
    g.down(2, -6, 10, "touch")
    assert sample.calls == ["down", "leave"]  # the first finger is cancelled, not released
    g.move(2, -2, 10)  # spread: distance 4 -> 8
    x, y, factor = host.zooms[-1]
    assert factor == 2.0 and (x, y) == (-6, 10)  # about the new midpoint
    g.move(1, -8, 12)
    g.move(2, 0, 12)  # both moved by (2, 2): pan
    assert host.pans[-2:] and sum(dx for dx, _ in host.pans) > 0
    g.up(1, -8, 12)
    g.move(2, 3, 3)  # the remaining finger does nothing
    g.up(2, 3, 3)
    assert sample.calls == ["down", "leave"]
    # a new touch works normally again
    g.down(3, 5, 5, "touch")
    assert sample._mouse_drag.body == sample.box


def test_no_pinch_while_a_finger_drags_a_body():
    host, sample, g = setup()
    g.down(1, 5, 5, "touch")  # grabs the box
    g.down(2, -10, 10, "touch")  # empty space, but the first finger drags
    g.move(2, -5, 10)
    assert not host.zooms and not host.pans
    assert sample._mouse_drag.active  # still dragging
    g.move(1, 6, 6)
    assert sample.calls == ["down", "move"]


def test_no_pinch_when_the_second_finger_is_on_a_body():
    host, sample, g = setup()
    g.down(1, -10, 10, "touch")
    g.down(2, 10, 5, "touch")  # on the kinematic body
    g.move(2, 12, 5)
    assert not host.zooms
    assert "leave" not in sample.calls  # the first finger keeps its interaction
    g.move(1, -9, 10)
    assert sample.calls[-1] == "move"


def test_a_second_mouse_pointer_never_pinches():
    host, sample, g = setup()
    g.down(1, -10, 10, "mouse")
    g.down(2, -6, 10, "mouse")
    g.move(2, -2, 10)
    assert not host.zooms and "leave" not in sample.calls


def test_cancel_is_not_a_release():
    host, sample, g = setup()
    g.down(1, 5, 5, "touch")
    g.up(1, 5, 5, cancelled=True)
    assert sample.calls == ["down", "leave"]
    assert not sample._mouse_drag.active


def test_reset_forgets_pointers():
    host, sample, g = setup()
    g.down(1, -10, 10, "touch")
    g.down(2, -6, 10, "touch")
    g.reset()
    g.move(2, 0, 10)
    assert not host.zooms
    g.down(3, 5, 5, "touch")
    assert sample._mouse_drag.body == sample.box
