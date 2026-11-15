# OpenglFrontend (imgui-bundle) is imported lazily: the GL renderers of this
# package (draw, shader, debug_draw_gl) are also used without imgui (the
# browser frontend pyb2d3_sandbox_webgl)

import OpenGL

# No glGetError after every GL call. PyOpenGL reads the flag when OpenGL.GL is
# imported the first time, so it is set here, before any module of this package
# imports OpenGL.GL (import this package before OpenGL.GL elsewhere too). In the
# browser every glGetError is a sync with the GPU process: ~35 us per GL call
# with checking vs ~0.5 us without (measured in the sandbox).
OpenGL.ERROR_CHECKING = False


def __getattr__(name):
    """lazy `OpenglFrontend` (needs imgui-bundle)"""
    if name == "OpenglFrontend":
        from .opengl_frontend import OpenglFrontend

        return OpenglFrontend
    raise AttributeError(name)
