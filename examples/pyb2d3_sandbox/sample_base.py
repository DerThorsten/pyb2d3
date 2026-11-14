import pyb2d3 as b2d
# from .frontend import run

from pyb2d3_sandbox.default_frontend import get_default_frontend
from pyb2d3_sandbox.registry import registry as default_registry

from dataclasses import dataclass
import weakref


@dataclass
class SampleBaseSettings:
    gravity: tuple = (0, -10)

    def set_gravity(self, gravity):
        self.gravity = gravity
        return self


class SampleBase(object):
    Settings = SampleBaseSettings

    # sub-steps per world step for this sample (None: the frontend's setting); e.g. long
    # chains of joints need more
    substeps = None

    # classmethod
    @classmethod
    def run(cls, sample_settings=None, frontend_class=None, frontend_settings=None, registry=None):
        if sample_settings is None:
            sample_settings = cls.Settings()
        if frontend_class is None:
            frontend_class = get_default_frontend()

        if isinstance(frontend_settings, dict):
            frontend_settings = frontend_class.Settings(**frontend_settings)
        elif frontend_settings is None:
            frontend_settings = frontend_class.Settings()

        frontend = frontend_class(settings=frontend_settings)
        if registry is not None:
            frontend.registry = registry
        frontend.run(cls, sample_settings=sample_settings)
        return frontend

    def __del__(self):
        self.world.destroy()
        self.world = None

    @property
    def frontend(self):
        return self._frontend()

    def __init__(self, frontend, settings=SampleBaseSettings(), world=None):
        # this created a cycle, so we need to break it
        self._frontend = weakref.ref(frontend)
        self.settings = settings
        self.world = world

        if b2d.WITH_THREADING:
            pool = b2d.ThreadPool()
        else:
            pool = None
        if self.world is None:
            self.world = b2d.World(gravity=settings.gravity, thread_pool=pool)

        # create an anchor body for joints
        self.anchor_body = self.world.create_static_body(position=(0, 0))

        # dragging bodies with the mouse (box2d >= 3.2 has no mouse joint)
        self._mouse_drag = b2d.MouseDrag(self.world)
        self._camera_drag = False

        self.is_mouse_down = False
        self.mouse_pos = None

        # world time (ie time in the simulation)
        self.world_time = 0.0
        self.world_iteration = 0

    # mouse drag tuning (kept under the old "mouse_joint" names)
    @property
    def mouse_joint_body(self):
        return self._mouse_drag.body

    @property
    def mouse_joint_hertz(self):
        return self._mouse_drag.hertz

    @mouse_joint_hertz.setter
    def mouse_joint_hertz(self, value):
        self._mouse_drag.hertz = value

    @property
    def mouse_joint_damping_ratio(self):
        return self._mouse_drag.damping_ratio

    @mouse_joint_damping_ratio.setter
    def mouse_joint_damping_ratio(self, value):
        self._mouse_drag.damping_ratio = value

    @property
    def mouse_joint_force_multiplier(self):
        """max pulling force as a multiple of the dragged body's weight"""
        return self._mouse_drag.force_scale

    @mouse_joint_force_multiplier.setter
    def mouse_joint_force_multiplier(self, value):
        self._mouse_drag.force_scale = value

    # some properties for the frontend
    @property
    def debug_draw(self):
        return self.frontend.debug_draw

    @property
    def canvas_shape(self):
        return self.frontend.settings.canvas_shape

    def update(self, dt):
        # Update the world with the given time step
        self._mouse_drag.step(dt)
        self.world.step(dt, self.substeps or self.frontend.settings.substeps)
        self.world_time += dt
        self.world_iteration += 1

    def pre_update(self, dt):
        # Pre-update logic, if any
        pass

    def post_update(self, dt):
        # Post-update logic, if any
        pass

    def pre_debug_draw(self):
        # Pre-debug draw logic, if any
        pass

    def post_debug_draw(self):
        # Post-debug draw logic, if any
        pass

    def post_run(self):
        # Post-run logic, if any
        pass

    def on_click(self, pos):
        pass

    # this is only used
    def is_done(self):
        return False

    # on_double_click and  on_triple_click can be implemented in derived classes
    # but if these methods are not present, we dont need to delay
    # the "on_click" event to wait for a possible double/triple click.
    # To be able to perform the check if the user has implemented these methods,
    # we wont implement them here.

    # def on_double_click(self, pos):
    #     pass

    # def on_triple_click(self, pos):
    #     pass

    def on_mouse_down(self, event):
        self.is_mouse_down = True
        self.mouse_pos = event.world_position
        body = self._mouse_drag.begin(self.mouse_pos)
        if body is not None:
            body.awake = True
        else:
            self._camera_drag = True

    def destroy_mouse_joint(self):
        self._mouse_drag.end()

    def on_mouse_up(self, event):
        # Handle mouse up events
        self.mouse_pos = event.world_position
        self._camera_drag = False
        self.is_mouse_down = False
        self.destroy_mouse_joint()

    def on_mouse_move(self, event):
        if self._mouse_drag.active:
            assert self.is_mouse_down, "Mouse drag should only be updated when mouse is down"
            self._mouse_drag.update(event.world_position)
        elif self._camera_drag:
            # If dragging the camera, update the camera position
            # delta = (pos[0] - self.mouse_pos[0], pos[1] - self.mouse_pos[1])
            self.frontend.drag_camera(event.world_delta)

        self.mouse_pos = event.world_position

    def on_mouse_leave(self, event):
        # Handle mouse leave events
        self.mouse_pos = None
        self.is_mouse_down = False
        self._camera_drag = False
        self.destroy_mouse_joint()

    def on_mouse_enter(self, event):
        # Handle mouse enter events
        pass

    def on_mouse_wheel(self, event):
        # Handle mouse wheel events
        self.frontend.change_zoom(event.delta)

    def is_key_pressed(self, key):
        return self.frontend.is_key_pressed(key)

    def pressed_keys(self):
        return self.frontend.pressed_keys()

    def on_key_down(self, event):
        # print("Key down:", event.key)
        pass

    def on_key_up(self, event):
        pass


def run_sample_browser(start=None, registry=None, frontend_class=None, frontend_settings=None):
    """Run the registered samples in a browser (the frontend can switch between them).

    `start` is the first sample: a 'Category/Name' key, a sample class, or None for
    the first registered sample.
    """
    registry = registry if registry is not None else default_registry
    if not len(registry):
        raise ValueError("no samples registered")
    if start is None:
        sample_class = registry.samples()[0].cls
    elif isinstance(start, str):
        sample_class = registry.get(start).cls
    else:
        sample_class = start
    return sample_class.run(
        frontend_class=frontend_class,
        frontend_settings=frontend_settings,
        registry=registry,
    )
