from .default_frontend import DefaultFrontend


def run(
    sample_class, sample_settings=None, frontend_class=None, frontend_settings=None
):
    """
    Run a sample with the specified sample settings, frontend class, and frontend settings.


    """
    if sample_settings is None:
        sample_settings = sample_class.Settings()

    if frontend_class is None:
        frontend_class = DefaultFrontend

    if frontend_settings is None:
        frontend_settings = frontend_class.Settings()

    frontend = frontend_class(settings=frontend_settings)
    frontend.run(sample_class, sample_settings=sample_settings)
