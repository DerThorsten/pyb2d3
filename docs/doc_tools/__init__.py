# this file
from pathlib import Path
import sys
import pyb2d3  # noqa: F401


this_file = Path(__file__).resolve()
this_dir = this_file.parent
docs_root = this_dir.parent
html_static_path = docs_root / "_static"
repo_root = docs_root.parent
examples_dir = repo_root / "examples"
companion_packages = repo_root / "companion_packages"

# add to sys.path
sys.path.insert(0, str(companion_packages / "pyb2d3_sandbox"))
sys.path.insert(0, str(companion_packages / "pyb2d3_sandbox_pygame"))

from pyb2d3_sandbox_pygame import PygameFrontendSettings, PygameHeadlessSettings  # noqa: E402
from pyb2d3_sandbox_pygame.sample_to_video import sample_to_video  # noqa: E402


github_url = "https://github.com/DerThorsten/pyb2d3"
github_main_url = f"{github_url}/blob/main"


# Add the examples directory to the system path
sys.path.insert(0, str(examples_dir))
import pyb2d3_samples  # noqa: E402


def create_sample_videos():
    out_dir = html_static_path / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)

    headless_settings = PygameHeadlessSettings(world_time_limit=5.0)
    frontend_settings = PygameFrontendSettings(
        canvas_shape=(500, 500),
        headless=True,  # Use headless mode for video creation]
        headless_settings=headless_settings,
    )

    for sample_class in pyb2d3_samples.all_examples:
        lower_name = sample_class.__name__.lower()

        print(f"Creating video for sample: {sample_class.__name__} ({lower_name})")

        # if the file f"{lower_name}.mp4" already exists, skip it
        video_output = out_dir / f"{lower_name}.mp4"
        if video_output.exists():
            print(f"Video {video_output} already exists, skipping.")
            continue

        sample_to_video(
            sample_class=sample_class,
            sample_settings=None,
            frontend_settings=frontend_settings,
            outdir=out_dir,
            outname=lower_name,
            world_time_limit=6.0,
            create_gif=False,  # set to True to create a gif
        )

    # create a sphinx gallery for the videos / gifs
    # create an rst file
    # .. video:: _static/video.mp4
    #     :nocontrols:
    #     :autoplay:
    #     :playsinline:
    #     :muted:
    #     :loop:
    #     :poster: _static/image.png
    #     :width: 100%

    rst_content = [".. grid:: 2"]
    template_str = """
    .. grid-item::

        .. video:: /_static/videos/{video_name}.mp4
            :nocontrols:
            :autoplay:
            :playsinline:
            :muted:
            :loop:
            :poster: ../../_static/videos/{video_name}.png
            :width: 100%




        :octicon:`mark-github`  `Source <{url}>`_



    """
    for sample_class in pyb2d3_samples.all_examples:
        lower_name = sample_class.__name__.lower()

        filename = sys.modules[sample_class.__module__].__file__
        # filename relative to examples_dir
        filename = Path(filename).relative_to(examples_dir)

        url = f"{github_main_url}/examples/{filename}"

        rst_content.append(template_str.format(video_name=lower_name, url=url))

    rst_file = docs_root / "src" / "samples" / "sample_videos.rst"
    with rst_file.open("w") as f:
        f.write("\n".join(rst_content))
