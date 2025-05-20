import pyb2d as b2d
from ipycanvas import Canvas
import time
import asyncio

# ipython display
from IPython.display import display, clear_output

from ipyevents import Event

# output from ipywidgets
from ipywidgets import Output

from .timing import WaitIfNeeded


class Transform(object):
    def __init__(self, canvas_shape, ppm, offset):
        self.canvas_shape = canvas_shape
        self.ppm = ppm
        self.offset = offset

    def point_world_to_canvas(self, p):
        x = (p[0] + self.offset[0]) * self.ppm
        y = self.canvas_shape[1] - ((p[1] + self.offset[1]) * self.ppm)
        return (x, y)

    def point_canvas_to_world(self, p):
        x = (p[0] / self.ppm) - self.offset[0]
        y = -((p[1] - self.canvas_shape[1]) / self.ppm) - self.offset[1]
        return (x, y)

    def points_world_to_canvas(self, points, output=None):
        if output is None:
            output = np.zeros((len(points), 2), dtype=np.float32)
        output[:] = numpy.require(points, dtype=np.float32)

        outout[:, 0] = (output[:, 0] + self.offset[0]) * self.ppm
        output[:, 1] = self.canvas_shape[1] - (
            (output[:, 1] + self.offset[1]) * self.ppm
        )
        return output

    def points_canvas_to_world(self, points):
        # convert a list of points to world coordinates
        return [self.point_canvas_to_world(p) for p in points]

    def scale_world_to_canvas(self, s):
        # convert a scale from world to canvas coordinates
        return s * self.ppm

    def scale_canvas_to_world(self, s):
        # convert a scale from canvas to world coordinates
        return s / self.ppm

    def scale_world_to_canvas(self, s):
        return s * self.ppm


