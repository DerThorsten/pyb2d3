from dataclasses import dataclass, field
import time
import math
from abc import ABC, abstractmethod

import pyb2d3 as b2d


class FrontendDebugDraw(b2d.DebugDraw):
    def __init__(self):
        super().__init__()

    def begin_draw(self):
        pass

    def end_draw(self):
        pass

    # only use this function if absolutely no other implementation is available for your debug draw implementation
    def _poor_mans_draw_solid_capsule(self, p1, p2, radius, color):
        # t0 = time.time()
        x1, y1 = p1
        x2, y2 = p2

        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)

        # Unit vector along p1->p2
        ux = dx / length
        uy = dy / length

        # Perpendicular vector
        px = -uy
        py = ux

        # Four corners of the rectangle part
        corner1 = (x1 + px * radius, y1 + py * radius)
        corner2 = (x2 + px * radius, y2 + py * radius)
        corner3 = (x2 - px * radius, y2 - py * radius)
        corner4 = (x1 - px * radius, y1 - py * radius)

        transform = b2d.Transform()
        transform.p = (0, 0)
        transform.q = b2d.Rot(0)

        self.draw_solid_polygon(
            points=[corner1, corner2, corner3, corner4],
            transform=transform,
            color=color,
            radius=0,
        )

        # Draw end circles
        transform = b2d.Transform()
        transform.p = b2d.Vec2(x1, y1)
        # transform.q = b2d.Rot(0)
        self.draw_solid_circle(transform=transform, radius=radius, color=color)
        transform = b2d.Transform()
        transform.p = b2d.Vec2(x2, y2)
        # transform.q = b2d.Rot(0)
        self.draw_solid_circle(transform=transform, radius=radius, color=color)

    # only use this function if absolutely no other implementation is available for your debug draw implementation
    def _poor_mans_draw_solid_rounded_polygon(self, transform, points, radius, color):
        n = len(points)

        for i in range(n):
            raw_p1 = b2d.Vec2(points[i, 0], points[i, 1])
            raw_p2 = b2d.Vec2(points[(i + 1) % n, 0], points[(i + 1) % n, 1])

            p1 = transform.transform_point(raw_p1)
            p2 = transform.transform_point(raw_p2)

            # Vector from p1 to p2
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = math.hypot(dx, dy)

            # Unit perpendicular vector
            ux = dx / length
            uy = dy / length
            perp_x = -uy
            perp_y = ux

            # Offset corners by radius along perpendicular
            corner1 = (float(p1[0] + perp_x * radius), float(p1[1] + perp_y * radius))
            corner2 = (float(p2[0] + perp_x * radius), float(p2[1] + perp_y * radius))
            corner3 = (float(p2[0] - perp_x * radius), float(p2[1] - perp_y * radius))
            corner4 = (float(p1[0] - perp_x * radius), float(p1[1] - perp_y * radius))

            # Draw rectangle as polygon
            # pygame.draw.polygon(surface, color, [corner1, corner2, corner3, corner4])
            empty_transform = b2d.Transform()
            # empty_transform.p = (0, 0)
            # empty_transform.q = b2d.Rot(0)
            self.draw_solid_polygon(
                transform=empty_transform,
                points=[corner1, corner2, corner3, corner4],
                color=color,
                radius=0,
            )

        # # Draw circles at corners

        for p in points:
            tp = transform.transform_point(b2d.Vec2(p[0], p[1]))
            ctransform = b2d.Transform()
            ctransform.p = b2d.Vec2(tp)
            ctransform.q = transform.q
            self.draw_solid_circle(transform=ctransform, radius=radius, color=color)
        # draw the inner part of the polygon
        self.draw_solid_polygon(points=points, transform=transform, color=color, radius=0)


@dataclass
class DebugDrawSettings:
    enabled: bool = True
    draw_shapes: bool = True
    draw_joints: bool = True
    draw_background: bool = True
    background_color: tuple = (46, 46, 46)


