#include <string>

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

#include "bind.hpp"
#include "pyb2d3/core/binder.hpp"
#include "pyb2d3/py_converter.hpp"
#include "pyb2d3/recording.hpp"

namespace pyb2d3::bind
{
    void export_recording(nb::module_& m)
    {
        // ---- recording ------------------------------------------------------------------
        nb::class_<PyRecording> rec(m, "Recording");
        rec.def(nb::init<int>(), nb::arg("byte_capacity") = 0)
            .def_static("from_file", &PyRecording::from_file, nb::arg("path"))
            .def_prop_ro(
                "data",
                [](const PyRecording& self)
                {
                    return nb::bytes(b2Recording_GetData(self.id), b2Recording_GetSize(self.id));
                }
            );
        Binder(rec)
            .ro<b2Recording_GetSize>("size")
            .def<&b2Recording_SaveToFile>("save_to_file", nb::arg("path"));

        m.def(
            "validate_recording",
            [](nb::bytes data, int worker_count)
            {
                return b2ValidateRecording(data.data(), static_cast<int>(data.size()), worker_count);
            },
            nb::arg("data"),
            nb::arg("worker_count") = 0
        );

        // ---- replay ---------------------------------------------------------------------
        nb::class_<b2ReplayInfo>(m, "ReplayInfo")
            .def_ro("frame_count", &b2ReplayInfo::frameCount)
            .def_ro("worker_count", &b2ReplayInfo::workerCount)
            .def_ro("time_step", &b2ReplayInfo::timeStep)
            .def_ro("sub_step_count", &b2ReplayInfo::subStepCount)
            .def_ro("length_scale", &b2ReplayInfo::lengthScale)
            .def_ro("bounds", &b2ReplayInfo::bounds);

        nb::enum_<b2ReplayQueryType>(m, "ReplayQueryType")
            .value("OVERLAP_AABB", b2_replayQueryOverlapAABB)
            .value("OVERLAP_SHAPE", b2_replayQueryOverlapShape)
            .value("CAST_RAY", b2_replayQueryCastRay)
            .value("CAST_SHAPE", b2_replayQueryCastShape)
            .value("COLLIDE_MOVER", b2_replayQueryCollideMover)
            .value("CAST_RAY_CLOSEST", b2_replayQueryCastRayClosest)
            .value("CAST_MOVER", b2_replayQueryCastMover);

        nb::class_<b2ReplayQueryInfo>(m, "ReplayQueryInfo")
            .def_ro("type", &b2ReplayQueryInfo::type)
            .def_ro("filter", &b2ReplayQueryInfo::filter)
            .def_ro("aabb", &b2ReplayQueryInfo::aabb)
            .def_ro("origin", &b2ReplayQueryInfo::origin)
            .def_ro("translation", &b2ReplayQueryInfo::translation)
            .def_ro("hit_count", &b2ReplayQueryInfo::hitCount);

        nb::class_<b2ReplayQueryHit>(m, "ReplayQueryHit")
            .def_ro("shape", &b2ReplayQueryHit::shapeId)
            .def_ro("point", &b2ReplayQueryHit::point)
            .def_ro("normal", &b2ReplayQueryHit::normal)
            .def_ro("fraction", &b2ReplayQueryHit::fraction);

        nb::class_<PyReplay> replay(m, "Replay");
        replay.def(
            "__init__",
            [](PyReplay* self, nb::bytes data, int worker_count)
            {
                new (self) PyReplay(data.data(), static_cast<int>(data.size()), worker_count);
            },
            nb::arg("data"),
            nb::arg("worker_count") = 0
        );
        Binder(replay)
            .def<b2Replay_StepFrame>("step_frame")
            .def<b2Replay_Restart>("restart")
            .def<b2Replay_SeekFrame>("seek_frame", nb::arg("frame"))
            .ro<b2Replay_GetWorldId>("world")
            .ro<b2Replay_GetFrame>("frame")
            .ro<b2Replay_GetInfo>("info")
            .ro<b2Replay_IsAtEnd>("is_at_end")
            .ro<b2Replay_HasDiverged>("has_diverged")
            .ro<b2Replay_GetDivergeFrame>("diverge_frame")
            .def<b2Replay_SetKeyframePolicy>(
                "set_keyframe_policy",
                nb::arg("budget_bytes"),
                nb::arg("min_interval_frames")
            )
            .ro<b2Replay_GetKeyframeBudget>("keyframe_budget")
            .ro<b2Replay_GetKeyframeMinInterval>("keyframe_min_interval")
            .ro<b2Replay_GetKeyframeInterval>("keyframe_interval")
            .ro<b2Replay_GetKeyframeBytes>("keyframe_bytes")
            .def<b2Replay_DrawFrameQueries>("draw_frame_queries", nb::arg("debug_draw"), nb::arg("query_index"))
            .ro<b2Replay_GetFrameQueryCount>("frame_query_count")
            .def<b2Replay_GetFrameQuery>("get_frame_query", nb::arg("index"))
            .def<b2Replay_GetFrameQueryHit>("get_frame_query_hit", nb::arg("query_index"), nb::arg("hit_index"))
            .ro<b2Replay_GetBodyCount>("body_count")
            .def<b2Replay_GetBodyId>("get_body", nb::arg("index"));
    }
}  // namespace pyb2d3::bind
