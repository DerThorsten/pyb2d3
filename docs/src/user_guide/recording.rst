Snapshots, Recording and Replay
===============================

.. literalinclude:: ../../snippets/recording.py
   :language: python

Snapshots
---------

``world.get_snapshot()`` returns the full simulation state as ``bytes``,
``world.restore_from_snapshot(image)`` restores it in place (ids of objects that existed at the
time stay valid) and :meth:`pyb2d3.World.from_snapshot` creates a new world. Snapshots hold
simulation state only: user data and callbacks are not included. Use them for undo, rollback
networking, save games or resetting episodes. The format is experimental in Box2D and may
change between versions.

Restoring in place puts every body, shape and joint that existed at the snapshot back into its
snapshot state (pose, velocities, enabled, ...). Objects created after the snapshot are removed
and their handles become invalid, so things added during an episode disappear on reset. The
``user_data`` of bodies, shapes and joints is reset to 0 (keep your own mapping from ids
instead).

Recording and replay
--------------------

A :class:`~pyb2d3.Recording` logs every API call made on a world after
``world.start_recording(recording)``. ``recording.data`` / ``recording.save_to_file(path)``
store it; :class:`~pyb2d3.Replay` plays it back step by step (``step_frame``, ``seek_frame``,
``restart``) in its own world (``replay.world``). ``replay.has_diverged`` reports whether the
replay reproduced the recorded state hashes, which makes recordings great bug reports and
determinism tests.
