import pyb2d3 as b2d
from .frontend import run

from dataclasses import dataclass


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
        run(
            sample_class=cls,
            sample_settings=sample_settings,
            frontend_class=frontend_class,
            frontend_settings=frontend_settings,
        )

    def __init__(self, settings=SampleBaseSettings(), world=None):

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
        self._mouse_joint_body = None
        self._camera_drag = False

        self.is_mouse_down = False
        self.mouse_pos = None

        self.frontend = None

        # world time (ie time in the simulation)
        self.world_time = 0.0
        self.world_iteration = 0

        self.mouse_joint_hertz = 100.0
        self.mouse_joint_force_multiplier = 500.0
        self.mouse_joint_damping_ratio = 1.0

    # some properties for the frontend
    @property
    def debug_draw(self):
        if self.frontend is not None:
            return self.frontend.debug_draw
        else:
            raise ValueError(
                "Frontend cannot be accesed in __init__ of the sample implementation"
            )

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

    def on_click(self, pos):
        pass

    # on_double_click and  on_triple_click can be implemented in derived classes
    # but if these methods are not present, we dont need to delay
    # the "on_click" event to wait for a possible double/triple click.
    # To be able to perform the check if the user has implemented these methods,
    # we wont implement them here.

    # def on_double_click(self, pos):
    #     pass

    # def on_triple_click(self, pos):
    #     pass

    def on_mouse_down(self, pos):
        self.is_mouse_down = True
        self.mouse_pos = pos
        body = self.world.dynamic_body_at_point(pos)
        if body:
            # wake body up
            body.awake = True
            self._mouse_joint_body = body
            self._mouse_joint = self.world.create_mouse_joint(
                body_a=self.anchor_body,
                body_b=self._mouse_joint_body,
                target=pos,
                hertz=self.mouse_joint_hertz,
                max_force=self._mouse_joint_body.mass
                * self.mouse_joint_force_multiplier,
                damping_ratio=self.mouse_joint_damping_ratio,
            )
        else:
            self._camera_drag = True

    def _destroy_mouse_joint(self):
        if self._mouse_joint is not None:
            self._mouse_joint.destroy()
            self._mouse_joint = None
            self.connected_body = None

    def on_mouse_up(self, pos):
        # Handle mouse up events
        self.mouse_pos = pos
        self._camera_drag = False
        self.is_mouse_down = False
        self._destroy_mouse_joint()

    def on_mouse_move(self, pos, delta):
        if self._mouse_joint is not None:
            assert (
                self.is_mouse_down
            ), "Mouse joint should only be updated when mouse is down"
            self._mouse_joint.target = pos
        elif self._camera_drag:
            # If dragging the camera, update the camera position
            # delta = (pos[0] - self.mouse_pos[0], pos[1] - self.mouse_pos[1])
            self.frontend.drag_camera(delta)

        self.mouse_pos = pos

    def on_mouse_leave(self):
        # Handle mouse leave events
        self.mouse_pos = None
        self.is_mouse_down = False
        self._camera_drag = False
        self._destroy_mouse_joint()

    def on_mouse_enter(self):
        # Handle mouse enter events
        pass

    def on_mouse_wheel(self, delta):
        # Handle mouse wheel events
        self.frontend.change_zoom(delta)
