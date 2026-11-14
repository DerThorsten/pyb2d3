from pytest import approx

import pyb2d3 as b2d

from .conftest import make_box_body, step

STEPS = 30


def record(world):
    recording = b2d.Recording()
    world.start_recording(recording)
    make_box_body(world, position=(0, -1), hx=20, hy=1, body_type=b2d.BodyType.STATIC)
    body = make_box_body(world, position=(0, 5))
    step(world, STEPS)
    world.overlap_aabb(b2d.aabb((-1, -1), (1, 1)), lambda shape: None)
    world.stop_recording()
    return recording, body


def test_recording(world):
    recording, _ = record(world)
    assert recording.size > 0
    data = recording.data
    assert isinstance(data, bytes) and len(data) == recording.size
    assert b2d.validate_recording(data)
    assert not b2d.validate_recording(b"garbage")


def test_recording_file_roundtrip(world, tmp_path):
    recording, _ = record(world)
    path = tmp_path / "session.b2rec"
    assert recording.save_to_file(str(path))
    loaded = b2d.Recording.from_file(str(path))
    assert loaded.data == recording.data


def test_replay(world):
    recording, body = record(world)
    final_position = tuple(body.position)

    replay = b2d.Replay(recording.data)
    info = replay.info
    assert info.frame_count >= STEPS
    assert info.time_step == approx(1 / 60)
    assert info.sub_step_count == 4

    replay_world = replay.world
    assert isinstance(replay_world, b2d.WorldView) and replay_world.is_valid

    frames = 0
    while not replay.is_at_end and frames < 10 * STEPS:
        replay.step_frame()
        frames += 1
    assert replay.is_at_end
    assert replay.frame == info.frame_count
    assert not replay.has_diverged

    assert replay.body_count >= 2
    replayed = [replay.get_body(i) for i in range(replay.body_count)]
    positions = [tuple(b.position) for b in replayed if b.type == b2d.BodyType.DYNAMIC]
    assert positions[0] == approx(final_position, abs=1e-5)

    assert replay.frame_query_count >= 0

    replay.restart()
    assert replay.frame == 0
    replay.seek_frame(5)
    assert replay.frame == 5

    replay.set_keyframe_policy(budget_bytes=1 << 20, min_interval_frames=4)
    assert replay.keyframe_budget == 1 << 20
    assert replay.keyframe_min_interval == 4
    assert replay.keyframe_interval >= 0
    assert replay.keyframe_bytes >= 0
