#include <cmath>
#include <optional>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/tuple.h>

#include "bind.hpp"
#include "query_context.hpp"
#include "pyb2d3/core/binder.hpp"
#include "pyb2d3/py_converter.hpp"
#include "pyb2d3/recording.hpp"

namespace pyb2d3::bind
{
    namespace
    {
        // ---------------------------------------------------------------------------
        // Python callbacks invoked by box2d *during* a step. Step releases the GIL,
        // so these reacquire it. Exceptions cannot cross box2d's C frames: they are
        // reported as "unraisable" and a neutral default is returned.
        // ---------------------------------------------------------------------------
        template <class R, class F>
        R call_python(R fallback, const char* where, F&& f) noexcept
        {
            nb::gil_scoped_acquire gil;
            try
            {
                return f();
            }
            catch (nb::python_error& e)
            {
                e.discard_as_unraisable(where);
            }
            catch (const std::exception& e)
            {
                PyErr_SetString(PyExc_RuntimeError, e.what());
                PyErr_WriteUnraisable(nb::str(where).ptr());
            }
            return fallback;
        }

        struct StepCallbacks
        {
            nb::object custom_filter;
            nb::object pre_solve;
            nb::object pre_continuous;
        };

        // per world callbacks, keyed by world id (never destroyed at interpreter exit)
        std::unordered_map<uint32_t, StepCallbacks*>& step_callbacks()
        {
            static auto* registry = new std::unordered_map<uint32_t, StepCallbacks*>();
            return *registry;
        }

        StepCallbacks& step_callbacks_for(b2WorldId id)
        {
            auto& registry = step_callbacks();
            auto [it, inserted] = registry.try_emplace(b2StoreWorldId(id), nullptr);
            if (inserted)
            {
                it->second = new StepCallbacks();
            }
            return *it->second;
        }

        void release_step_callbacks(b2WorldId id)
        {
            auto& registry = step_callbacks();
            auto it = registry.find(b2StoreWorldId(id));
            if (it != registry.end())
            {
                delete it->second;
                registry.erase(it);
            }
        }

        bool custom_filter_trampoline(b2ShapeId a, b2ShapeId b, void* ctx)
        {
            return call_python(
                true,
                "custom filter callback",
                [&]
                {
                    return nb::cast<bool>(static_cast<StepCallbacks*>(ctx)->custom_filter(a, b));
                }
            );
        }

        void pre_solve_trampoline(b2ShapeId a, b2ShapeId b, b2Manifold* manifold, void* ctx)
        {
            call_python(
                0,
                "pre-solve callback",
                [&]
                {
                    static_cast<StepCallbacks*>(ctx)->pre_solve(a, b, nb::cast(manifold, nb::rv_policy::reference));
                    return 0;
                }
            );
        }

        bool pre_continuous_trampoline(b2ShapeId a, b2ShapeId b, b2Pos point, b2Vec2 normal, void* ctx)
        {
            return call_python(
                true,
                "pre-continuous callback",
                [&]
                {
                    return nb::cast<bool>(static_cast<StepCallbacks*>(ctx)->pre_continuous(a, b, point, normal));
                }
            );
        }

        // box2d's friction / restitution callbacks have no context: they are global
        nb::object*& friction_callback()
        {
            static nb::object* fn = nullptr;
            return fn;
        }

        nb::object*& restitution_callback()
        {
            static nb::object* fn = nullptr;
            return fn;
        }

        // box2d's default mixing rules, used as fallback if the python callback fails
        float default_friction(float a, float b)
        {
            return std::sqrt(a * b);
        }

        float default_restitution(float a, float b)
        {
            return a > b ? a : b;
        }

