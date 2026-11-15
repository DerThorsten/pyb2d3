"""Browser frontend of the sandbox (pyjs): the GL renderers of
pyb2d3_sandbox_opengl (instanced shaders) on a WebGL2 canvas via PyOpenGL,
an HTML control panel instead of imgui.

`WebglFrontend` is imported lazily (it needs pyjs, i.e. the browser); the pointer
gesture logic (`gestures`) is plain python and tested outside the browser."""


def __getattr__(name):
    """lazy `WebglFrontend` (needs pyjs)"""
    if name == "WebglFrontend":
        from .webgl_frontend import WebglFrontend

        return WebglFrontend
    raise AttributeError(name)
