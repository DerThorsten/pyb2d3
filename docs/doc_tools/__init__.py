"""The docs' sample gallery: videos of the samples registered with ``video=True``
(rendered headless with the pygame frontend), grouped by category."""

import html
import sys
from pathlib import Path

import pyb2d3  # noqa: F401

this_dir = Path(__file__).resolve().parent
docs_root = this_dir.parent
html_static_path = docs_root / "_static"
repo_root = docs_root.parent
examples_dir = repo_root / "examples"

# the sandbox, its frontends and the samples live in examples/
sys.path.insert(0, str(examples_dir))

from pyb2d3_sandbox_pygame import PygameFrontendSettings, PygameHeadlessSettings  # noqa: E402
from pyb2d3_sandbox_pygame.sample_to_video import sample_to_video  # noqa: E402
import pyb2d3_samples  # noqa: E402, F401  (registers the samples)
from pyb2d3_sandbox import registry  # noqa: E402

github_url = "https://github.com/DerThorsten/pyb2d3"
github_main_url = f"{github_url}/blob/main"
videos_dir = html_static_path / "videos"

# the samples worth a video (@register_sample(..., video=True)), in registry order
video_entries = [entry for entry in registry if entry.video]


# the screencast of all samples (`pixi run smoke-video`, recorded locally, not in CI):
# an asset of the GitHub release "media", downloaded into _static by every docs build
SANDBOX_TOUR_URL = f"{github_url}/releases/download/media/sandbox_tour.mp4"


def fetch_sandbox_tour():
    """download the sandbox tour video into _static (the start page shows it)"""
    import urllib.request

    target = html_static_path / "sandbox_tour.mp4"
    try:
        with urllib.request.urlopen(SANDBOX_TOUR_URL, timeout=60) as response:
            target.write_bytes(response.read())
    except OSError as e:
        print(f"WARNING: no sandbox tour video ({SANDBOX_TOUR_URL}: {e})")


def video_name(entry):
    return entry.cls.__name__.lower()


def create_sample_videos():
    """render the missing videos, delete those of samples no longer in the gallery
    (sphinx copies all of _static), write src/samples/sample_videos.rst"""
    videos_dir.mkdir(parents=True, exist_ok=True)
    wanted = {video_name(entry) for entry in video_entries}
    for path in videos_dir.iterdir():
        if path.suffix in (".mp4", ".png", ".gif") and path.stem not in wanted:
            path.unlink()

    frontend_settings = PygameFrontendSettings(
        canvas_shape=(500, 500),
        headless=True,
        headless_settings=PygameHeadlessSettings(world_time_limit=5.0),
    )
    for entry in video_entries:
        name = video_name(entry)
        if (videos_dir / f"{name}.mp4").exists():
            continue
        print(f"rendering the video of {entry.key}")
        sample_to_video(
            sample_class=entry.cls,
            sample_settings=None,
            frontend_settings=frontend_settings,
            outdir=videos_dir,
            outname=name,
            world_time_limit=6.0,
            create_gif=False,
        )

    write_gallery(docs_root / "src" / "samples" / "sample_videos.rst")


def gallery_item(entry):
    """one grid item: the looping video, the source link, the sandbox link"""
    name = video_name(entry)
    source = Path(sys.modules[entry.cls.__module__].__file__).relative_to(examples_dir)
    url = f"{github_main_url}/examples/{source.as_posix()}"
    key = html.escape(entry.key, quote=True)
    # anonymous links (`text <url>`__): the same text on every item would clash
    return f"""\
    .. grid-item::

        .. video:: /_static/videos/{name}.mp4
            :nocontrols:
            :autoplay:
            :playsinline:
            :muted:
            :loop:
            :poster: ../../_static/videos/{name}.png
            :width: 100%

        :octicon:`mark-github` `{entry.name} <{url}>`__

        .. raw:: html

            <a class="pyb2d3-sandbox-link" data-sample="{key}">&#9654; run in the browser</a>
"""


def write_gallery(rst_file):
    """the gallery page: a section per category, a two column grid of videos in each
    (samples whose video is not rendered yet, e.g. in a quick build, are left out)"""
    entries = [e for e in video_entries if (videos_dir / f"{video_name(e)}.mp4").exists()]
    lines = []
    for category in dict.fromkeys(entry.category for entry in entries):
        lines += [category, "-" * len(category), "", ".. grid:: 2", ""]
        lines += [gallery_item(entry) for entry in entries if entry.category == category]
    rst_file.write_text("\n".join(lines))
