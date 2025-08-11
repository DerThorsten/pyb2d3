from .pygame_frontend import (
    PygameFrontend,
    PygameFrontendSettings,
    PygameHeadlessSettings,
)

# to create a temp dir
import os
import tempfile
import pygame
import subprocess


def sample_to_video(
    sample_class,
    sample_settings=None,
    frontend_settings=None,
    outdir=None,
    outname="output",
    world_time_limit=5.0,
    create_gif=True,
    scale_gif_width=320,
    max_gif_fps=30,
):
    if frontend_settings is None:
        frontend_settings = PygameFrontendSettings()
    else:
        assert isinstance(frontend_settings, PygameFrontendSettings)

    hertz = frontend_settings.hertz

    # create a temporary directory for the frames
    frame_dir = tempfile.mkdtemp()

    def screenshot_callback(screen, world_time, iteration):
        filename = os.path.join(frame_dir, f"frame_{iteration:04d}.png")
        pygame.image.save(screen, filename)

    def create_video_from_frames(frame_dir, output, framerate):
        cmd = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(framerate),
            "-i",
            f"{frame_dir}/frame_%04d.png",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            output,
        ]
        subprocess.run(cmd, check=True)

    def create_gif_from_video(video_file, output_gif, fps, scale_gif_width):
        palette = "/tmp/palette.png"
        if scale_gif_width is not None:
            filters = f"fps={fps},scale={scale_gif_width}:-1:flags=lanczos"
        else:
            # filter without scaling
            filters = f"fps={fps}"

        # 1. Generate palette
        cmd_palette = [
            "ffmpeg",
            "-y",
            "-i",
            video_file,
            "-vf",
            f"{filters},palettegen",
            palette,
        ]
        subprocess.run(cmd_palette, check=True)

        # 2. Create GIF using palette
        cmd_gif = [
            "ffmpeg",
            "-y",
            "-i",
            video_file,
            "-i",
            palette,
            "-lavfi",
            f"{filters} [x]; [x][1:v] paletteuse",
            output_gif,
        ]
        subprocess.run(cmd_gif, check=True)

    frontend_settings.headless = True
    frontend_settings.headless_settings = PygameHeadlessSettings(
        world_time_limit=world_time_limit, screenshot_callback=screenshot_callback
    )

    sample_class.run(
        frontend_class=PygameFrontend,
        sample_settings=sample_settings,
        frontend_settings=frontend_settings,
    )

    if outdir is None:
        video_output = f"{outname}.mp4"
    else:
        video_output = os.path.join(outdir, f"{outname}.mp4")
    create_video_from_frames(frame_dir, output=video_output, framerate=hertz)

    if outdir is None:
        output = f"{outname}.gif"
    else:
        output = os.path.join(outdir, f"{outname}.gif")

    if create_gif:
        create_gif_from_video(
            video_output,
            output,
            fps=min(max_gif_fps, hertz),
            scale_gif_width=scale_gif_width,
        )

    # save the first frame as a thumbnail
    first_frame = os.path.join(frame_dir, "frame_0000.png")
    thumbnail_output = os.path.join(outdir, f"{outname}.png")
    if os.path.exists(first_frame):
        os.rename(first_frame, thumbnail_output)
