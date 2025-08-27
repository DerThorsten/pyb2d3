import asyncio
import time


def wait_for_change(widget, value):
    future = asyncio.Future()

    def getvalue(change):
        # make the new value available
        future.set_result(change.new)
        widget.unobserve(getvalue, value)

    widget.observe(getvalue, value)
    return future


async def _call_repeated(canvas, func):
    # we limit this to 60 hz by default, but this can be overridden
    target_dt = 1 / 60  # default to 60 fps

    try:
        while True:
            try:
                t0 = time.perf_counter()
                func()
                await wait_for_change(canvas, "_frame")
                elapsed = time.perf_counter() - t0
                sleep_time = max(0, target_dt - elapsed)

                await asyncio.sleep(sleep_time)

            except Exception:
                break

    except asyncio.CancelledError:
        # If the task is cancelled, we just exit the loop
        pass


def render_loop(canvas, func):
    loop = asyncio.get_event_loop()
    task = loop.create_task(_call_repeated(canvas, func))
    return lambda: task.cancel()
