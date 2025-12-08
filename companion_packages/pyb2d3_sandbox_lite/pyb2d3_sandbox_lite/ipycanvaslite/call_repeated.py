import pyjs
import sys


# call a function repeatedly at a given frame rate
# when fps is 0, requestAnimationFrame is used
def call_repeated(func, fps=0):
    """Call a function repeatedly at a given frame rate.
    If fps is 0, requestAnimationFrame is used.

    Args:
        func: The function to call repeatedly.
        fps: The frame rate to call the function at. If 0, requestAnimationFrame
    """
    pyjs.set_main_loop_callback(func, fps)


# set a render loop for the canvas
# this is used to call the function repeatedly at a given frame rate
# if the canvas is **not** an offscreen canvas, we use the hold_canvas context manager
# st. we we only send one message to the frontend per frame
def set_render_loop(canvas, func, fps=0):
    """Set a render loop for the canvas.
    This is used to call the function repeatedly at a given frame rate.
    If the canvas is **not** an offscreen canvas, we use the hold_canvas context
    manager st. we only send one message to the frontend per frame.

    Args:
        canvas: The canvas to set the render loop for.
        func: The function to call repeatedly.
        fps: The frame rate to call the function at. If 0, requestAnimationFrame
    """

    def wrapped_func(dt):
        try:
            func(dt)
        except Exception as e:
            # the best we can do there is catch the error and print it to the error stream
            print(f"Error in requestAnimationFrame callback: {e}", file=sys.stderr)
            pyjs.cancel_main_loop()

    pyjs.set_main_loop_callback(wrapped_func, 0)
    # return a lambda which can be used to cancel the loop
    return lambda: pyjs.cancel_main_loop()
