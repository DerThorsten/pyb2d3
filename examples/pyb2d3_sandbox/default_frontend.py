import os
import traceback

_CachedDefaultFrontend = None


def _opengl():
    from pyb2d3_sandbox_opengl import OpenglFrontend

    return OpenglFrontend


def _pygame():
    from pyb2d3_sandbox_pygame import PygameFrontend

    return PygameFrontend


# in order of preference
_FRONTENDS = {"opengl": _opengl, "pygame": _pygame}


def get_default_frontend():
    """The frontend named by PYB2D3_SANDBOX_DEFAULT_FRONTEND, else the first available one."""
    global _CachedDefaultFrontend
    if _CachedDefaultFrontend is not None:
        return _CachedDefaultFrontend

    name = os.environ.get("PYB2D3_SANDBOX_DEFAULT_FRONTEND")
    if name:
        loader = _FRONTENDS.get(name.lower())
        if loader is None:
            raise ValueError(
                f"unknown PYB2D3_SANDBOX_DEFAULT_FRONTEND={name!r}, expected one of {list(_FRONTENDS)}"
            )
        _CachedDefaultFrontend = loader()
        return _CachedDefaultFrontend

    tracebacks = []
    for loader in _FRONTENDS.values():
        try:
            _CachedDefaultFrontend = loader()
            return _CachedDefaultFrontend
        except ImportError:
            tracebacks.append(traceback.format_exc())

    raise ImportError(
        "No sandbox frontend available, the OpenGL frontend needs imgui-bundle and PyOpenGL, "
        "the pygame frontend needs pygame.\nTracebacks of the import errors:\n" + "".join(tracebacks)
    )
