from ...debug_draw.pygame_debug_draw import PygameDebugDraw
from .frontend_base import FrontendBase

import pyb2d3 as b2d
import pygame
import time
import sys


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

        pygame.display.set_caption("Hello World")
        self.debug_draw = PygameDebugDraw(transform=self.transform, screen=self.screen)
        self.debug_draw.draw_shapes = settings.debug_draw.draw_shapes
        self.debug_draw.draw_joints = settings.debug_draw.draw_joints

        self._last_canvas_mouse_pos = None

        # for double / tripple clicks, we need to keep track of the time of the last click

        self._last_click_time = None
        self._last_double_click_time = None

        print(
            f"Debug draw shapes: {self.debug_draw.draw_shapes}, joints: {self.debug_draw.draw_joints}"
        )

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
        self.center_sample(self.sample, self.transform)
        clock = self.clock

        # Set up font: None = default font
        font = pygame.font.Font(None, 48)  # size 48

        # Render the text to a surface
        text_surface = font.render("", True, (255, 255, 255))  # white text
        last_text = ""
        text_rect = text_surface.get_rect(center=(320, 240))  # center on screen

        iteration = 0
        acc_draw_time = 0.0

        while True:
            if self.settings.debug_draw.draw_background:
                self.screen.fill(self.settings.debug_draw.background_color)

            dt = clock.tick_busy_loop(self.settings.fps)
            dt = dt / 1000.0  # convert to seconds
            # print(f"FPS:{clock.get_fps() } dt: {dt}")

            # call the sample update methods (also pre and post update)
            # and call debug draw  (also pre and post debug draw)
            self.update_and_draw(dt)

            # draw fps  and average draw time
            fps = clock.get_fps()

            fps_rounded = round(fps, 2)
            new_text = f"FPS: {fps_rounded:.2f}  Draw : {self.debug_draw_time:.5f}  Update : {self.sample_update_time:.5f} I: {iteration}"
            if last_text != new_text:
                last_text = new_text
                text_surface = font.render(last_text, True, (255, 255, 255))
                text_rect = text_surface.get_rect(
                    center=(self.settings.canvas_shape[0] // 2, 30)
                )
            self.screen.blit(text_surface, text_rect)

            self._dispatch_events()

            pygame.display.update()

            iteration += 1

    def _dispatch_events(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # mouse events
            if event.type == pygame.MOUSEBUTTONDOWN:
                # only for left and right mouse buttons
                if event.button not in (1,):
                    continue

                # check for tripple-click first, then double-click
                mouse_pos = pygame.mouse.get_pos()
                self._last_canvas_mouse_pos = mouse_pos
                world_pos = self.transform.canvas_to_world(mouse_pos)
                self._multi_click_handler.handle_click(world_pos)

                self.sample.on_mouse_down(world_pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_pos = pygame.mouse.get_pos()
                self._last_canvas_mouse_pos = mouse_pos
                world_pos = self.transform.canvas_to_world(mouse_pos)
                self.sample.on_mouse_up(world_pos)
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                if self._last_canvas_mouse_pos is None:
                    self._last_canvas_mouse_pos = mouse_pos
                delta = (
                    mouse_pos[0] - self._last_canvas_mouse_pos[0],
                    mouse_pos[1] - self._last_canvas_mouse_pos[1],
                )
                self._last_canvas_mouse_pos = mouse_pos

                world_pos = self.transform.canvas_to_world(mouse_pos)

                # convert delta to world coordinates
                delta_world = (
                    delta[0] / self.transform.ppm,
                    -delta[1] / self.transform.ppm,
                )

                self.sample.on_mouse_move(world_pos, delta_world)
            # mouse-wheel
            elif event.type == pygame.MOUSEWHEEL:
                self.sample.on_mouse_wheel(event.y)
            # window leave
            elif event.type == pygame.WINDOWLEAVE:
                self.sample.on_mouse_leave()
            # window enter
            elif event.type == pygame.WINDOWENTER:
                self.sample.on_mouse_enter()
