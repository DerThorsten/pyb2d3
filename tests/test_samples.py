import pytest

# examples/ is put on sys.path by tests/__init__.py
import pyb2d3_samples  # (registers the samples)
from pyb2d3_sandbox import SampleBase, SampleRegistry, register_sample, registry, run_sample_browser, widgets

from .headless_test_frontend import HeadlessTestFrontend, run_in_headless_test_frontend

SAMPLES = registry.samples()


def test_samples_are_registered():
    assert len(SAMPLES) >= len(pyb2d3_samples.all_examples)
    for cls in pyb2d3_samples.all_examples:
        entry = registry.find(cls)
        assert entry is not None, cls
        assert (cls.sample_category, cls.sample_name) == (entry.category, entry.name)
    assert {"Games", "Demos", "Queries"} <= set(registry.categories())


# every registered sample, grouped by category in the test ids ("Games/Billiard", ...)
@pytest.mark.parametrize("entry", SAMPLES, ids=[entry.key for entry in SAMPLES])
def test_sample(entry):
    run_in_headless_test_frontend(sample_class=entry.cls, sample_settings=entry.cls.Settings())


class WidgetFrontend(HeadlessTestFrontend):
    """Collects the sample's widgets and drives each one through its values while stepping."""

    def add_widget(self, element):
        self.widgets.append(element)

    def pre_new_sample(self, sample_class, sample_settings):
        self.widgets = []

    @staticmethod
    def widget_values(element):
        if isinstance(element, (widgets.RadioButtons, widgets.Dropdown)):
            return list(element.options) + [element.value]
        if isinstance(element, widgets.Checkbox):
            return [not element.value, element.value]
        if isinstance(element, (widgets.FloatSlider, widgets.IntSlider)):
            return [element.min_value, element.max_value, element.value]
        if isinstance(element, widgets.Button):
            return [None]
        raise TypeError(f"unknown widget {element!r}")

    def main_loop(self):
        self.ui_is_ready()
        for _ in range(10):
            self.update_physics_single_step()
        for element in list(self.widgets):
            for value in self.widget_values(element):
                if isinstance(element, widgets.Button):
                    element.callback()
                else:
                    element.value = value
                    element.callback(value)
                for _ in range(5):
                    self.update_physics_single_step()
                    self.draw_physics()
        self.sample.post_run()


@pytest.mark.parametrize("entry", SAMPLES, ids=[e.key for e in SAMPLES])
def test_sample_widgets(entry):
    entry.cls.run(
        sample_settings=entry.cls.Settings(),
        frontend_class=WidgetFrontend,
        frontend_settings=WidgetFrontend.Settings(),
    )


def test_registry():
    reg = SampleRegistry()

    @register_sample("A", "First", registry=reg)
    class First(SampleBase):
        pass

    @register_sample("B", registry=reg)
    class Second(SampleBase):
        pass

    assert reg.categories() == ["A", "B"]
    assert [e.key for e in reg] == ["A/First", "B/Second"]
    assert reg.get("B/Second").cls is Second
    assert reg.find(Second).name == "Second"
    assert reg.neighbor(First).cls is Second
    assert reg.neighbor(Second).cls is First  # wraps around
    assert reg.neighbor(First, -1).cls is Second
    with pytest.raises(KeyError):
        reg.get("A/Missing")
    with pytest.raises(ValueError):
        reg.register(type("Other", (SampleBase,), {}), "A", "First")


class BrowsingFrontend(HeadlessTestFrontend):
    """Switches to the next registered sample every few steps."""

    def main_loop(self):
        self.ui_is_ready()
        self.visited = [self.sample_class]
        for i in range(3 * 20):
            self.update_frontend_logic()
            self.update_physics_single_step()
            self.draw_physics()
            if i % 20 == 19:
                self.next_sample()
                self.update_frontend_logic()
                self.visited.append(self.sample_class)
        self.sample.post_run()


def test_switch_samples_in_frontend():
    frontend = run_sample_browser(
        start="Demos/Joints",
        frontend_class=BrowsingFrontend,
        frontend_settings=BrowsingFrontend.Settings(),
    )
    keys = [registry.find(cls).key for cls in frontend.visited]
    entries = [e.key for e in registry]
    start = entries.index("Demos/Joints")
    assert keys == [entries[(start + i) % len(entries)] for i in range(len(keys))]
    assert frontend.sample_title == " / ".join(keys[-1].split("/"))
