import pyb2d3 as b2d
from pyb2d3_sandbox.frontend_base import (
    FrontendDebugDraw,
    FrontendBase,
    MouseDownEvent,
    MouseUpEvent,
    MouseMoveEvent,
    MouseLeaveEvent,
    MouseEnterEvent,
    ClickEvent,
    DoubleClickEvent,
    TripleClickEvent,
)

import random
import time
from dataclasses import dataclass


class NoopDebugDraw(FrontendDebugDraw):
    def __init__(self):
        super().__init__()

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

    def draw_string(self, x, y, string):
        pass

    def draw_aabb(self, aabb, color):
        pass


class HeadlessTestFrontend(FrontendBase):
    @dataclass
    class Settings(FrontendBase.Settings):
        world_time_limit: float = 5.0

    def __init__(self, settings):
        super().__init__(settings)

        # to emulate clicks on a canvas, we use a "canvas-shape"
        # even though we are in headless mode
        self.transform = b2d.CanvasWorldTransform(
            canvas_shape=self.settings.canvas_shape,
            ppm=self.settings.ppm,
            offset=(0, 0),
        )

        # this debug draw is a no-op, since we are in headless mode
        self.debug_draw = NoopDebugDraw()
        self.debug_draw.draw_shapes = settings.debug_draw.draw_shapes
        self.debug_draw.draw_joints = settings.debug_draw.draw_joints

        self.mouse_down = False
        self.mouse_pos = b2d.Vec2(0, 0)
        self.mouse_in = False

    def drag_camera(self, delta):
        pass

    def change_zoom(self, delta):
        pass

    def main_loop(self):
        self.ui_is_ready()
        n_steps = int(self.settings.world_time_limit * self.settings.hertz)

        for i in range(n_steps):
            self.update_frontend_logic()
            if self.sample.is_done():
                break
            self.fire_random_event()
            self.update_physics_single_step()
            self.draw_physics()

        self.sample.post_run()

    def fire_random_event(self):
        # 30% for no event
        if random.random() < 0.3:
            return

        # enter / leave mouse events
        if not self.mouse_in:
            # 90 % chance for a mouse enter event
            if random.random() < 0.9:
                self.sample.on_mouse_enter(MouseEnterEvent())
                self.mouse_in = True

            return
        else:
            # 10 % chance for a mouse leave event
            if random.random() < 0.1:
                self.sample.on_mouse_leave(MouseLeaveEvent())
                self.mouse_in = False
                return

        # 50 % chance for a mouse move event
        if random.random() < 0.70:
            left_margin = int(self.mouse_pos[0])
            right_margin = int(self.settings.canvas_shape[0] - self.mouse_pos[0])
            top_margin = int(self.mouse_pos[1])
            bottom_margin = int(self.settings.canvas_shape[1] - self.mouse_pos[1])

            delta = b2d.Vec2(
                random.randint(-min(left_margin, 10), min(right_margin, 10)),
                random.randint(-min(top_margin, 10), min(bottom_margin, 10)),
            )
            new_pos = self.mouse_pos + delta

            assert 0 <= new_pos[0] < self.settings.canvas_shape[0]
            assert 0 <= new_pos[1] < self.settings.canvas_shape[1]

            world_delta = (
                delta[0] / self.transform.ppm,
                -delta[1] / self.transform.ppm,
            )
            self.mouse_pos = new_pos

            self.sample.on_mouse_move(
                MouseMoveEvent(
                    world_position=self.transform.canvas_to_world(new_pos),
                    world_delta=world_delta,
                )
            )
            return

        # 30 % for a tripple click if the sample has "on_triple_click" method
        if hasattr(self.sample, "on_triple_click") and random.random() < 0.3:
            # tripple click

            self.sample.on_triple_click(
                TripleClickEvent(
                    world_position=self.transform.canvas_to_world(self.mouse_pos)
                )
            )
            return

        # 30 % for a double click if the sample has "on_double_click" method
        if hasattr(self.sample, "on_double_click") and random.random() < 0.3:
            # double click
            self.sample.on_double_click(
                DoubleClickEvent(
                    world_position=self.transform.canvas_to_world(self.mouse_pos)
                )
            )
            return

        if self.mouse_down:
            # 20 % chance for a mouse up event
            if random.random() < 0.2:
                self.mouse_down = False
                self.sample.on_mouse_up(
                    MouseUpEvent(
                        world_position=self.transform.canvas_to_world(self.mouse_pos),
                    )
                )
                return
        else:
            # 20 % chance for a mouse down event
            if random.random() < 0.2:
                self.mouse_down = True
                self.sample.on_mouse_down(
                    MouseDownEvent(
                        world_position=self.transform.canvas_to_world(self.mouse_pos),
                    )
                )
                self.sample.on_click(
                    ClickEvent(
                        world_position=self.transform.canvas_to_world(self.mouse_pos),
                    )
                )
                return

    def center_sample(self, margin_px=10):
        self.center_sample_with_transform(transform=self.transform, margin_px=margin_px)


def run_in_headless_test_frontend(sample_class, sample_settings=None, repeats=10):
    frontend_settings = HeadlessTestFrontend.Settings()

    total_time_budget_sec = 1

    print(f"Running sample: {sample_class.__name__} ")
    t0 = time.time()
    # run(
    #     sample_class=sample_class,
    #     sample_settings=sample_settings,
    #     frontend_class=HeadlessTestFrontend,
    #     frontend_settings=frontend_settings,
    # )

    sample_class.run(
        sample_settings=sample_settings,
        frontend_class=HeadlessTestFrontend,
        frontend_settings=frontend_settings,
    )

    elapsed_time = time.time() - t0
    time_left = total_time_budget_sec - elapsed_time

    print(f"Sample {sample_class.__name__} took {elapsed_time:.2f} seconds to run.")

    if time_left > elapsed_time:
        repeats = int(time_left / elapsed_time)
        repeats = min(repeats, 4)  # Limit to 5 repeats in total (4 additional runs)
        for i in range(repeats):
            print(
                f"Running sample: {sample_class.__name__}  {i + 2} / {repeats + 1} time(s)"
            )
            sample_class.run(
                sample_settings=sample_settings,
                frontend_class=HeadlessTestFrontend,
                frontend_settings=frontend_settings,
            )
