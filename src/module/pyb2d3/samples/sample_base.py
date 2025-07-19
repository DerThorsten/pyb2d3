import pyb2d3 as b2d
from .frontend import run


class SampleBase(object):

    # classmethod
    @classmethod
    def run(cls, frontend_class=None, settings=None):
        """
        Run the sample with the specified frontend class and settings.
        If no frontend class is provided, it defaults to the DefaultFrontend.
        """
        if frontend_class is None:
            from .frontend import DefaultFrontend

            frontend_class = DefaultFrontend

        run(sample_class=cls, frontend_class=frontend_class, settings=settings)

    def __init__(self, world=None, gravity=(0, -10)):
        self.world = world

        if b2d.WITH_THREADING:
            pool = b2d.ThreadPool()
        else:
            pool = None
        if self.world is None:
            self.world = b2d.World(gravity=gravity, thread_pool=pool)

        # create an anchor body for joints
        self.anchor_body = self.world.create_static_body(position=(0, 0))

        self._mouse_joint = None
        self._mouse_joint_body = None
        self._camera_drag = False

        self.is_mouse_down = False
        self.mouse_pos = None

        self.frontend = None

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

    def on_double_click(self, pos):
        pass

    def on_triple_click(self, pos):
        pass

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
                hertz=100.0,
                max_force=500.0 * self._mouse_joint_body.mass,
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