        // the slot is global but installed per world: a world may still use the trampoline
        // after another world cleared the callback, fall back to the default rule then
        float friction_trampoline(float fa, uint64_t ma, float fb, uint64_t mb)
        {
            if (friction_callback() == nullptr)
            {
                return default_friction(fa, fb);
            }
            return call_python(
                default_friction(fa, fb),
                "friction callback",
                [&]
                {
                    return nb::cast<float>((*friction_callback())(fa, ma, fb, mb));
                }
            );
        }

        float restitution_trampoline(float ra, uint64_t ma, float rb, uint64_t mb)
        {
            if (restitution_callback() == nullptr)
            {
                return default_restitution(ra, rb);
            }
            return call_python(
                default_restitution(ra, rb),
                "restitution callback",
                [&]
                {
                    return nb::cast<float>((*restitution_callback())(ra, ma, rb, mb));
                }
            );
        }

        void set_global_callback(nb::object*& slot, nb::object fn)
        {
            delete slot;
            slot = fn.is_none() ? nullptr : new nb::object(std::move(fn));
        }

        // ---------------------------------------------------------------------------
        // Query callbacks (see query_context.hpp)
        // ---------------------------------------------------------------------------

        // overlap callbacks: return False to stop, anything else (incl. None) continues
        bool overlap_trampoline(b2ShapeId shape, void* ctx)
        {
            return static_cast<QueryContext*>(ctx)->call(false, continue_or_bool, shape);
        }

        // cast callbacks: return the new max fraction (-1 ignore, 0 stop, 1 continue); None continues
        float cast_trampoline(b2ShapeId shape, b2Pos point, b2Vec2 normal, float fraction, void* ctx)
        {
            return static_cast<QueryContext*>(ctx)->call(0.0f, fraction_or_continue, shape, point, normal, fraction);
        }

        bool plane_trampoline(b2ShapeId shape, const b2PlaneResult* plane, void* ctx)
        {
            return static_cast<QueryContext*>(ctx)->call(false, continue_or_bool, shape, *plane);
        }

        std::tuple<float, float, float> get_contact_tuning(const WorldView& self)
        {
            float hertz = 0.0f, damping_ratio = 0.0f, push_speed = 0.0f;
            b2World_GetContactTuning(self.id, &hertz, &damping_ratio, &push_speed);
            return {hertz, damping_ratio, push_speed};
        }
    }  // namespace

