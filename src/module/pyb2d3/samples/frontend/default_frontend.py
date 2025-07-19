has_pygame_frontend = True
try:
    from .pygame import PygameFrontend
except ImportError:
    has_pygame_frontend = False


if has_pygame_frontend:
    DefaultFrontend = PygameFrontend