@dataclass
class FrontendBaseSettings:
    canvas_shape: tuple = (800, 800)

    hertz: int = 60  # Physics update frequency
    speed: float = 1.0  # Speed multiplier for the simulation
    substeps: int = 5

    # depcrecated as as we center examples automatically
    ppm: float = 40.0  # Pixels per meter

    debug_draw: DebugDrawSettings = field(default_factory=DebugDrawSettings)
    multi_click_delay_ms: int = 350  # Delay in milliseconds to wait for multi-clicks
    headless: bool = False  # If True, run in headless mode (no GUI)


class Event:
    def __init__(self, handled=False):
        self.handled = handled


class MouseEvent(Event):
    def __init__(self, world_position, handled=False):
        super().__init__(handled)
        self.world_position = world_position


class MouseLeaveEvent(Event):
    def __init__(self, handled=False):
        super().__init__(handled)


class MouseEnterEvent(Event):
    def __init__(self, handled=False):
        super().__init__(handled)


class MouseWheelEvent(MouseEvent):
    def __init__(self, world_position, delta, handled=False):
        super().__init__(world_position, handled)
        self.delta = delta


class MouseDownEvent(MouseEvent):
    def __init__(self, world_position, handled=False):
        super().__init__(world_position, handled)


class MouseUpEvent(MouseEvent):
    def __init__(self, world_position, handled=False):
        super().__init__(world_position, handled)


class MouseMoveEvent(MouseEvent):
    def __init__(self, world_position, world_delta, handled=False):
        super().__init__(world_position, handled)
        self.world_delta = world_delta


class ClickEvent(MouseEvent):
    def __init__(self, world_position, handled=False):
        super().__init__(world_position, handled)


class DoubleClickEvent(MouseEvent):
    def __init__(self, world_position, handled=False):
        super().__init__(world_position, handled)


class TripleClickEvent(MouseEvent):
    def __init__(self, world_position, handled=False):
        super().__init__(world_position, handled)


class KeyDownEvent(Event):
    def __init__(self, key, ctrl=False, shift=False, meta=False, alt=False, handled=False):
        super().__init__(handled)
        self.key = key
        self.ctrl = ctrl
        self.shift = shift
        self.meta = meta
        self.alt = alt

    def __repr__(self):
        return f"KeyDownEvent(key={self.key}, ctrl={self.ctrl}, shift={self.shift}, meta={self.meta}, alt={self.alt})"


class KeyUpEvent(Event):
    def __init__(self, key, handled=False):
        super().__init__(handled)
        self.key = key


class MultiClickHandler:
    def __init__(self, delayed_time_ms, on_click, on_double_click=None, on_triple_click=None):
        self.delayed_time = delayed_time_ms / 1000.0
        self.first_click_time = None
        self.second_click_time = None

        self.on_click = on_click
        self.on_double_click = on_double_click
        self.on_triple_click = on_triple_click
        self.last_canvas_pos = None
        self.last_world_pos = None

    def update(self):
        if self.on_double_click is None and self.on_triple_click is None:
            return

        current_time = time.time()

        # check if times out
        if self.first_click_time is not None:
            if current_time - self.first_click_time > self.delayed_time:
                #  chance for a second click timed out, we can call the first click handler
                self.on_click(ClickEvent(world_position=self.last_world_pos))
                self.first_click_time = None
                self.second_click_time = None
            # else # we are still waiting for a second click

        if self.on_double_click is None:
            # if we don't have a double click handler, we can just call the click handler
            return
        if self.second_click_time is not None:
            if current_time - self.second_click_time > self.delayed_time:
                # chance for a triple click timed out, we can call the second click handler
                self.on_double_click(DoubleClickEvent(world_position=self.last_world_pos))
                self.first_click_time = None
                self.second_click_time = None

    def handle_click(self, world_position):
        if self.on_double_click is None and self.on_triple_click is None:
            # if we don't have a double or triple click handler, we can just call the click handler
            self.on_click(ClickEvent(world_position=world_position))
            return

        self.last_world_pos = world_position

        # if we have already a second click
        if self.second_click_time is not None:
            # this is a potential tripple click if
            # the time frame is still valid
            if time.time() - self.second_click_time <= self.delayed_time:
                self.on_triple_click(TripleClickEvent(world_position=self.last_world_pos))
            self.first_click_time = None
            self.second_click_time = None
            return
        else:
            if self.first_click_time is not None:
                # click is in time frame for a second click
                if self.on_triple_click is None:
                    self.on_double_click(DoubleClickEvent(world_position=self.last_world_pos))
                    self.first_click_time = None
                    self.second_click_time = None
                else:
                    self.second_click_time = time.time()
                    self.first_click_time = None

            else:
                # this is the first click
                self.first_click_time = time.time()
                self.second_click_time = None


