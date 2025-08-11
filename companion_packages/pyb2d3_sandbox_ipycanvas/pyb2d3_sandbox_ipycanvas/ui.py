import ipywidgets
from ipywidgets import Layout, ToggleButton, Button, VBox
from pyb2d3_sandbox import widgets

from IPython.display import display


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
        ctrl_buttons = self._make_control_button_group()

        # fps int slider
        hertz_slider = ipywidgets.IntSlider(
            value=self.frontend.settings.hertz,
            min=1,
            max=120,
            step=1,
            description="Hertz",
            tooltip="How often the simulation updates per second",
            continuous_update=True,
            layout=Layout(align_self="flex-start"),
            style={"description_width": "initial"},
        )

        def on_hertz_change(change):
            if change["type"] == "change" and change["name"] == "value":
                self.frontend.settings.hertz = change["new"]

        hertz_slider.observe(on_hertz_change, names="value")

        # n-substeps int slider
        n_substeps_slider = ipywidgets.IntSlider(
            value=self.frontend.settings.substeps,
            min=1,
            max=20,
            step=1,
            description="Substeps",
            continuous_update=True,
            layout=Layout(align_self="flex-start"),
            style={"description_width": "initial"},
        )

        def on_n_substeps_change(change):
            if change["type"] == "change" and change["name"] == "value":
                self.frontend.settings.substeps = change["new"]

        n_substeps_slider.observe(on_n_substeps_change, names="value")

        # speed slider from "-max_factor" to "+max_factor"
        max_factor = 4

        def mapping(val):
            if val > 0:
                return 1.0 + val
            elif val == 0:
                return 1.0
            else:
                return 1.0 / abs(val - 1)

        speed_slider = ipywidgets.FloatSlider(
            value=0.0,  # initial value is 0.0, which means no speed change
            min=-max_factor,
            max=max_factor,
            step=0.1,
            description="Speed",
            continuous_update=True,
            layout=Layout(align_self="flex-start"),
            style={"description_width": "initial"},
        )

        def on_speed_change(change):
            if change["type"] == "change" and change["name"] == "value":
                self.frontend.settings.speed = mapping(change["new"])

        speed_slider.observe(on_speed_change, names="value")

        # this section is only valid if fixed_delta_t is True

        vbox = VBox(
            children=[
                ctrl_buttons,
                hertz_slider,
                n_substeps_slider,
                speed_slider,
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

        # open this by default
        self._simulation_settings_accordion.selected_index = 0
        self._debug_draw_accordion.selected_index = 0

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
                # self._footer_left(),
                # ipywidgets.Label(""),
                # self._footer_right(),
            ],
            layout=Layout(height="60px", display="flex", justify_content="flex-start"),
        )

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
        # ensure the accordion is visible
        if not self._sample_settings_accordion.selected_index == 0:
            self._sample_settings_accordion.selected_index = 0
        if isinstance(element, widgets.FloatSlider):
            slider = ipywidgets.FloatSlider(
                value=element.value,
                min=element.min_value,
                max=element.max_value,
                step=element.step,
                description=element.label,
                continuous_update=True,
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
                continuous_update=True,
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
        try:
            if change["new"]:
                self.play_pause_btn.icon = "pause"
                self.single_step_btn.disabled = True
                self.on_play()
            else:
                self.play_pause_btn.icon = "play"
                self.on_pause()
                self.single_step_btn.disabled = False
        except Exception as e:
            self.frontend._handle_exception(e)

    def _on_stop_clicked(self, _):
        try:
            was_playing_before = not self.frontend.is_paused()
            self.play_pause_btn.value = False
            self.single_step_btn.disabled = False
            self.play_pause_btn.icon = "play"
            self.on_stop(was_playing_before)
        except Exception as e:
            self.frontend._handle_exception(e)

    def on_play(self):
        try:
            self.frontend.set_running()
        except Exception as e:
            self.frontend._handle_exception(e)

    def on_pause(self):
        try:
            self.frontend.set_paused()
        except Exception as e:
            self.frontend._handle_exception(e)

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
        self.frontend.update_physics_single_step()

    def display(self):
        display(self.app_layout, self._output_widget)
