import pyb2d3 as b2d
# from .frontend import run

from pyb2d3_sandbox.default_frontend import get_default_frontend

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

    # classmethod
    @classmethod
    def run(cls, sample_settings=None, frontend_class=None, frontend_settings=None):
        if sample_settings is None:
            sample_settings = cls.Settings()
        if frontend_class is None:
            frontend_class = get_default_frontend()
        if frontend_settings is None:
            frontend_settings = frontend_class.Settings()

        frontend = frontend_class(settings=frontend_settings)
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

        self._mouse_joint = None
        self.mouse_joint_body = None
        self._camera_drag = False

        self.is_mouse_down = False
        self.mouse_pos = None

        # world time (ie time in the simulation)
        self.world_time = 0.0
        self.world_iteration = 0

        self.mouse_joint_hertz = 100.0
        self.mouse_joint_force_multiplier = 500.0
        self.mouse_joint_damping_ratio = 1.0

    # some properties for the frontend
    @property
    def debug_draw(self):
        return self.frontend.debug_draw

    @property
    def canvas_shape(self):
        return self.frontend.settings.canvas_shape

    def update(self, dt):
        # Update the world with the given time step
        self.world.step(dt, self.frontend.settings.substeps)
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
        body = self.world.dynamic_body_at_point(self.mouse_pos)
        if body:
            # wake body up
            body.awake = True
            self.mouse_joint_body = body
            self._mouse_joint = self.world.create_mouse_joint(
                body_a=self.anchor_body,
                body_b=self.mouse_joint_body,
                target=self.mouse_pos,
                hertz=self.mouse_joint_hertz,
                max_force=self.mouse_joint_body.mass * self.mouse_joint_force_multiplier,
                damping_ratio=self.mouse_joint_damping_ratio,
            )
        else:
            self._camera_drag = True

    def destroy_mouse_joint(self):
        if self._mouse_joint is not None:
            self._mouse_joint.destroy()
        self._mouse_joint = None
        self.connected_body = None

    def on_mouse_up(self, event):
        # Handle mouse up events
        self.mouse_pos = event.world_position
        self._camera_drag = False
        self.is_mouse_down = False
        self.destroy_mouse_joint()

    def on_mouse_move(self, event):
        if self._mouse_joint is not None:
            if not self.mouse_joint_body.is_valid():
                self.destroy_mouse_joint()
                return

            assert self.is_mouse_down, "Mouse joint should only be updated when mouse is down"
            self._mouse_joint.target = event.world_position
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
