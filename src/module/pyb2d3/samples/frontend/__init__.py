from .frontend_base import FrontendBase, EngineSettings
from .default_frontend import DefaultFrontend


def run(sample_class, frontend_class=DefaultFrontend, settings=None):
    """
    Run a sample with the specified frontend.

    :param sample_class: The sample class to run.
    :param frontend_class: The frontend class to use (default is DefaultFrontend).
    :param settings: Optional settings for the frontend.
    """
    if settings is None:
        settings = frontend_class.Settings()

    frontend = frontend_class(settings=settings)
    frontend.run(sample_class)
