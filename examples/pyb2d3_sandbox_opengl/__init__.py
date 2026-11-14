# OpenglFrontend (imgui-bundle) is imported lazily: the GL renderers of this
# package (draw, shader, debug_draw_gl) are also used without imgui (the
# browser frontend pyb2d3_sandbox_webgl)


def __getattr__(name):
    """lazy `OpenglFrontend` (needs imgui-bundle)"""
    if name == "OpenglFrontend":
        from .opengl_frontend import OpenglFrontend

        return OpenglFrontend
    raise AttributeError(name)
