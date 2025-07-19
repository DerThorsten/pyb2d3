from dataclasses import dataclass, field
import time

# abc meta
from abc import ABC, abstractmethod


@dataclass
class DebugDrawSettings:
    enabled: bool = True
    draw_shapes: bool = True
    draw_joints: bool = True
    draw_background: bool = True
    background_color: tuple = (46, 46, 46)


@dataclass
class EngineSettings:
    canvas_shape: tuple = (1200, 1200)
    fps: int = 60
    substeps: int = 20
    ppm: float = 40.0  # Pixels per meter
    debug_draw: DebugDrawSettings = field(default_factory=DebugDrawSettings)
    double_click_time_ms: int = 500  # Time in milliseconds to consider a double click


# same as above, but with abstract methods
class FrontendBase(ABC):

    Settings = EngineSettings

    def __init__(self, settings: EngineSettings):
        self.settings = settings
        self.sample_class = None
        self.sample = None

        self.iteration = 0

        # record some timing information
        self.debug_draw_time = None

        # sample update time
        self.sample_update_time = None

    def run(self, sample_class):
        self.sample_class = sample_class
        # construct the sample
        self.sample = self.sample_class()
        self.sample.frontend = self

        # call sample.update in a loop
        # depending on the frontend, this can
        # be blocking or non-blocking
        self.main_loop()

    def update_and_draw(self, dt):

        # update sample
        self.sample.pre_update(dt)
        t0 = time.time()
        self.sample.update(dt)
        self.sample_update_time = time.time() - t0
        self.sample.post_update(dt)

        # debug draw
        self.sample.pre_debug_draw()
        t0 = time.time()
        if self.settings.debug_draw.enabled:
            self.sample.world.draw(self.debug_draw)
        self.debug_draw_time = time.time() - t0
        self.sample.post_debug_draw()
        self.iteration += 1

    def center_sample(self, sample, transform):
        canvas_shape = self.settings.canvas_shape
        aabb = sample.aabb()

        # this default implementation of center_sample
        # assumes that there is a transform attribute in the sample
        world_lower_bound = aabb.lower_bound
        world_upper_bound = aabb.upper_bound

        canvas_lower_bound = transform.world_to_canvas(world_lower_bound)
        canvas_upper_bound = transform.world_to_canvas(world_upper_bound)
        canvas_lower_bound_new = min(canvas_lower_bound[0], canvas_upper_bound[0]), min(
            canvas_lower_bound[1], canvas_upper_bound[1]
        )
        canvas_upper_bound_new = max(canvas_lower_bound[0], canvas_upper_bound[0]), max(
            canvas_lower_bound[1], canvas_upper_bound[1]
        )
        canvas_lower_bound = canvas_lower_bound_new
        canvas_upper_bound = canvas_upper_bound_new

        needed_canvas_width = canvas_upper_bound[0] - canvas_lower_bound[0]
        needed_canvas_height = canvas_upper_bound[1] - canvas_lower_bound[1]
        lower_bound_should = (canvas_shape[0] - needed_canvas_width) // 2, (
            canvas_shape[1] - needed_canvas_height
        ) // 2
        world_lower_bound_should = (
            lower_bound_should[0] / transform.ppm,
            lower_bound_should[1] / transform.ppm,
        )
        world_delta = (
            world_lower_bound_should[0] - world_lower_bound[0],
            world_lower_bound_should[1] - world_lower_bound[1],
        )
        transform.offset = world_delta

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
