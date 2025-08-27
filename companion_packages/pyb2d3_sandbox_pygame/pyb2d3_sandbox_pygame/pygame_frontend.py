from pyb2d3_sandbox.frontend_base import (
    FrontendDebugDraw,
    FrontendBase,
    MouseDownEvent,
    MouseUpEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    MouseLeaveEvent,
    MouseEnterEvent,
    KeyDownEvent,
    KeyUpEvent,
)

from dataclasses import dataclass, field
import pyb2d3 as b2d
import pygame
import sys
import os

X_AXIS = b2d.Vec2(1, 0)
Y_AXIS = b2d.Vec2(0, 1)


class PygameDebugDraw(FrontendDebugDraw):
    def __init__(self, transform, screen):
        self.screen = screen
        self.transform = transform

        self.font_cache = {}

        # helper to speed up drawing of capsules
        self._capsule_builder = b2d.CapsuleBuilderWithTransform(
            transform=self.transform,
            max_circle_segments=10,
        )
        self._capsule_vertices_buffer = self._capsule_builder.get_vertices_buffer()

        super().__init__()

    def _get_font(self, font_size):
        if font_size not in self.font_cache:
            # create a new font
            font = pygame.font.Font(None, font_size)
            self.font_cache[font_size] = font
        else:
            font = self.font_cache[font_size]
        return font

    def convert_hex_color(self, hex_color):
        # we have a hexadecimal color **as integer**
        r = (hex_color >> 16) & 0xFF
        g = (hex_color >> 8) & 0xFF
        b = hex_color & 0xFF
        return (r, g, b)

    def world_to_canvas(self, point):
        return self.transform.world_to_canvas((float(point[0]), float(point[1])))

    def draw_polygon(self, points, color):
        # convert vertices to canvas coordinates
        canvas_vertices = [self.world_to_canvas(v) for v in points]
        pygame.draw.polygon(self.screen, color, canvas_vertices, 1)

    def draw_solid_polygon(self, transform, points, radius, color):
        if radius <= 0:
            canvas_vertices = [self.world_to_canvas(transform.transform_point(v)) for v in points]
            pygame.draw.polygon(self.screen, color, canvas_vertices, 0)
        else:
            self._poor_mans_draw_solid_rounded_polygon(
                points=points, transform=transform, radius=radius, color=color
            )

    def draw_circle(self, center, radius, color):
        # convert center to canvas coordinates
        canvas_center = self.world_to_canvas(center)
        canvas_radius = self.transform.scale_world_to_canvas(radius)
        pygame.draw.circle(self.screen, color, canvas_center, int(canvas_radius + 0.5), 1)

    def draw_solid_circle(self, transform, radius, color):
        # convert center to canvas coordinates
        canvas_center = self.world_to_canvas(transform.p)
        canvas_radius = self.transform.scale_world_to_canvas(radius)
        pygame.draw.circle(self.screen, color, canvas_center, int(canvas_radius + 0.5), 0)

    def draw_segment(self, p1, p2, color):
        # convert points to canvas coordinates
        canvas_p1 = self.world_to_canvas(p1)
        canvas_p2 = self.world_to_canvas(p2)
        pygame.draw.aaline(self.screen, color, canvas_p1, canvas_p2)

    def draw_transform(self, transform):
        world_pos = transform.p
        canvas_pos = self.world_to_canvas(world_pos)

        world_x_axis = world_pos + transform.transform_point(X_AXIS)
        world_y_axis = world_pos + transform.transform_point(Y_AXIS)

        x_axis = self.world_to_canvas(world_x_axis)
        y_axis = self.world_to_canvas(world_y_axis)

        pygame.draw.line(self.screen, (255, 0, 0), canvas_pos, x_axis, 1)
        pygame.draw.line(self.screen, (0, 255, 0), canvas_pos, y_axis, 1)

    def draw_point(self, p, size, color):
        # convert point to canvas coordinates
        canvas_point = self.world_to_canvas(p)
        # canvas_size = self.transform.scale_world_to_canvas(size)
        pygame.draw.circle(self.screen, color, canvas_point, int(size / 2 + 0.5), 0)

    def draw_string(self, x, y, string):
        # convert position to canvas coordinates
        canvas_pos = self.world_to_canvas((x, y))
        font = self._get_font(20)
        text_surface = font.render(string, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=canvas_pos)
        self.screen.blit(text_surface, text_rect)

    def draw_solid_capsule(self, p1, p2, radius, color):
        n_vertices = self._capsule_builder.build(p1, p2, radius)
        canvas_vertices = self._capsule_vertices_buffer[0:n_vertices]
        pygame.draw.polygon(self.screen, color, canvas_vertices, 0)


