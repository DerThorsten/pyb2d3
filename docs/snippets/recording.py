import os
import tempfile

import pyb2d3 as b2d


def build(world):
    ground = world.create_static_body(position=(0, -1))
    ground.create_shape(b2d.shape_def(), b2d.box(20, 1))
    for i in range(10):
        body = world.create_dynamic_body(position=(0, 1 + i))
        body.create_shape(b2d.shape_def(), b2d.box(0.4, 0.4))


# --- snapshots: save / restore the full simulation state ------------------------------
world = b2d.World()
build(world)
image = world.get_snapshot()  # bytes
for _ in range(60):
    world.step(1 / 60, 4)
world.restore_from_snapshot(image)  # back to the saved state (user data is cleared)
clone = b2d.World.from_snapshot(image)  # an independent copy

# --- recording: log every api call for exact replay ---------------------------------------
recording = b2d.Recording()
world = b2d.World()
world.start_recording(recording)
build(world)
for _ in range(60):
    world.step(1 / 60, 4)
world.stop_recording()

path = os.path.join(tempfile.mkdtemp(), "session.b2rec")
recording.save_to_file(path)

# --- replay -------------------------------------------------------------------------------
replay = b2d.Replay(b2d.Recording.from_file(path).data)
print(replay.info.frame_count, "frames")
while not replay.is_at_end:
    replay.step_frame()
assert not replay.has_diverged  # determinism check
replay.seek_frame(30)
print(replay.world.counters.body_count, "bodies in the replay world")