    void export_world(nb::module_& m)
    {
        // release the global mixing callbacks before interpreter shutdown: a callable still
        // installed at exit would otherwise keep python objects alive past finalization
        nb::module_::import_("atexit").attr("register")(nb::cpp_function(
            []
            {
                set_global_callback(friction_callback(), nb::none());
                set_global_callback(restitution_callback(), nb::none());
            }
        ));

        nb::class_<b2RayResult>(m, "RayResult")
            .def_ro("shape", &b2RayResult::shapeId)
            .def_ro("point", &b2RayResult::point)
            .def_ro("normal", &b2RayResult::normal)
            .def_ro("fraction", &b2RayResult::fraction)
            .def_ro("node_visits", &b2RayResult::nodeVisits)
            .def_ro("leaf_visits", &b2RayResult::leafVisits)
            .def_ro("hit", &b2RayResult::hit);

        nb::class_<WorldView> cls(m, "WorldView");
        bind_handle(cls);

        const auto origin = nb::arg("origin") = b2Vec2{0.0f, 0.0f};
        const auto query_filter = nb::arg("query_filter") = b2DefaultQueryFilter();

        Binder(cls)
            .def<b2World_Draw>("_draw", nb::arg("debug_draw"))
            .ro<b2World_GetBounds>("bounds")

            // events
            .def<b2World_GetBodyEvents>("get_body_events")
            .def<b2World_GetSensorEvents>("get_sensor_events")
            .def<b2World_GetContactEvents>("get_contact_events")
            .def<b2World_GetJointEvents>("get_joint_events")

            // settings
            .rw<b2World_GetGravity, b2World_SetGravity>("gravity")
            .rw<b2World_IsSleepingEnabled, b2World_EnableSleeping>("sleeping_enabled")
            .rw<b2World_IsContinuousEnabled, b2World_EnableContinuous>("continuous_enabled")
            .rw<b2World_IsWarmStartingEnabled, b2World_EnableWarmStarting>("warm_starting_enabled")
            .rw<b2World_GetRestitutionThreshold, b2World_SetRestitutionThreshold>("restitution_threshold")
            .rw<b2World_GetRestitutionIterations, b2World_SetRestitutionIterations>("restitution_iterations")
            .rw<b2World_IsRestitutionPropagationEnabled, b2World_EnableRestitutionPropagation>(
                "restitution_propagation_enabled"
            )
            .rw<b2World_GetHitEventThreshold, b2World_SetHitEventThreshold>("hit_event_threshold")
            .rw<b2World_GetContactRecycleDistance, b2World_SetContactRecycleDistance>("contact_recycle_distance")
            .rw<b2World_GetMaxLinearSpeed, b2World_SetMaxLinearSpeed>("max_linear_speed")
            .rw<b2World_GetWorkerCount, b2World_SetWorkerCount>("worker_count")
            .def<b2World_EnableSSE2Fallback>("enable_sse2_fallback", nb::arg("flag"))
            .def<b2World_SetContactTuning>(
                "set_contact_tuning",
                nb::arg("hertz"),
                nb::arg("damping_ratio"),
                nb::arg("push_speed")
            )

            // statistics
            .ro<b2World_GetAwakeBodyCount>("awake_body_count")
            .ro<b2World_GetProfile>("profile")
            .ro<b2World_GetCounters>("counters")
            .ro<b2World_GetMaxCapacity>("max_capacity")
            .ro<b2World_GetStateHash>("state_hash")
            .def<b2World_DumpMemoryStats>("dump_memory_stats")
            .def<b2World_RebuildStaticTree>("rebuild_static_tree")

            // creation
            .def<b2World_Explode>("_explode", nb::arg("explosion_def"))
            .def<b2CreateBody>("create_body_from_def", nb::arg("body_def"))
            .def<b2CreateDistanceJoint>("_create_distance_joint", nb::arg("def"))
            .def<b2CreateFilterJoint>("_create_filter_joint", nb::arg("def"))
            .def<b2CreateMotorJoint>("_create_motor_joint", nb::arg("def"))
            .def<b2CreateMoverJoint>("_create_mover_joint", nb::arg("def"))
            .def<b2CreatePogoJoint>("_create_pogo_joint", nb::arg("def"))
            .def<b2CreatePrismaticJoint>("_create_prismatic_joint", nb::arg("def"))
            .def<b2CreateRevoluteJoint>("_create_revolute_joint", nb::arg("def"))
            .def<b2CreateWeldJoint>("_create_weld_joint", nb::arg("def"))
            .def<b2CreateWheelJoint>("_create_wheel_joint", nb::arg("def"))

            // queries without callback
            .def<b2World_CastRayClosest>(
                "cast_ray_closest",
                nb::arg("origin"),
                nb::arg("translation"),
                query_filter
            );

        cls.def(
               "destroy",
               [](WorldView& self)
               {
                   release_step_callbacks(self.id);
                   self.Destroy();
               }
        )
            .def(
                "step",
                [](WorldView& self, float time_step, int sub_step_count)
                {
                    nb::gil_scoped_release release;
                    b2World_Step(self.id, time_step, sub_step_count);
                },
                nb::arg("time_step"),
                nb::arg("sub_step_count") = 4
            )
            .def_prop_ro("contact_tuning", &get_contact_tuning)

            // ---- queries with python callbacks ----------------------------------------------
            .def(
                "overlap_aabb",
                [](WorldView& self, b2AABB aabb, nb::object callback, b2QueryFilter filter, b2Vec2 origin_)
                {
                    QueryContext q(std::move(callback));
                    auto stats = b2World_OverlapAABB(self.id, origin_, aabb, filter, overlap_trampoline, &q);
                    q.rethrow();
                    return stats;
                },
                nb::arg("aabb"),
                nb::arg("callback"),
                query_filter,
                origin
            )
            .def(
                "overlap_shape",
                [](WorldView& self, const b2ShapeProxy& proxy, nb::object callback, b2QueryFilter filter, b2Vec2 origin_)
                {
                    QueryContext q(std::move(callback));
                    auto stats = b2World_OverlapShape(self.id, origin_, &proxy, filter, overlap_trampoline, &q);
                    q.rethrow();
                    return stats;
                },
                nb::arg("proxy"),
                nb::arg("callback"),
                query_filter,
                origin
            )
            .def(
                "cast_ray",
                [](WorldView& self, b2Vec2 origin_, b2Vec2 translation, nb::object callback, b2QueryFilter filter)
                {
                    QueryContext q(std::move(callback));
                    auto stats = b2World_CastRay(self.id, origin_, translation, filter, cast_trampoline, &q);
                    q.rethrow();
                    return stats;
                },
                nb::arg("origin"),
                nb::arg("translation"),
                nb::arg("callback"),
                query_filter
            )
            .def(
                "cast_shape",
                [](WorldView& self,
                   const b2ShapeProxy& proxy,
                   b2Vec2 translation,
                   nb::object callback,
                   b2QueryFilter filter,
                   b2Vec2 origin_)
                {
                    QueryContext q(std::move(callback));
                    auto stats =
                        b2World_CastShape(self.id, origin_, &proxy, translation, filter, cast_trampoline, &q);
                    q.rethrow();
                    return stats;
                },
                nb::arg("proxy"),
                nb::arg("translation"),
                nb::arg("callback"),
                query_filter,
                origin
            )
            .def(
                "cast_mover",
                [](WorldView& self, const b2Capsule& mover, b2Vec2 translation, b2QueryFilter filter, b2Vec2 origin_)
                {
                    return b2World_CastMover(self.id, origin_, &mover, translation, filter);
                },
                nb::arg("mover"),
                nb::arg("translation"),
                query_filter,
                origin
            )
            .def(
                "collide_mover",
                [](WorldView& self, const b2Capsule& mover, nb::object callback, b2QueryFilter filter, b2Vec2 origin_)
                {
                    QueryContext q(std::move(callback));
                    b2World_CollideMover(self.id, origin_, &mover, filter, plane_trampoline, &q);
                    q.rethrow();
                },
                nb::arg("mover"),
                nb::arg("callback"),
                query_filter,
                origin
            )
            .def(
                "shape_at_point",
                &WorldView::ShapeAtPoint,
                nb::arg("point"),
                query_filter,
                nb::arg("dynamic_only") = false
            )
            .def(
                "body_at_point",
                &WorldView::BodyAtPoint,
                nb::arg("point"),
                query_filter,
                nb::arg("dynamic_only") = false
            )

            // ---- step callbacks ---------------------------------------------------------------
            .def(
                "set_custom_filter_callback",
                [](WorldView& self, nb::object fn)
                {
                    auto& cbs = step_callbacks_for(self.id);
                    cbs.custom_filter = fn;
                    b2World_SetCustomFilterCallback(
                        self.id,
                        fn.is_none() ? nullptr : custom_filter_trampoline,
                        &cbs
                    );
                },
                nb::arg("callback").none()
            )
            .def(
                "set_pre_solve_callback",
                [](WorldView& self, nb::object pre_solve, nb::object pre_continuous)
                {
                    auto& cbs = step_callbacks_for(self.id);
                    cbs.pre_solve = pre_solve;
                    cbs.pre_continuous = pre_continuous;
                    b2World_SetPreSolveCallback(
                        self.id,
                        pre_solve.is_none() ? nullptr : pre_solve_trampoline,
                        pre_continuous.is_none() ? nullptr : pre_continuous_trampoline,
                        &cbs
                    );
                },
                nb::arg("pre_solve").none() = nb::none(),
                nb::arg("pre_continuous").none() = nb::none()
            )
            .def(
                "set_friction_callback",
                [](WorldView& self, nb::object fn)
                {
                    const bool clear = fn.is_none();
                    set_global_callback(friction_callback(), std::move(fn));
                    b2World_SetFrictionCallback(self.id, clear ? nullptr : friction_trampoline);
                },
                nb::arg("callback").none(),
                "Set the friction mixing callback ``f(friction_a, material_a, friction_b, material_b) -> float``\n"
                "(``material_*`` are the shapes' ``surface_material.user_material_id``). ``None`` restores\n"
                "box2d's default rule (``sqrt(friction_a * friction_b)``) for this world.\n\n"
                "Warning: box2d passes no context (not even the world) to this callback, so pyb2d3 keeps a\n"
                "single python callback shared by all worlds: setting it on one world replaces it for every\n"
                "world that has one installed, and clearing it makes those worlds fall back to the default\n"
                "rule. For per world rules, encode the world in ``user_material_id`` and branch on it."
            )
            .def(
                "set_restitution_callback",
                [](WorldView& self, nb::object fn)
                {
                    const bool clear = fn.is_none();
                    set_global_callback(restitution_callback(), std::move(fn));
                    b2World_SetRestitutionCallback(self.id, clear ? nullptr : restitution_trampoline);
                },
                nb::arg("callback").none(),
                "Set the restitution mixing callback ``f(restitution_a, material_a, restitution_b, material_b)\n"
                "-> float``. ``None`` restores box2d's default rule (``max(restitution_a, restitution_b)``).\n\n"
                "Warning: like the friction callback this is a single python callback shared by all worlds\n"
                "(see ``set_friction_callback``)."
            )

            // ---- snapshots / recording ---------------------------------------------------------
            .def(
                "get_snapshot",
                [](WorldView& self)
                {
                    const int size = b2World_GetSnapshot(self.id, nullptr, 0);
                    if (size <= 0)
                    {
                        throw nb::value_error("cannot snapshot a world while it is stepping");
                    }
                    std::vector<uint8_t> image(size);
                    b2World_GetSnapshot(self.id, image.data(), size);
                    return nb::bytes(image.data(), image.size());
                }
            )
            .def(
                "restore_from_snapshot",
                [](WorldView& self, nb::bytes image)
                {
                    return b2World_RestoreFromSnapshot(
                        self.id,
                        static_cast<const uint8_t*>(image.data()),
                        static_cast<int>(image.size())
                    );
                },
                nb::arg("image")
            )
            .def(
                "start_recording",
                [](WorldView& self, PyRecording& recording)
                {
                    b2World_StartRecording(self.id, recording.id);
                },
                nb::arg("recording"),
                nb::keep_alive<1, 2>()
            )
            .def(
                "stop_recording",
                [](WorldView& self)
                {
                    b2World_StopRecording(self.id);
                }
            );

        m.def(
            "create_world_id",
            [](const b2WorldDef& def)
            {
                return b2StoreWorldId(b2CreateWorld(&def));
            },
            nb::arg("def")
        );

        m.def(
            "create_world_id_from_snapshot",
            [](nb::bytes image, int worker_count)
            {
                b2WorldId id = b2CreateWorldFromSnapshot(
                    static_cast<const uint8_t*>(image.data()),
                    static_cast<int>(image.size()),
                    worker_count
                );
                if (!b2World_IsValid(id))
                {
                    throw nb::value_error("invalid snapshot");
                }
                return b2StoreWorldId(id);
            },
            nb::arg("image"),
            nb::arg("worker_count") = 0
        );
    }
}  // namespace pyb2d3::bind
