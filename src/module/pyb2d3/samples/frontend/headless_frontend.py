from ...debug_draw.noop_debug_draw import NoOpDebugDraw
from .frontend_base import FrontendBase

# dataclass for settings
from dataclasses import dataclass

import pyb2d3 as b2d
import pygame
import time
import sys


class HeadlessFrontend(FrontendBase):

    @dataclass
    class Settings(FrontendBase.Settings):
        world_time_limit: float = 10.0

    def __init__(self, settings):
        super().__init__(settings)

        # this debug draw is a no-op, since we are in headless mode
        self.debug_draw = NoopDebugDraw()
        self.debug_draw.draw_shapes = settings.debug_draw.draw_shapes
        self.debug_draw.draw_joints = settings.debug_draw.draw_joints

    def drag_camera(self, delta):
        pass

    def change_zoom(self, delta):
        pass

    def main_loop(self):

        n_steps = self.settings.world_time_limit / self.settings.dt
