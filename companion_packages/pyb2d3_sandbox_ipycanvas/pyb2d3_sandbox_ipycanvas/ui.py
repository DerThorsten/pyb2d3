import ipywidgets
from ipywidgets import Layout, ToggleButton, Button, VBox

from pyb2d3_sandbox import widgets


class TestbedUI:
    def __init__(self, frontend):
        self.frontend = frontend
        self._canvas = frontend.canvas
        self._output_widget = frontend.output_widget

        self._header = self._make_header()
        self._right_sidebar = self._make_right_sidebar()
        self._left_sidebar = self._make_left_sidebar()
        self._footer = self._make_footer()

        self.app_layout = ipywidgets.AppLayout(
            header=self._header,
            center=self._canvas,
            right_sidebar=self._right_sidebar,
            left_sidebar=self._left_sidebar,
            footer=self._footer,
            pane_heights=["60px", 5, "60px"],
            pane_widths=[0, f"{self._canvas.width}px", 1],
        )

    def is_playing(self):
        return self.play_pause_btn.value

    def is_paused(self):
        return not self.play_pause_btn.value

    def _make_header(self):
        layout = Layout(height="60px")
        return ipywidgets.Label("Testbed", layout=layout)

    def _make_debug_draw_accordion(self):
        option_names = [
            ("draw_shapes", "Draw Shapes"),
            ("draw_joints", "Draw Joints"),
            ("draw_joint_extras", "Draw Joint Extras"),
            ("draw_bounds", "Draw Bounds"),
            # ("draw_mass", "Draw Mass"),
            # ("draw_body_names", "Draw Body Names"),
            ("draw_contacts", "Draw Contacts"),
            # ("draw_graph_colors", "Draw Graph Colors"),
            # ("draw_contact_normals", "Draw Contact Normals"),
            # ("draw_contact_impulses", "Draw Contact Impulses"),
            # ("draw_contact_features", "Draw Contact Features"),
            # ("draw_friction_impulses", "Draw Friction Impulses"),
        ]

        def get_val(option_name):
            try:
                return getattr(self.frontend.debug_draw, option_name, False)
            except AttributeError:
                return False

        # make a list of checkboxes for each option
        checkboxes = [
            ipywidgets.Checkbox(
                value=get_val(option_name),
                description=desc,
                layout=Layout(align_self="flex-start"),
                style={"description_width": "initial"},
            )
            for option_name, desc in option_names
        ]

        # connect the checkboxes to the debug draw options
        for checkbox, (option_name, desc) in zip(checkboxes, option_names):

            def on_change(change, option_name=option_name):
                if change["type"] == "change" and change["name"] == "value":
                    setattr(self.frontend.debug_draw, option_name, change["new"])

            checkbox.observe(on_change, names="value")

        vbox = VBox(
            checkboxes,
            layout=Layout(
                align_items="flex-start",
                width="100%",
            ),
        )

        # create an accordion with the checkboxes
        accordion = ipywidgets.Accordion(
            children=[vbox],
            layout=Layout(height="auto", justify_content="flex-start", width="auto"),
        )
        accordion.set_title(0, "Drawing Settings:")
        return accordion

    def _make_sample_settings_accordion(self):
        self.sample_settings_vbox = VBox(
            children=[],
            layout=Layout(
                align_items="flex-start",
                width="100%",
            ),
        )

        # create an accordion with the checkboxes
        accordion = ipywidgets.Accordion(
            children=[self.sample_settings_vbox],
            layout=Layout(height="auto", justify_content="flex-start", width="auto"),
        )
        accordion.set_title(0, "Sample Settings:")
        return accordion

    def _make_simulation_settings_accordion(self):
        # fps int slider
        fps_slider = ipywidgets.IntSlider(
            value=self.frontend.settings.fps,
            min=0,
            max=120,
            step=1,
            description="FPS",
            tooltip="Frames per second",
            continuous_update=False,
            layout=Layout(align_self="flex-start"),
            style={"description_width": "initial"},
        )

        def on_fps_change(change):
            if change["type"] == "change" and change["name"] == "value":
                self.frontend.settings.fps = change["new"]

        fps_slider.observe(on_fps_change, names="value")

        # n-substeps int slider
        n_substeps_slider = ipywidgets.IntSlider(
            value=self.frontend.settings.substeps,
            min=1,
            max=20,
            step=1,
            description="Substeps",
            continuous_update=False,
            layout=Layout(align_self="flex-start"),
            style={"description_width": "initial"},
        )

        def on_n_substeps_change(change):
            if change["type"] == "change" and change["name"] == "value":
                self.frontend.settings.substeps = change["new"]

        n_substeps_slider.observe(on_n_substeps_change, names="value")

        # add a checkbox for fixed-delta time
        fixed_delta_checkbox = ipywidgets.Checkbox(
            value=self.frontend.settings.fixed_delta_t,
            description="fixed-Δt",
            tooltip="If checked, the physics simulation will use a fixed delta time to update the physical world",
            layout=Layout(align_self="flex-start"),
            style={"description_width": "initial"},
        )

        def on_fixed_delta_change(change):
            if change["type"] == "change" and change["name"] == "value":
                self.frontend.settings.fixed_delta_t = change["new"]

        fixed_delta_checkbox.observe(on_fixed_delta_change, names="value")

        # this section is only valid if fixed_delta_t is True

        vbox = VBox(
            children=[
                fps_slider,
                n_substeps_slider,
                fixed_delta_checkbox,
            ],
            layout=Layout(
                align_items="flex-start",
                width="100%",
            ),
        )

        # create an accordion with the checkboxes
        accordion = ipywidgets.Accordion(
            children=[vbox],
            layout=Layout(height="auto", justify_content="flex-start", width="auto"),
        )
        accordion.set_title(0, "Simulation Settings:")
        return accordion

    def _make_right_sidebar(self):
        # we place multiple accordions in the right sidebar
        # - one for simulation settings
        # - one for debug draw settings
        # - one for sample specific settings

        self._simulation_settings_accordion = self._make_simulation_settings_accordion()
        self._debug_draw_accordion = self._make_debug_draw_accordion()
        self._sample_settings_accordion = self._make_sample_settings_accordion()

        return ipywidgets.VBox(
            [
                self._simulation_settings_accordion,
                self._debug_draw_accordion,
                self._sample_settings_accordion,
            ],
            layout=Layout(display="flex", justify_content="flex-start", width="400px"),
        )

    def _make_left_sidebar(self):
        return None

    def _make_footer(self):
        return ipywidgets.HBox(
            [
                self._footer_left(),
                ipywidgets.Label(""),
                self._footer_right(),
            ],
            layout=Layout(height="60px", display="flex", justify_content="flex-start"),
        )

    def _footer_left(self):
        return self._make_control_button_group()

    def _footer_right(self):
        return ipywidgets.Label("")

    def _make_control_button_group(self):
        self.play_pause_btn = ToggleButton(
            value=True, tooltip="Play/Pause", icon="pause", layout=Layout(width="40px")
        )
        self.stop_btn = Button(
            tooltip="Stop", icon="stop", layout=Layout(width="40px"), button_style="danger"
        )

        self.single_step_btn = Button(
            tooltip="Step", icon="step-forward", layout=Layout(width="40px")
        )
        self.single_step_btn.disabled = True

        self.play_pause_btn.observe(self._on_play_pause_change, names="value")
        self.stop_btn.on_click(self._on_stop_clicked)
        self.single_step_btn.on_click(self.on_single_step)

        # grup the buttons in a horizontal box
        return ipywidgets.HBox(
            [
                self.play_pause_btn,
                self.stop_btn,
                self.single_step_btn,
            ],
            layout=Layout(justify_content="center"),
        )

    def remove_sample_ui_elements(self):
        # remove all children from the sample settings vbox
        self.sample_settings_vbox.children = []

    def add_sample_ui_element(self, element):
        if isinstance(element, widgets.FloatSlider):
            slider = ipywidgets.FloatSlider(
                value=element.value,
                min=element.min_value,
                max=element.max_value,
                step=element.step,
                description=element.label,
                continuous_update=False,
                layout=Layout(width="100%"),
            )
            slider.observe(
                lambda change, callback=element.callback: callback(change["new"]), names="value"
            )
            self.sample_settings_vbox.children += (slider,)
        elif isinstance(element, widgets.IntSlider):
            slider = ipywidgets.IntSlider(
                value=element.value,
                min=element.min_value,
                max=element.max_value,
                step=element.step,
                description=element.label,
                continuous_update=False,
                layout=Layout(width="100%"),
            )
            slider.observe(
                lambda change, callback=element.callback: callback(change["new"]), names="value"
            )
            self.sample_settings_vbox.children += (slider,)

        elif isinstance(element, widgets.Checkbox):
            checkbox = ipywidgets.Checkbox(
                value=element.value, description=element.label, layout=Layout(width="100%")
            )
            checkbox.observe(
                lambda change, callback=element.callback: callback(change["new"]), names="value"
            )
            self.sample_settings_vbox.children += (checkbox,)
        elif isinstance(element, widgets.Button):
            button = Button(description=element.label, layout=Layout(width="100%"))
            button.on_click(element.callback)
            self.sample_settings_vbox.children += (button,)
        elif isinstance(element, widgets.Dropdown):
            dropdown = ipywidgets.Dropdown(
                options=element.options,
                value=element.value,
                description=element.label,
                layout=Layout(width="100%"),
            )
            dropdown.observe(
                lambda change, callback=element.callback: callback(change["new"]), names="value"
            )
            self.sample_settings_vbox.children += (dropdown,)
        elif isinstance(element, widgets.RadioButtons):
            radio_buttons = ipywidgets.RadioButtons(
                options=element.options,
                value=element.value,
                description=element.label,
                layout=Layout(width="100%"),
            )
            radio_buttons.observe(
                lambda change, callback=element.callback: callback(change["new"]), names="value"
            )
            self.sample_settings_vbox.children += (radio_buttons,)

    def _on_play_pause_change(self, change):
        if change["new"]:
            self.play_pause_btn.icon = "pause"
            self.single_step_btn.disabled = True
            self.on_play()
        else:
            self.play_pause_btn.icon = "play"
            self.on_pause()
            self.single_step_btn.disabled = False

    def _on_stop_clicked(self, _):
        was_playing_before = self.is_playing()
        self.play_pause_btn.value = False
        self.single_step_btn.disabled = False
        self.play_pause_btn.icon = "play"
        self.on_stop(was_playing_before)

    def on_play(self):
        self.frontend.on_play()

    def on_pause(self):
        self.frontend.on_pause()

    def on_stop(self, was_playing_before):
        self.frontend._clear_canvas()

        self.frontend.stop()

        if was_playing_before:
            self.play_pause_btn.value = True
            self.play_pause_btn.icon = "pause"
            self.single_step_btn.disabled = True
        else:
            self.play_pause_btn.value = False
            self.play_pause_btn.icon = "play"
            self.single_step_btn.disabled = False

            # we want to do a single step to display at least
            # the first frame, instead of displaying the last frame

            # self.frontend.on_single_step()

    def on_single_step(self, _):
        self.frontend._clear_canvas()
        self.frontend.single_step()

    def display(self):
        display(self.app_layout, self._output_widget)


if __name__ == "__main__":

    class MockFrontend:
        def __init__(self):
            self.canvas = ipycanvas.Canvas(
                width=800,
                height=600,
            )
            self.canvas.fill_style = "darkblue"
            self.canvas.fill_rect(0, 0, self.canvas.width, self.canvas.height)
            self.settings = type("Settings", (), {"headless": False})

        def on_pause(self):
            print("MockFrontend: Paused")

        def on_play(self):
            print("MockFrontend: Playing")

        def on_stop(self):
            print("MockFrontend: Stopped")

        def on_single_step(self):
            print("MockFrontend: Single step")

    import ipycanvas
    from IPython.display import display

    frontend = MockFrontend()
    ui = TestbedUI(frontend)
    ui.display()
