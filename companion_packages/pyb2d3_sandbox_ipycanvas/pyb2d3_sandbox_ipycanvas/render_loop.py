from ipycanvas import hold_canvas as hold_classic_canvas
import asyncio


async def _call_repeated(func, mandatory_minimum_sleep_time):
    try:
        while True:
            try:
                func()
            except Exception:
                break
            await asyncio.sleep(mandatory_minimum_sleep_time)
    except asyncio.CancelledError:
        # If the task is cancelled, we just exit the loop
        pass


def call_repeated(func, mandatory_minimum_sleep_time):
    loop = asyncio.get_event_loop()
    task = loop.create_task(_call_repeated(func, mandatory_minimum_sleep_time))

    # Return a lambda that can be used to cancel the loop
    return lambda: task.cancel()


def set_render_loop(canvas, func, mandatory_minimum_sleep_time=1 / 100):
    def wrapped_func():
        with hold_classic_canvas(canvas):
            func()

    return call_repeated(wrapped_func, mandatory_minimum_sleep_time)
