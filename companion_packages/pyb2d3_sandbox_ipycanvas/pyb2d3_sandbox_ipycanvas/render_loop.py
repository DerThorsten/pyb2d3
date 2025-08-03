from ipycanvas import hold_canvas as hold_classic_canvas
import asyncio
import time
import sys


async def _call_repeated(func, fps, mandatory_minimum_sleep_time):
    try:
        interval = 1 / fps
        last_start_time = time.time()

        while True:
            start_time = time.time()
            dt = start_time - last_start_time
            last_start_time = start_time
            try:
                func(dt)
            except Exception as e:
                print(f"Error in repeated function call: {e}", file=sys.stderr)
                break

            elapsed_time = time.time() - start_time
            sleep_time = max(mandatory_minimum_sleep_time, interval - elapsed_time)
            await asyncio.sleep(sleep_time)
    except asyncio.CancelledError:
        # If the task is cancelled, we just exit the loop
        pass


def call_repeated(func, fps, mandatory_minimum_sleep_time):
    """Call a function repeatedly at a given frame rate.
    Since we map an fps to requestAnimationFrame, for the
    emscripten/lite environment, we use 60hz as default when fps is 0.

    Args:
        func: The function to call repeatedly.
        fps: The frame rate to call the function at. If 0, requestAnimationFrame
        mandatory_minimum_sleep_time:  a minimum sleep time, even if no sleep would be needed time-wise.
                                This is to give other events a better chance to run.
                                In particular mouse updates
    """
    if fps == 0:
        # this is a special case, because for lite
        # this mean "use requestAnimationFrame"
        # so here we just assume this means 60hz
        fps = 60

    loop = asyncio.get_event_loop()
    task = loop.create_task(_call_repeated(func, fps, mandatory_minimum_sleep_time))

    # Return a lambda that can be used to cancel the loop
    return lambda: task.cancel()


def set_render_loop(canvas, func, fps=0, mandatory_minimum_sleep_time=1 / 100):
    """Set a render loop for the canvas.
    This is used to call the function repeatedly at a given frame rate.
    We use the hold_canvas context manager so we only send one message to the frontend per frame.

    Args:
        canvas: The canvas to set the render loop for.
        func: The function to call repeatedly.
        fps: The frame rate to call the function at. If 0, requestAnimationFrame
    """

    def wrapped_func(dt):
        with hold_classic_canvas():
            func(dt)

    return call_repeated(wrapped_func, fps, mandatory_minimum_sleep_time)
