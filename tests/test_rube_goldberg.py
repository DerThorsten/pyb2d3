"""The Rube Goldberg sample runs through all its stages (a regression test for the
tuning: a changed density / position anywhere breaks the chain)."""

from pyb2d3_samples.rube_goldberg import RubeGoldberg

from .headless_test_frontend import HeadlessTestFrontend


class QuietFrontend(HeadlessTestFrontend):
    """steps the sample without random mouse events until the chain is done"""

    seconds = 40.0

    def main_loop(self):
        self.ui_is_ready()
        for _ in range(int(self.seconds * self.settings.hertz)):
            self.update_frontend_logic()
            self.update_physics_single_step()
            if self.sample.stages_done == len(self.sample.stages):
                break
        self.result = [(stage.name, stage.time) for stage in self.sample.stages]
        self.sample.post_run()


def test_rube_goldberg_chain_completes():
    frontend = RubeGoldberg.run(frontend_class=QuietFrontend, frontend_settings=QuietFrontend.Settings())
    missing = [name for name, time in frontend.result if time is None]
    assert not missing, f"the chain stopped before: {missing} ({frontend.result})"
    times = [time for _, time in frontend.result]
    assert times == sorted(times), f"stages out of order: {frontend.result}"