class Sample(object):
    def __init__(self, world_def=None, settings=None):
        if world_def is None:
            world_def = b2d.world_def()

        print("gravity", world_def.gravity)
        self.world_id = b2d.create_world(world_def)
        self.world_def = world_def

        if settings is None:
            settings = {}
        self.settings = settings

        # rendering
        self.canvas_shape = self.settings.get("canvas_shape", [1000, 500])
        self.canvas = Canvas(width=self.canvas_shape[0], height=self.canvas_shape[1])
        ppm = self.settings.get("ppm", 60)
        offset = self.settings.get("offset", [0, 0])
        self.fps = self.settings.get("fps", 60)

        self.transform = Transform(self.canvas_shape, ppm, offset)

        # ipython output
        self.output = Output()

        # events
        d = Event(
            source=self.canvas,
            watched_events=[
                "mouseenter",
                "mousedown",
                "mouseup",
                "mousemove",
                "wheel",
                "mouseleave",
            ],
        )
        d.on_dom_event(self.handle_event)
        self.trigger_move_events_only_on_mouse_down = True

        # mouse joint
        self.mouse_joint = None
        self.connected_body_id = None
        self.mouse_down = False
        self.mouse_inside = False

        # ground body for mouse joint
        self.ground_body_id = b2d.create_body(
            self.world_id, b2d.body_def(type=b2d.BodyType.STATIC)
        )

    def print(self, *args):
        # print to the output widget
        with self.output:
            clear_output(wait=False)
            print(*args)
            # self.output.append_stdout(*args)
            # self.output.append_stdout("\n")

    def handle_event(self, event):
        # handle the event
        # print("event", event.keys())
        if event["type"] == "mousemove":
            if self.trigger_move_events_only_on_mouse_down and not self.mouse_down:
                return
            self.on_mouse_move(event)
        elif event["type"] == "mouseenter":
            self.mouse_inside = True
            self.on_mouse_enter(event)
        elif event["type"] == "mouseleave":
            self.mouse_inside = False
            self.on_mouse_leave(event)
        elif event["type"] == "mousedown":
            self.mouse_down = True
            self.on_mouse_down(event)
        elif event["type"] == "mouseup":
            self.mouse_down = False
            self.on_mouse_up(event)
        elif event["type"] == "wheel":
            self.on_mouse_wheel(event)

    def on_mouse_enter(self, event):
        pass

    def on_mouse_leave(self, event):
        self._destroy_mouse_joint()

    def on_mouse_down(self, event):
        canvas_point = (event["offsetX"], event["offsetY"])
        world_point = self.transform.point_canvas_to_world(canvas_point)

        # aabb around the mouse point
        aabb = b2d.aabb_arround_point(point=world_point, radius=0.1)

        # query filter
        query_filter = b2d.QueryFilter()

        result = [False, None]  # [found, shape_id]

        def callback(shape_id):
            # check if the world point is inside the shape
            inside = b2d.shape_test_point(shape_id, world_point)
            if inside:
                result[0] = True
                result[1] = shape_id
            # true continues the search
            return not inside

        # world overlapp aabb
        b2d.world_overlap_aabb(self.world_id, aabb, query_filter, callback)

        if result[0]:
            self.print("on_mouse_down found shape", result[1])
            shape_id = result[1]
            # get the body id
            body_id = b2d.shape_get_body(shape_id)
            self.connected_body_id = body_id

            # create the mouse joint between the ground body and the body
            # create the mouse joint
            mouse_joint_def = b2d.mouse_joint_def()
            mouse_joint_def.body_id_a = self.ground_body_id
            mouse_joint_def.body_id_b = body_id
            mouse_joint_def.target = world_point
            mouse_joint_def.hertz = 100.0
            mouse_joint_def.max_force = 10000.0 * b2d.body_get_mass(body_id)
            # mouse_joint_def.damping_ratio = 0.5

            # create the mouse joint
            self.mouse_joint = b2d.create_mouse_joint(self.world_id, mouse_joint_def)

    def _destroy_mouse_joint(self):
        if self.mouse_joint is not None:
            b2d.destroy_joint(self.mouse_joint)
            self.mouse_joint = None

    def on_mouse_up(self, event):
        self._destroy_mouse_joint()

    def on_mouse_move(self, event):
        if self.mouse_joint is not None:
            # wake up the body
            b2d.body_set_awake(self.connected_body_id, True)
            canvas_point = (event["relativeX"], event["relativeY"])
            world_point = self.transform.point_canvas_to_world(canvas_point)
            # set the target of the mouse joint
            b2d.mouse_joint_set_target(self.mouse_joint, world_point)

    def on_mouse_wheel(self, event):
        # print("on_mouse_wheel", event)
        # self.output.append_stdout("event wheel: " + str(event['deltaX']) + ", " + str(event['deltaY']) + "\n")
        # self.output.append_stdout("event mousemove: " + str(event['offsetX']) + ", " + str(event['offsetY']) + "\n")
        pass

    def show(self):

        display(self.canvas)
        display(self.output)

        self.canvas.clear()
        self.canvas.fill_style = "white"
        self.canvas.fill_rect(0, 0, *self.canvas_shape)

    def scale_world_to_canvas(self, s):
        return s * self.ppm

    def render(self, dt):
        pass

    def update(self, dt):
        pass

    def step(self, dt):
        # step the world with dt
        # print("step", dt)
        b2d.world_step(self.world_id, dt, 5)

    async def run(self):
        try:
            target_dt = 1 / self.fps

            # t0 = time.time()
            for i in range(50000):

                # t1 = time.time()
                # dt = t1 - t0
                # t0 = t1
                async with WaitIfNeeded(target_dt):

                    self.update(target_dt)
                    self.render(target_dt)
                    self.step(target_dt)

                # sleep if needed
                # time.sleep(target_dt)
                # await asyncio.sleep(target_dt)
                # clear the output
        except Exception as e:
            print("Exception in run", e)

    def start_run_task(self):
        # start the run task
        self.run_task = asyncio.create_task(self.run())
        return self.run_task
