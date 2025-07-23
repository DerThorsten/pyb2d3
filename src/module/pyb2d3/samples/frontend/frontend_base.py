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
class FrontendBaseSettings:
    canvas_shape: tuple = (1200, 1200)
    fps: int = 60
    substeps: int = 20
    ppm: float = 40.0  # Pixels per meter
    debug_draw: DebugDrawSettings = field(default_factory=DebugDrawSettings)
    multi_click_delay_ms: int = 350  # Delay in milliseconds to wait for multi-clicks


@dataclass(kw_only=True)
class Event:
    is_handled: bool = False


@dataclass
class MouseEvent(Event):
    world_position: tuple
    canvas_position: tuple


@dataclass
class MouseLeaveEvent(Event):
    pass


@dataclass
class MouseEnterEvent(Event):
    pass


@dataclass
class MouseWheelEvent(MouseEvent):
    delta: int


@dataclass
class MouseDownEvent(MouseEvent):
    pass


@dataclass
class MouseUpEvent(MouseEvent):
    pass


@dataclass
class MouseMoveEvent(MouseEvent):
    world_delta: tuple
    canvas_delta: tuple


@dataclass
class ClickEvent(MouseEvent):
    pass


@dataclass
class DoubleClickEvent(MouseEvent):
    pass


@dataclass
class TripleClickEvent(MouseEvent):
    pass


class MultiClickHandler:
    def __init__(
        self, delayed_time_ms, on_click, on_double_click=None, on_triple_click=None
    ):
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
                self.on_click(
                    ClickEvent(
                        world_position=self.last_world_pos,
                        canvas_position=self.last_canvas_pos,
                    )
                )
                self.first_click_time = None
                self.second_click_time = None
            # else # we are still waiting for a second click

        if self.on_double_click is None:
            # if we don't have a double click handler, we can just call the click handler
            return
        if self.second_click_time is not None:
            if current_time - self.second_click_time > self.delayed_time:
                # chance for a triple click timed out, we can call the second click handler
                self.on_double_click(
                    DoubleClickEvent(
                        world_position=self.last_world_pos,
                        canvas_position=self.last_canvas_pos,
                    )
                )
                self.first_click_time = None
                self.second_click_time = None

    def handle_click(self, world_position, canvas_position):
        if self.on_double_click is None and self.on_triple_click is None:
            # if we don't have a double or triple click handler, we can just call the click handler
            self.on_click(
                ClickEvent(
                    world_position=world_position, canvas_position=canvas_position
                )
            )
            return

        self.last_canvas_pos = canvas_position
        self.last_world_pos = world_position

        # if we have already a second click
        if self.second_click_time is not None:
            # this is a potential tripple click if
            # the time frame is still valid
            if time.time() - self.second_click_time <= self.delayed_time:
                self.on_triple_click(
                    TripleClickEvent(
                        world_position=self.last_world_pos,
                        canvas_position=self.last_canvas_pos,
                    )
                )
            self.first_click_time = None
            self.second_click_time = None
            return
        else:
            if self.first_click_time is not None:
                # click is in time frame for a second click
                if self.on_triple_click is None:
                    self.on_double_click(
                        DoubleClickEvent(
                            world_position=self.last_world_pos,
                            canvas_position=self.last_canvas_pos,
                        )
                    )
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

        self.sample = None

        self.iteration = 0

        # record some timing information
        self.debug_draw_time = None

        # sample update time
        self.sample_update_time = None

        self._multi_click_handler = None

    def set_sample(self, sample_class, sample_settings=None):
        self.sample_class = sample_class
        self.sample_settings = sample_settings
        self.change_sample_class_requested = True

    def _set_new_sample(self, sample_class, sample_settings):
        print("_set_new_sample called with", sample_class, sample_settings)
        # construct the sample
        self.sample = self.sample_class(self, self.sample_settings)

        self.center_sample(self.sample, margin_px=10)

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

        self._set_new_sample(sample_class, sample_settings)

        # call sample.update in a loop
        # depending on the frontend, this can
        # be blocking or non-blocking
        self.main_loop()

    def update_and_draw(self, dt):
        # do we need to change the sample class?
        if self.change_sample_class_requested:
            self.change_sample_class_requested = False
            self.sample.post_run()

            self._set_new_sample(self.sample_class, self.sample_settings)

        # click handler update
        if self._multi_click_handler:
            self._multi_click_handler.update()

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

    def center_sample(self, sample, margin_px=10):
        raise NotImplementedError(
            "The center_sample method must be implemented in the derived class."
        )

    # this may not be applicable to all frontends
    def center_sample_with_transform(self, sample, transform, margin_px=10):
        canvas_shape = self.settings.canvas_shape
        aabb = sample.aabb()

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