class FrontendBase(ABC):
    Settings = FrontendBaseSettings

    def __init__(self, settings):
        self.settings = settings

        self.sample_class = None
        self.sample_settings = None
        self.change_sample_class_requested = False

        self.sample = None  # until the ui is ready, this will be None
        self.iteration = 0

        # record some timing information
        self.acc_debug_draw_time = 0
        self.acc_update_time = 0

        # sample update time
        self.sample_update_time = None
        self._multi_click_handler = None

        # the last time when the world was updated
        self.last_world_update_time = None

        # the dt for the physics update
        self.physics_update_dt = 1 / self.settings.hertz

        self._is_paused = False

        # store which key is currently pressed
        self._pressed_keys = set()

    def set_paused(self):
        self._is_paused = True
        self.last_world_update_time = None

    def set_running(self):
        self._is_paused = False

    def set_sample(self, sample_class, sample_settings=None):
        self.sample_class = sample_class
        self.sample_settings = sample_settings
        self.change_sample_class_requested = True

    def pre_new_sample(self, sample_class, sample_settings):
        # this can be overridden in derived classes
        pass

    def post_new_sample(self, sample_class, sample_settings):
        # this can be overridden in derived classes
        pass

    def _set_new_sample(self, sample_class, sample_settings):
        self.iteration = 0
        self.acc_debug_draw_time = 0
        self.acc_update_time = 0

        self.pre_new_sample(sample_class, sample_settings)
        # construct the sample
        self.sample = self.sample_class(self, self.sample_settings)

        # post new sample
        self.post_new_sample(sample_class, sample_settings)

        self.center_sample(margin_px=10)

        on_double_click = getattr(self.sample, "on_double_click", None)
        on_triple_click = getattr(self.sample, "on_triple_click", None)

        # install the click handlers
        self._multi_click_handler = MultiClickHandler(
            delayed_time_ms=self.settings.multi_click_delay_ms,
            on_click=self.sample.on_click,
            on_double_click=on_double_click,
            on_triple_click=on_triple_click,
        )

    def run(self, sample_class, sample_settings):
        self.sample_class = sample_class
        self.sample_settings = sample_settings

        # self._set_new_sample(sample_class, sample_settings)

        # call sample.update in a loop
        # depending on the frontend, this can
        # be blocking or non-blocking
        self.main_loop()

    def ui_is_ready(self):
        # derived classes *must* call this when the UI is ready
        # this is used to signal that the frontend is ready to run the sample
        self._set_new_sample(self.sample_class, self.sample_settings)

    def update_physics_single_step(self):
        dt = self.settings.speed / self.settings.hertz
        self.sample.pre_update(dt)
        self.sample.update(dt)
        self.sample.post_update(dt)

    def update_physics(self):
        if self._is_paused:
            # if we are paused, we don't update the physics
            return
        expected_dt = 1 / self.settings.hertz
        now = time.perf_counter()
        if self.last_world_update_time is None:
            self.update_physics_single_step()
            self.last_world_update_time = now
            return

        dt = now - self.last_world_update_time

        while dt >= expected_dt:
            self.update_physics_single_step()
            dt -= expected_dt
            self.last_world_update_time += expected_dt

    def update_frontend_logic(self):
        if self._is_paused:
            self._last_world_update_time = None
        # do we need to change the sample class?
        if self.change_sample_class_requested:
            self.change_sample_class_requested = False
            self.sample.post_run()
            self._set_new_sample(self.sample_class, self.sample_settings)

        # click handler update
        if self._multi_click_handler is not None:
            self._multi_click_handler.update()

    def draw_physics(self):
        t0 = time.time()
        if self.settings.debug_draw.enabled:
            self.debug_draw.begin_draw()

        self.sample.pre_debug_draw()
        if self.settings.debug_draw.enabled:
            self.sample.world.draw(self.debug_draw, call_begin_end=False)

        self.sample.post_debug_draw()

        if self.settings.debug_draw.enabled:
            self.debug_draw.end_draw()
        self.acc_debug_draw_time += time.time() - t0

    def stop(self):
        self.set_sample(self.sample_class, self.sample_settings)
        self.on_stop()

    def on_stop(self):
        """Called when the frontend is stopped."""
        # this can be overridden in derived classes
        pass

    def center_sample(self, sample, margin_px=10):
        raise NotImplementedError(
            "The center_sample method must be implemented in the derived class."
        )

    # this may not be applicable to all frontends
    def center_sample_with_transform(self, transform, margin_px=10):
        canvas_shape = self.settings.canvas_shape
        aabb = self.sample.aabb()

        # this default implementation of center_sample
        # assumes that there is a transform attribute in the sample
        world_lower_bound = aabb.lower_bound
        world_upper_bound = aabb.upper_bound

        world_shape = (
            world_upper_bound[0] - world_lower_bound[0],
            world_upper_bound[1] - world_lower_bound[1],
        )

        # add a margin
        needed_canvas_shape = (
            world_shape[0] * transform.ppm + margin_px * 2,
            world_shape[1] * transform.ppm + margin_px * 2,
        )
        # print(f"canvas_shape shape: {canvas_shape}, needed canvas shape: {needed_canvas_shape}")
        # if needed_canvas_shape[0] > canvas_shape[0] or needed_canvas_shape[1] > canvas_shape[1]:
        # get the factor to scale the current ppm
        factor = max(
            needed_canvas_shape[0] / canvas_shape[0],
            needed_canvas_shape[1] / canvas_shape[1],
        )
        transform.ppm /= factor

        canvas_lower_bound = transform.world_to_canvas(world_lower_bound)
        canvas_upper_bound = transform.world_to_canvas(world_upper_bound)
        canvas_lower_bound_new = (
            min(canvas_lower_bound[0], canvas_upper_bound[0]),
            min(canvas_lower_bound[1], canvas_upper_bound[1]),
        )
        canvas_upper_bound_new = (
            max(canvas_lower_bound[0], canvas_upper_bound[0]),
            max(canvas_lower_bound[1], canvas_upper_bound[1]),
        )
        canvas_lower_bound = canvas_lower_bound_new
        canvas_upper_bound = canvas_upper_bound_new

        needed_canvas_width = canvas_upper_bound[0] - canvas_lower_bound[0]
        needed_canvas_height = canvas_upper_bound[1] - canvas_lower_bound[1]

        lower_bound_should = (
            (canvas_shape[0] - needed_canvas_width) // 2,
            (canvas_shape[1] - needed_canvas_height) // 2,
        )
        world_lower_bound_should = (
            lower_bound_should[0] / transform.ppm,
            lower_bound_should[1] / transform.ppm,
        )
        world_delta = (
            world_lower_bound_should[0] - world_lower_bound[0],
            world_lower_bound_should[1] - world_lower_bound[1],
        )
        transform.offset = world_delta

    def is_paused(self):
        return self._is_paused

    @abstractmethod
    def drag_camera(self, delta):
        pass

    @abstractmethod
    def change_zoom(self, delta):
        pass

    @abstractmethod
    def main_loop(self):
        """Main loop of the frontend, where the sample is updated and drawn."""
        pass

    def add_widget(self, element):
        pass

    def is_key_pressed(self, key):
        """Check if a key is pressed."""
        return key in self._pressed_keys

    def pressed_keys(self):
        """Get the currently pressed keys set"""
        return self._pressed_keys

    def _on_key_down(self, event):
        """Handle key down events."""
        if event.key in self._pressed_keys:
            # if the key is already pressed, we don't add it again
            # this is because some frontend keep fireing the key down event
            # when the key is pressed
            # e.g. the ipycanvas frontend does this
            return
        self._pressed_keys.add(event.key)
        self.sample.on_key_down(event)

    def _on_key_up(self, event):
        """Handle key up events."""
        if event.key in self._pressed_keys:
            self._pressed_keys.remove(event.key)
        self.sample.on_key_up(event)
