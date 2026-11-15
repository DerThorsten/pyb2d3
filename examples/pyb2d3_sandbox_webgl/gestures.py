"""Pointer gestures of the browser sandbox: mouse, touch and pen pointers become the
sample's mouse events, two fingers on empty space zoom and pan the view.

Pure python (no pyjs): the frontend feeds it the pointer events of the canvas, the
tests feed it fake ones. The host (the frontend) provides:

* ``sample``: the running sample (``on_mouse_down`` / ``move`` / ``up`` / ``leave``)
* ``screen_to_world(x, y)``: canvas CSS px -> world position
* ``on_primary_down(x, y)``: what the first pointer's press does (the sample's
  ``on_mouse_down`` + the multi-click handler)
* ``zoom_at(x, y, factor)``: zoom about a canvas point (factor > 1: zoom in)
* ``pan_screen(dx, dy)``: move the view by a canvas px delta

Rules:

* the first pointer is "the mouse": down / move / up go to the sample as before (drag a
  body, the sample's own handling, or pan the view on empty space)
* a second finger starts a pinch only if neither finger is on a dynamic / kinematic body
  and the first finger is not dragging one; the first finger's interaction is then
  cancelled (``on_mouse_leave``: no "release", e.g. no slingshot shot), the two fingers
  zoom (distance ratio) and pan (midpoint) the view
* any other extra pointer is ignored until it lifts, as is the remaining finger of an
  ended pinch (no sudden jump into a drag / pan)
"""

import math

import pyb2d3 as b2d
from pyb2d3_sandbox.frontend_base import MouseLeaveEvent, MouseMoveEvent, MouseUpEvent


def movable_body_at(world, point):
    """the dynamic or kinematic body at `point` (world coordinates), or None"""
    body = world.dynamic_body_at_point(point)
    if body is None:
        body = world.body_at_point(point)
        if body is not None and body.type == b2d.BodyType.STATIC:
            body = None
    return body


class PointerGestures:
    """pointer events (with pointer ids) -> sample mouse events + pinch zoom / pan"""

    def __init__(self, host):
        self.host = host
        self.positions = {}  # pointer id -> last canvas position (x, y)
        self.primary = None  # the pointer that acts as the mouse
        self.primary_start = None  # where it went down (canvas px)
        self.pinch = None  # (id_a, id_b) while pinching
        self.ignored = set()  # pointers ignored until they lift

    # ---- helpers ----------------------------------------------------------------------

    def _on_movable_body(self, x, y):
        """a dynamic / kinematic body under the canvas position?"""
        sample = self.host.sample
        return (
            sample is not None
            and movable_body_at(sample.world, self.host.screen_to_world(x, y)) is not None
        )

    def _primary_drags_body(self):
        """is the first pointer dragging a body (the built-in mouse drag)?"""
        drag = getattr(self.host.sample, "_mouse_drag", None)
        return drag is not None and drag.active

    def _pinch_geometry(self):
        """(distance, midpoint) of the two pinching pointers"""
        (ax, ay), (bx, by) = (self.positions[i] for i in self.pinch)
        return math.hypot(bx - ax, by - ay), (0.5 * (ax + bx), 0.5 * (ay + by))

    # ---- events -----------------------------------------------------------------------

    def down(self, pid, x, y, pointer_type="mouse"):
        """a pointer went down at canvas position (x, y)"""
        if self.primary is None and self.pinch is None and not self.positions:
            self.positions[pid] = (x, y)
            self.primary, self.primary_start = pid, (x, y)
            self.host.on_primary_down(x, y)
            return
        self.positions[pid] = (x, y)
        can_pinch = (
            pointer_type != "mouse"
            and self.pinch is None
            and self.primary is not None
            and len(self.positions) == 2
            and not self._primary_drags_body()
            and not self._on_movable_body(*self.primary_start)
            and not self._on_movable_body(x, y)
        )
        if not can_pinch:
            self.ignored.add(pid)
            return
        # the first finger's interaction is cancelled, not released
        if self.host.sample is not None:
            self.host.sample.on_mouse_leave(MouseLeaveEvent())
        self.pinch = (self.primary, pid)
        self.primary = None

    def move(self, pid, x, y):
        """a pointer moved (only pressed pointers: touch / pen, or a mouse with a button)"""
        if pid not in self.positions:
            return
        last_x, last_y = self.positions[pid]
        if self.pinch is not None and pid in self.pinch:
            distance, (mx, my) = self._pinch_geometry()
            self.positions[pid] = (x, y)
            new_distance, (nx, ny) = self._pinch_geometry()
            if distance > 1.0 and new_distance > 1.0:
                self.host.zoom_at(nx, ny, new_distance / distance)
            self.host.pan_screen(nx - mx, ny - my)
            return
        self.positions[pid] = (x, y)
        if pid == self.primary and self.host.sample is not None:
            world = self.host.screen_to_world(x, y)
            last = self.host.screen_to_world(last_x, last_y)
            delta = (world[0] - last[0], world[1] - last[1])
            self.host.sample.on_mouse_move(
                MouseMoveEvent(world_position=world, world_delta=b2d.Vec2(*delta))
            )

    def up(self, pid, x, y, cancelled=False):
        """a pointer lifted (cancelled: the browser took it, e.g. a system gesture)"""
        if pid not in self.positions:
            return
        self.positions.pop(pid)
        self.ignored.discard(pid)
        if self.pinch is not None and pid in self.pinch:
            # the pinch ends; the other finger is ignored until it lifts too
            other = self.pinch[0] if self.pinch[1] == pid else self.pinch[1]
            self.pinch = None
            if other in self.positions:
                self.ignored.add(other)
            return
        if pid == self.primary:
            self.primary = self.primary_start = None
            sample = self.host.sample
            if sample is None:
                return
            if cancelled:
                sample.on_mouse_leave(MouseLeaveEvent())
            else:
                sample.on_mouse_up(MouseUpEvent(world_position=self.host.screen_to_world(x, y)))

    def reset(self):
        """forget all pointers (e.g. a new sample)"""
        self.positions.clear()
        self.ignored.clear()
        self.primary = self.primary_start = self.pinch = None
