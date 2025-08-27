import traceback
import os

_CachedDefaultFrontend = None

has_pyjs = False
try:
    import pyjs  # noqa

    has_pyjs = True
except ImportError:
    pass


def is_notebook() -> bool:
    try:
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell" or shell == "XPythonShell":
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False  # Probably standard Python interpreter


def compare_case_insensitive(a: str, b: str) -> bool:
    """
    Compare two strings case-insensitively.
    """
    return a.lower() == b.lower()


def get_default_frontend():
    global _CachedDefaultFrontend
    if _CachedDefaultFrontend is not None:
        return _CachedDefaultFrontend

    # check for certain env variables
    PYB2D3_SANDBOX_DEFAULT_FRONTEND = os.environ.get("PYB2D3_SANDBOX_DEFAULT_FRONTEND", None)
    if PYB2D3_SANDBOX_DEFAULT_FRONTEND:
        if compare_case_insensitive(PYB2D3_SANDBOX_DEFAULT_FRONTEND, "OPENGL"):
            from pyb2d3_sandbox_opengl import OpenglFrontend

            _CachedDefaultFrontend = OpenglFrontend
            return _CachedDefaultFrontend
        elif compare_case_insensitive(PYB2D3_SANDBOX_DEFAULT_FRONTEND, "PYGAME"):
            from pyb2d3_sandbox_pygame import PygameFrontend

            _CachedDefaultFrontend = PygameFrontend
            return _CachedDefaultFrontend
        elif compare_case_insensitive(PYB2D3_SANDBOX_DEFAULT_FRONTEND, "IPYCANVAS"):
            from pyb2d3_sandbox_ipycanvas import IpycanvasFrontend

            _CachedDefaultFrontend = IpycanvasFrontend
            return _CachedDefaultFrontend

    tracebacks = []

    if not is_notebook():
        # Check if OpenglFrontend is available
        has_opengl_frontend = True
        try:
            from pyb2d3_sandbox_opengl import OpenglFrontend
        except ImportError:
            has_opengl_frontend = False
            tracebacks.append(traceback.format_exc())
        if has_opengl_frontend:
            _CachedDefaultFrontend = OpenglFrontend
            return _CachedDefaultFrontend

        # check if PygameFrontend is available
        has_pygame_frontend = True
        try:
            from pyb2d3_sandbox_pygame import PygameFrontend
        except ImportError:
            has_pygame_frontend = False
            tracebacks.append(traceback.format_exc())
        if has_pygame_frontend:
            _CachedDefaultFrontend = PygameFrontend
            return _CachedDefaultFrontend

        raise ImportError(f"""No default frontend available. Please install either pyb2d3-sandbox-opengl or pyb2d3-sandbox-pygame.
Tracebacks of the import errors:
{"".join(tracebacks)}""")

    else:
        # for vanilla-Jupyter we use "jupyter-frontend"
        if not has_pyjs:
            has_jupyter_frontend = True
            try:
                from pyb2d3_sandbox_jupyter import JupyterFrontend
            except ImportError:
                has_jupyter_frontend = False
                tracebacks.append(traceback.format_exc())
            if has_jupyter_frontend:
                _CachedDefaultFrontend = JupyterFrontend
                return _CachedDefaultFrontend
        # for lite-Jupyter we use "ipycanvas-frontend"
        else:
            # Check if IpycanvasFrontend is available
            has_ipycanvas_frontend = True
            try:
                from pyb2d3_sandbox_ipycanvas import IpycanvasFrontend
            except ImportError:
                has_ipycanvas_frontend = False
                tracebacks.append(traceback.format_exc())
            if has_ipycanvas_frontend:
                _CachedDefaultFrontend = IpycanvasFrontend
                return _CachedDefaultFrontend

        raise ImportError(f"""No default frontend available. Please install pyb2d3-sandbox-ipycanvas for Jupyter notebook support.
Tracebacks of the import errors:
{"".join(tracebacks)}""")
