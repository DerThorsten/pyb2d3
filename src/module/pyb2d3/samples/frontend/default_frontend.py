import traceback

_CachedDefaultFrontend = None


def get_default_frontend():
    global _CachedDefaultFrontend
    if _CachedDefaultFrontend is not None:
        return _CachedDefaultFrontend

    def is_notebook() -> bool:
        try:
            shell = get_ipython().__class__.__name__
            if shell == "ZMQInteractiveShell":
                return True  # Jupyter notebook or qtconsole
            elif shell == "TerminalInteractiveShell":
                return False  # Terminal running IPython
            else:
                return False  # Other type (?)
        except NameError:
            return False  # Probably standard Python interpreter

    if not is_notebook():
        # Check if PygameFrontend is available
        has_pygame_frontend = True
        try:
            from .pygame_frontend import PygameFrontend
        except ImportError:
            has_pygame_frontend = False
            traceback.print_exc()

        if has_pygame_frontend:
            _DefaultFrontend = PygameFrontend
        else:
            raise RuntimeError(
                "No frontend available. Please install pygame to use the PygameFrontend."
            )

    else:
        # Check if IpyCanvasFrontend is available
        has_ipycanvas_frontend = True
        try:
            from .ipycanvas_frontend import IpycanvasFrontend
        except ImportError:
            has_ipycanvas_frontend = False
            traceback.print_exc()

        if has_ipycanvas_frontend:
            _DefaultFrontend = IpycanvasFrontend
        else:
            raise RuntimeError(
                "No frontend available. Please install ipycanvas to use the IpycanvasFrontend."
            )
    _CachedDefaultFrontend = _DefaultFrontend
    return _CachedDefaultFrontend
