# this code is based on   https://github.com/giorgosg/box2d-py/blob/main/src/box2d_testbed/testbed.py
# The code has been adapted to work with the pyb2d3 library and its frontend system.
# The original code is licensed under the MIT License with the following copyright:
#
# MIT License
# Copyright 2025 Giorgos Giagas
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”),
# to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from pyb2d3_sandbox.frontend_base import (
    FrontendBase,
    MouseDownEvent,
    MouseUpEvent,
    MouseMoveEvent,
    MouseWheelEvent,
)

from dataclasses import dataclass

from imgui_bundle import hello_imgui, imgui
from OpenGL import GL as gl

from pyb2d3 import Vec2


from .debug_draw_gl import GLDebugDraw, Camera

# weakref
import weakref


class OpenglFrontend(FrontendBase):
    @dataclass
    class Settings(FrontendBase.Settings):
        pass

    def __init__(self, settings):
        super().__init__(settings)

        self.camera = Camera()
        self.debug_draw = None
        # self._self_ref = weakref.ref(self)
        self.runner_params = hello_imgui.RunnerParams()

        self.init_app()
        self._last_mouse_pos = None
        self._last_world_mouse_pos = None

        self._center_when_ready = False

    @property
    def weak_self(self):
        """Returns a weak reference to the current instance."""
        return self._self_ref()

    def __del__(self):
        print("OpenglFrontend.__del__()")
        # self.sample.destroy()

    def init_app(self):
        weak = weakref.proxy(self)

        runner_params = self.runner_params

        # Set window type back to docking with default window
        runner_params.imgui_window_params.default_imgui_window_type = (
            hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space
        )
        runner_params.app_window_params.window_geometry.size = (
            self.settings.canvas_shape
        )
        # Initialize simulation and debug draw in post_init
        runner_params.callbacks.post_init = lambda: weak.post_gl_init()

        # Menu setup
        runner_params.imgui_window_params.show_menu_bar = True
        runner_params.callbacks.show_menus = lambda: weak.show_menus()
        runner_params.imgui_window_params.show_menu_app = False

        # Status bar
        runner_params.imgui_window_params.show_status_bar = True
        runner_params.imgui_window_params.show_status_fps = False
        runner_params.fps_idling.enable_idling = False

        runner_params.callbacks.show_status = lambda: weak.show_status()

        # Docking layout
        runner_params.docking_params = self.create_layout()
        runner_params.docking_params.main_dock_space_node_flags = (
            imgui.DockNodeFlags_.none
        )

        # runner_params.callbacks.pre_new_frame = lambda: weak.on_pre_new_frame()

        # # on exit
        # runner_params.callbacks.on_exit = lambda: self.sample.destroy()

    def show_status(self):
        imgui.push_style_var(imgui.StyleVar_.item_spacing, (10, 1))
        # for key, value, display in state.show_dd.get_current():
        #     _, newvalue = imgui.checkbox(display, value)
        #     setattr(state.show_dd, key, newvalue)
        #     imgui.same_line()
        imgui.pop_style_var()

    def show_menus(self):
        pass
        # if imgui.begin_menu("Draw"):
        #     # for key, value, display in state.show_dd.get_current():
        #     #     _, newvalue = imgui.menu_item(display, "", value)
        #     #     setattr(state.show_dd, key, newvalue)
        #     imgui.end_menu()

    def render_simulation(self):
        """Draw the simulation in the window"""
        # Get window dimensions and position in screen coordinates
        pos = imgui.get_window_pos()
        size = imgui.get_window_size()
        io = imgui.get_io()
        # # Ensure we have valid dimensions
        if size.x <= 0 or size.y <= 0:
            return

        if self._center_when_ready:
            # Center the sample when the debug draw is ready
            self.debug_draw.camera.set_view(
                self.debug_draw.camera.center,
                self.debug_draw.camera.zoom,
                size.x,
                size.y,
            )
            self.center_sample(margin_px=self._margin_px)
            self._center_when_ready = False
            self._margin_px = None

        # print("OpenglFrontend.render_simulation(): pos:", pos, "size:", size)

        # Convert ImGui coordinates to GL coordinates (flip Y)
        gl_y = io.display_size.y - (pos.y + size.y)
        # Set viewport to window region
        gl.glViewport(int(pos.x), int(gl_y), int(size.x), int(size.y))

        if imgui.is_window_hovered():
            # print("OpenglFrontend.render_simulation(): window hovered")

            mouse_pos = Vec2(io.mouse_pos.x, io.mouse_pos.y) - Vec2(pos.x, pos.y)
            world_pos = self.debug_draw.camera.convert_screen_to_world(mouse_pos)

            # Only handle scroll when mouse is over simulation window
            mouse_scroll = io.mouse_wheel
            if mouse_scroll != 0.0:
                self.sample.on_mouse_wheel(
                    MouseWheelEvent(delta=-mouse_scroll, world_position=world_pos)
                )

            # print(" OpenglFrontend.render_simulation(): mouse_pos:", mouse_pos, "world_pos:", world_pos)
            # Check left mouse button events.
            if io.mouse_clicked[0]:
                event = MouseDownEvent(world_position=world_pos)
                self.sample.on_mouse_down(event)
                self._multi_click_handler.handle_click(world_position=world_pos)
            elif io.mouse_down[0]:
                delta = Vec2(io.mouse_delta.x, io.mouse_delta.y)

                if delta[0] != 0 or delta[1] != 0:
                    event = MouseMoveEvent(
                        world_position=world_pos,
                        world_delta=self.debug_draw.camera.screen_delta_to_world_delta(
                            delta
                        ),
                    )
                    self.sample.on_mouse_move(event)
            elif io.mouse_released[0]:
                event = MouseUpEvent(world_position=world_pos)
                self.sample.on_mouse_up(event)
        center = self.debug_draw.camera.center
        scale = self.debug_draw.camera.zoom
        # print("OpenglFrontend.render_simulation(): center:", center, "scale:", scale, "size:", size)
        self.debug_draw.camera.set_view(center, scale, size.x, size.y)
        self.update_and_draw(1 / 60)

        # Reset viewport
        gl.glViewport(0, 0, int(io.display_size.x), int(io.display_size.y))

    def create_simulation_window(self):
        weak = weakref.proxy(self)
        window = hello_imgui.DockableWindow()
        window.label = "Simulation"
        window.dock_space_name = "MainDockSpace"
        window.gui_function = lambda: weak.render_simulation()
        window.imgui_window_flags = imgui.WindowFlags_.no_background
        return window

    def create_right_panel_split(self):
        split = hello_imgui.DockingSplit()
        split.initial_dock = "MainDockSpace"
        split.new_dock = "RightPanel"
        split.direction = imgui.Dir_.right
        split.ratio = 0.2
        return split

    def create_right_panel_split1(self):
        split_right1 = hello_imgui.DockingSplit()
        split_right1.initial_dock = "RightPanel"
        split_right1.new_dock = "RightPanel1"
        split_right1.direction = imgui.Dir_.down
        split_right1.ratio = 0.73
        return split_right1

    def create_right_panel_split2(self):
        split_right2 = hello_imgui.DockingSplit()
        split_right2.initial_dock = "RightPanel1"
        split_right2.new_dock = "RightPanel2"
        split_right2.direction = imgui.Dir_.down
        split_right2.ratio = 0.5
        return split_right2

    def create_right_panel_split3(self):
        split_right3 = hello_imgui.DockingSplit()
        split_right3.initial_dock = "RightPanel2"
        split_right3.new_dock = "RightPanel3"
        split_right3.direction = imgui.Dir_.down
        split_right3.ratio = 0.4
        return split_right3

    def create_test_list_window(self):
        window = hello_imgui.DockableWindow()
        window.label = "Tests"
        window.dock_space_name = "RightPanel1"
        # window.gui_function = self.show_test_list
        return window

    def create_stats_window(self):
        window = hello_imgui.DockableWindow()
        window.label = "Performance"
        window.dock_space_name = "RightPanel3"
        # window.gui_function = weakref.proxy(self).show_stats
        return window

    def show_stats(self):
        imgui.text("current (avg) [max] ms")

    def create_controls_window(self):
        window = hello_imgui.DockableWindow()
        window.label = "Controls"
        window.dock_space_name = "RightPanel"
        # window.gui_function = self.show_controls
        return window

    def create_test_ui_window(self):
        window = hello_imgui.DockableWindow()
        window.label = "Test UI"
        window.dock_space_name = "RightPanel2"
        # window.gui_function = self.show_test_ui
        return window

    def create_layout(self):
        docking_params = hello_imgui.DockingParams()
        docking_params.docking_splits = [
            self.create_right_panel_split(),
            self.create_right_panel_split1(),
            self.create_right_panel_split2(),
            self.create_right_panel_split3(),
        ]
        docking_params.dockable_windows = [
            self.create_simulation_window(),  # Add back the simulation window
            self.create_test_list_window(),
            self.create_stats_window(),
            self.create_controls_window(),
            self.create_test_ui_window(),
        ]
        return docking_params

    def on_pre_new_frame(self):
        if self._center_when_ready:
            # Center the sample when the debug draw is ready
            self.center_sample(margin_px=self._margin_px)
            self._center_when_ready = False
            self._margin_px = None

        # we can use it to update the sample
        # todo, meassure time
        # print("OpenglFrontend.on_pre_new_frame(): updating sample")
        # self.update_and_draw(1/60)
        # self.sample.world.step(1/60, 10)

    def before_exit(self):
        print("OpenglFrontend.before_exit()")
        self.sample.world.destroy()
        # self.sample.world = None

    def post_gl_init(self):
        print("Post GL initialization")
        self.debug_draw = GLDebugDraw(self.camera)
        # self.debug_draw.camera.zoom = 100
        self.debug_draw.draw_shapes = True  # self.settings.debug_draw.draw_shapes
        self.debug_draw.draw_joints = True  # self.settings.debug_draw.draw_joints

    def center_sample(self, margin_px):
        if self.debug_draw is None:
            self._center_when_ready = True
            self._margin_px = margin_px
            return

        aabb = self.sample.aabb()

        # Step 1: Compute center of AABB
        center = aabb.center()

        # Step 2: Compute AABB size (extents)
        aabb_size = aabb.upper_bound - aabb.lower_bound
        half_width = 0.5 * aabb_size.x
        half_height = 0.5 * aabb_size.y

        # Step 3: Compute aspect ratio of screen
        w = float(self.camera.width)
        h = float(self.camera.height)
        aspect_ratio = w / h

        # Step 4: Determine required zoom
        # Our camera's visible area is: (zoom * aspect_ratio, zoom)
        # So to fit the AABB, we choose the *larger* zoom required in either axis
        zoom_x = half_width / aspect_ratio
        zoom_y = half_height

        # Final zoom is the max needed to fit both dimensions
        zoom = max(zoom_x, zoom_y)

        # Step 5: Apply
        self.camera.center = center
        self.camera.zoom = zoom

    def drag_camera(self, delta):
        screen_delta = (delta[0], delta[1])
        self.camera.center -= screen_delta

    def change_zoom(self, delta):
        self.camera.zoom += delta
        if self.camera.zoom < 1:
            self.camera.zoom = 1

    def main_loop(self):
        hello_imgui.run(self.runner_params)
