from .frontend_base import (
    FrontendDebugDraw,
    FrontendBase,
    MouseDownEvent,
    MouseUpEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    MouseLeaveEvent,
    MouseEnterEvent,
)

import pyb2d3 as b2d
import pygame
import sys


class PygameDebugDraw(FrontendDebugDraw):
    def __init__(self, transform, screen):
        self.screen = screen
        self.transform = transform

        self.font_cache = {}
        super().__init__()

    def convert_hex_color(self, hex_color):
        # we have a hexadecimal color **as integer**
        r = (hex_color >> 16) & 0xFF
        g = (hex_color >> 8) & 0xFF
        b = hex_color & 0xFF
        return (r, g, b)

    def world_to_canvas(self, point):
        return self.transform.world_to_canvas((float(point[0]), float(point[1])))

    def maybe_world_to_canvas(self, point, world_coordinates=True):
        if not world_coordinates:
            return point
        return self.transform.world_to_canvas(point)

    def maybe_scale(self, value, world_coordinates=True):
        if world_coordinates:
            return self.transform.scale_world_to_canvas(value)
        return value

    def draw_polygon(
        self, vertices, color, line_width, width_in_pixels=False, world_coordinates=True
    ):
        if not width_in_pixels and world_coordinates:
            line_width = self.transform.scale_world_to_canvas(line_width)
        if world_coordinates:
            vertices = [self.world_to_canvas(v) for v in vertices]
        pygame.draw.polygon(
            self.screen,
            color,
            vertices,
            round(line_width),
        )

    def draw_solid_polygon(self, points, color, world_coordinates=True):
        if world_coordinates:
            points = [self.world_to_canvas(v) for v in points]
        pygame.draw.polygon(self.screen, color, points, 0)

    def draw_circle(
        self,
        center,
        radius,
        line_width,
        color,
        width_in_pixels=False,
        world_coordinates=True,
    ):
        if not width_in_pixels and world_coordinates:
            line_width = self.transform.scale_world_to_canvas(line_width)
        if world_coordinates:
            center = self.world_to_canvas(center)
            radius = self.transform.scale_world_to_canvas(radius)

        pygame.draw.circle(
            self.screen,
            color,
            center,
            radius,
            round(line_width),
        )

    def draw_solid_circle(self, center, radius, color, world_coordinates=True):
        if world_coordinates:
            center = self.world_to_canvas(center)
            radius = self.transform.scale_world_to_canvas(radius)
        pygame.draw.circle(
            self.screen,
            color,
            center,
            radius,
            0,
        )

    def draw_line(
        self, p1, p2, line_width, color, width_in_pixels=False, world_coordinates=True
    ):
        if not width_in_pixels and world_coordinates:
            line_width = self.transform.scale_world_to_canvas(line_width)
        if world_coordinates:
            p1 = self.world_to_canvas(p1)
            p2 = self.world_to_canvas(p2)
        pygame.draw.line(
            self.screen,
            color,
            p1,
            p2,
            round(line_width),
        )

    def _get_font(self, font_size):
        if font_size not in self.font_cache:
            # create a new font
            font = pygame.font.Font(None, font_size)
            self.font_cache[font_size] = font
        else:
            font = self.font_cache[font_size]
        return font

    def draw_text(
        self,
        position,
        text,
        color,
        font_size,
        alignment="center",
        world_coordinates=True,
    ):
        if world_coordinates:
            position = self.world_to_canvas(position)
            font_size = self.transform.scale_world_to_canvas(font_size)

        font = self._get_font(font_size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if alignment == "center":
            text_rect.center = position
        elif alignment == "left":
            text_rect.topleft = position
        elif alignment == "right":
            text_rect.topright = position
        elif alignment == "top":
            text_rect.midtop = position
        elif alignment == "bottom":
            text_rect.midbottom = position
        else:
            raise ValueError(f"Unknown alignment: {alignment}")

        self.screen.blit(text_surface, text_rect)


class PygameFrontend(FrontendBase):
    Settings = FrontendBase.Settings

    def __init__(self, settings):
        super().__init__(settings)

        pygame.init()
        self.screen = pygame.display.set_mode(
            self.settings.canvas_shape, pygame.SRCALPHA
        )
        self.clock = pygame.time.Clock()
        self.transform = b2d.CanvasWorldTransform(
            canvas_shape=self.settings.canvas_shape,
            ppm=self.settings.ppm,
            offset=(0, 0),
        )

        # pygame.display.set_caption("Hello World")
        self.debug_draw = PygameDebugDraw(transform=self.transform, screen=self.screen)
        self.debug_draw.draw_shapes = settings.debug_draw.draw_shapes
        self.debug_draw.draw_joints = settings.debug_draw.draw_joints

        self._last_canvas_mouse_pos = None

        # for double / tripple clicks, we need to keep track of the time of the last click

        self._last_click_time = None
        self._last_double_click_time = None

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
        # center the sample in the canvas

        clock = self.clock

        # Set up font: None = default font
        # font = pygame.font.Font(None, 48)  # size 48
        # # Render the text to a surface
        # text_surface = font.render("", True, (255, 255, 255))  # white text
        # last_text = ""
        # text_rect = text_surface.get_rect(center=(320, 240))  # center on screen

        while not self.sample.is_done():
            if self.settings.debug_draw.draw_background:
                self.screen.fill(self.settings.debug_draw.background_color)

            dt = clock.tick_busy_loop(self.settings.fps)
            dt = dt / 1000.0  # convert to seconds

            # call the sample update methods (also pre and post update)
            # and call debug draw  (also pre and post debug draw)
            self.update_and_draw(dt)

            # draw fps  and average draw time
            # fps = clock.get_fps()
            # fps_rounded = round(fps, 2)
            # new_text = f"FPS: {fps_rounded:.2f}  Draw : {self.debug_draw_time:.5f}  Update : {self.sample_update_time:.5f} I: {self.iteration}"
            # if last_text != new_text:
            #     last_text = new_text
            #     text_surface = font.render(last_text, True, (255, 255, 255))
            #     text_rect = text_surface.get_rect(
            #         center=(self.settings.canvas_shape[0] // 2, 30)
            #     )
            # self.screen.blit(text_surface, text_rect)

            self._dispatch_events()

            pygame.display.update()

        self.sample.post_run()

    def center_sample(self, sample, margin_px=10):
        # center the sample in the canvas
        self.center_sample_with_transform(sample, self.transform, margin_px)

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
                self._multi_click_handler.handle_click(
                    world_position=world_pos, canvas_position=canvas_position
                )
                self.sample.on_mouse_down(
                    MouseDownEvent(
                        world_position=world_pos, canvas_position=canvas_position
                    )
                )
            elif event.type == pygame.MOUSEBUTTONUP:
                # only for left
                if event.button not in (1,):
                    continue
                canvas_position = b2d.Vec2(pygame.mouse.get_pos())
                self._last_canvas_mouse_pos = canvas_position
                world_pos = self.transform.canvas_to_world(canvas_position)
                self.sample.on_mouse_up(
                    MouseUpEvent(
                        world_position=world_pos, canvas_position=canvas_position
                    )
                )
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
                    MouseMoveEvent(
                        world_position=world_pos,
                        canvas_position=canvas_position,
                        world_delta=delta_world,
                        canvas_delta=canvas_delta,
                    )
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
                        canvas_position=canvas_position,
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
