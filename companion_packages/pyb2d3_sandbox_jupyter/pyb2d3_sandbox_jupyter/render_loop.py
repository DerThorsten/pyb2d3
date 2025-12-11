import asyncio
import time


def wait_for_change(widget, value):
    future = asyncio.Future()

    def getvalue(change):
        # make the new value available
        try:
            future.set_result(change.new)
        except asyncio.InvalidStateError:
            pass
        widget.unobserve(getvalue, value)

    widget.unobserve_it = lambda: widget.unobserve(getvalue, value)

    widget.observe(getvalue, value)
    return future


class Loop(object):
    def __init__(self):
        self.callback = None
        self.running = True
        self.canvas = None

        self.next_canvas = None
        self.next_callback = None

    async def run(self):
        try:
            # i = 0
            while self.running:
                # if i % 60 == 0:
                #     print("Render loop running...")
                #  i += 1
                t0 = time.perf_counter()
                if self.callback is not None:
                    await self.callback(self.canvas)

                elapsed = time.perf_counter() - t0

                sleep_time = max(0, 1 / 60 - elapsed)

                if not self.callback:
                    sleep_time = 0.1  # sleep a bit longer if no callback is set

                await asyncio.sleep(sleep_time)

                if self.next_canvas is not None and self.next_callback is not None:
                    print("!!!Changing render loop canvas and callback...")
                    self.canvas = self.next_canvas
                    self.callback = self.next_callback
                    self.next_canvas = None
                    self.next_callback = None
        except Exception as e:
            print(e)

    def change_callback_when_possible(self, canvas, func):
        self.next_canvas = canvas
        self.next_callback = func


# global instanced of loop
_global_loop = None


def render_loop(canvas, func):
    global _global_loop
    if _global_loop is None:
        _global_loop = Loop()

        asyncio.create_task(_global_loop.run())

    async def callback(canvas):
        func()
        await wait_for_change(canvas, "_frame")

    _global_loop.change_callback_when_possible(canvas, callback)

    def cancel():
        pass

    return cancel