@dataclass
class PygameHeadlessSettings:
    screenshot_callback: callable = None
    world_time_limit: float = 5.0


@dataclass
class PygameFrontendSettings(FrontendBase.Settings):
    headless_settings: PygameHeadlessSettings = field(default_factory=PygameHeadlessSettings)


class PygameFrontend(FrontendBase):
    Settings = FrontendBase.Settings

    def __init__(self, settings):
        super().__init__(settings)

        canvas_shape = settings.canvas_shape
        ppm = settings.ppm

        self.transform = b2d.CanvasWorldTransform(
            canvas_shape=canvas_shape,
            ppm=ppm,
            offset=(0, 0),
        )

        headless = settings.headless
        if not headless:
            pygame.init()
            self.screen = pygame.display.set_mode(self.settings.canvas_shape)
            self.clock = pygame.time.Clock()
        else:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.init()
            pygame.display.set_mode((1, 1))
            self.screen = pygame.Surface(self.settings.canvas_shape)

        self.debug_draw = PygameDebugDraw(transform=self.transform, screen=self.screen)

        self.debug_draw.draw_shapes = settings.debug_draw.draw_shapes
        self.debug_draw.draw_joints = settings.debug_draw.draw_joints

        self._last_canvas_mouse_pos = None

        # for double / tripple clicks, we need to keep track of the time of the last click

        self._last_click_time = None
        self._last_double_click_time = None

        self.font = pygame.font.Font(None, 20)

    def drag_camera(self, delta):
        # drag the camera by the given delta
        self.transform.offset = (
            self.transform.offset[0] + delta[0],
            self.transform.offset[1] + delta[1],
        )

    def change_zoom(self, delta):
        current_mouse_world_pos = self.transform.canvas_to_world(pygame.mouse.get_pos())

        # change the zoom by the given delta
        new_ppm = self.transform.ppm + delta
        if new_ppm > 0:
            self.transform.ppm = new_ppm

        # new mouse world position after zoom
        new_mouse_world_pos = self.transform.canvas_to_world(pygame.mouse.get_pos())

        delta = (
            new_mouse_world_pos[0] - current_mouse_world_pos[0],
            new_mouse_world_pos[1] - current_mouse_world_pos[1],
        )
        # adjust the offset to keep the mouse position in the same place
        self.transform.offset = (
            self.transform.offset[0] + delta[0],
            self.transform.offset[1] + delta[1],
        )

    def main_loop(self):
        self.ui_is_ready()
        if self.settings.headless:
            self._main_loop_headless()
        else:
            self._main_loop_non_headless()

    def _main_loop_headless(self):
        iteration = 0
        while not self.sample.is_done():
            if self.sample.world_time >= self.settings.headless_settings.world_time_limit:
                break

            if self.settings.debug_draw.draw_background:
                self.screen.fill(self.settings.debug_draw.background_color)
            self.update_frontend_logic()
            self.update_physics_single_step()
            self.draw_physics()

            if self.settings.headless_settings.screenshot_callback:
                self.settings.headless_settings.screenshot_callback(
                    screen=self.screen,
                    world_time=self.sample.world_time,
                    iteration=iteration,
                )
            iteration += 1

        self.sample.post_run()

    def _main_loop_non_headless(self):
        # center the sample in the canvas
        clock = pygame.time.Clock()
        while not self.sample.is_done():
            if self.settings.debug_draw.draw_background:
                self.screen.fill(self.settings.debug_draw.background_color)

            self.update_frontend_logic()
            self.update_physics()
            self._dispatch_events()
            self.draw_physics()

            # RENDER FPS
            clock.tick()
            fps = clock.get_fps()

            font = self.font
            text_surface = font.render(f"FPS: {fps:.2f}", True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(10, 10))
            self.screen.blit(text_surface, text_rect)

            pygame.display.update()

        self.sample.post_run()

    def center_sample(self, margin_px=10):
        # center the sample in the canvas
        self.center_sample_with_transform(self.transform, margin_px)

    def _dispatch_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # mouse events
            if event.type == pygame.MOUSEBUTTONDOWN:
                # only for left
                if event.button not in (1,):
                    continue

                # check for tripple-click first, then double-click
                canvas_position = b2d.Vec2(pygame.mouse.get_pos())
                self._last_canvas_mouse_pos = canvas_position
                world_pos = self.transform.canvas_to_world(canvas_position)
                self._multi_click_handler.handle_click(world_position=world_pos)
                self.sample.on_mouse_down(MouseDownEvent(world_position=world_pos))
            elif event.type == pygame.MOUSEBUTTONUP:
                # only for left
                if event.button not in (1,):
                    continue
                canvas_position = b2d.Vec2(pygame.mouse.get_pos())
                self._last_canvas_mouse_pos = canvas_position
                world_pos = self.transform.canvas_to_world(canvas_position)
                self.sample.on_mouse_up(MouseUpEvent(world_position=world_pos))
            elif event.type == pygame.MOUSEMOTION:
                canvas_position = b2d.Vec2(pygame.mouse.get_pos())
                if self._last_canvas_mouse_pos is None:
                    self._last_canvas_mouse_pos = canvas_position

                canvas_delta = canvas_position - self._last_canvas_mouse_pos
                self._last_canvas_mouse_pos = canvas_position

                world_pos = self.transform.canvas_to_world(canvas_position)

                # convert delta to world coordinates
                delta_world = (
                    canvas_delta[0] / self.transform.ppm,
                    -canvas_delta[1] / self.transform.ppm,
                )

                self.sample.on_mouse_move(
                    MouseMoveEvent(world_position=world_pos, world_delta=delta_world)
                )
            # mouse-wheel
            elif event.type == pygame.MOUSEWHEEL:
                # self.sample.on_mouse_wheel(event.y / 5.0)
                canvas_position = pygame.mouse.get_pos()
                self._last_canvas_mouse_pos = canvas_position
                world_pos = self.transform.canvas_to_world(canvas_position)
                self.sample.on_mouse_wheel(
                    MouseWheelEvent(
                        world_position=world_pos,
                        delta=event.y / 5.0,
                    )
                )
            # window leave
            elif event.type == pygame.WINDOWLEAVE:
                # self.sample.on_mouse_leave()
                self.sample.on_mouse_leave(MouseLeaveEvent())
                self._last_canvas_mouse_pos = None
                self._last_world_mouse_pos = None

            # window enter
            elif event.type == pygame.WINDOWENTER:
                self.sample.on_mouse_enter(MouseEnterEvent())
                self._last_canvas_mouse_pos = None
                self._last_world_mouse_pos = None

            # keydown
            elif event.type == pygame.KEYDOWN:
                # # ignore modifier keys
                # if event.key in KEY_MODIFIER_SET:
                #     continue

                key_name = pygame.key.name(event.key)
                # remove left / right
                if key_name.startswith("left ") or key_name.startswith("right "):
                    key_name = key_name.split(" ", 1)[1]

                ctrl = (event.mod & pygame.KMOD_CTRL) != 0
                shift = (event.mod & pygame.KMOD_SHIFT) != 0
                meta = (event.mod & pygame.KMOD_META) != 0
                alt = (event.mod & pygame.KMOD_ALT) != 0
                self._on_key_down(
                    KeyDownEvent(
                        key=key_name,
                        ctrl=ctrl,
                        shift=shift,
                        meta=meta,
                        alt=alt,
                    )
                )

            # keyup
            elif event.type == pygame.KEYUP:
                key_name = pygame.key.name(event.key)
                self._on_key_up(KeyUpEvent(key=key_name))
