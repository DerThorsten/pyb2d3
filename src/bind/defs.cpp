#include <string>
#include <unordered_set>
#include <vector>

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

#include "bind.hpp"
#include "defs_common.hpp"
#include "pyb2d3/core/binder.hpp"
#include "pyb2d3/core/points.hpp"
#include "pyb2d3/py_chain_def.hpp"
#include "pyb2d3/py_converter.hpp"

#ifndef PYB2D3_NO_THREADING
#    include <pyb2d3/threadpool.hpp>
#endif

namespace pyb2d3::bind
{
    namespace
    {
        // box2d copies the body name on creation, but the def only holds a pointer.
        // Keep the strings alive in a pool so the pointer is valid for any def.
        const char* intern(const std::string& s)
        {
            static std::unordered_set<std::string> pool;
            return pool.insert(s).first->c_str();
        }

#ifndef PYB2D3_NO_THREADING
        void install_thread_pool(b2WorldDef& def, ThreadPool& pool)
        {
            def.userTaskContext = &pool;
            def.workerCount = pool.nThreads();
            def.enqueueTask = [](b2TaskCallbackFcn* task, void* taskContext, void* userContext) -> void*
            {
                auto* threadpool = static_cast<ThreadPool*>(userContext);
                auto* future = new std::future<void>(threadpool->enqueue(
                    [task, taskContext](std::size_t)
                    {
                        task(taskContext);
                    }
                ));
                return future;
            };
            def.finishTask = [](void* userTask, void*)
            {
                auto* future = static_cast<std::future<void>*>(userTask);
                future->get();
                delete future;
            };
        }
#endif
    }  // namespace

    void export_defs(nb::module_& m)
    {
        // ---- world -----------------------------------------------------------------------
        nb::class_<b2Capacity>(m, "Capacity")
            .def(nb::init<>())
            .def_rw("static_shape_count", &b2Capacity::staticShapeCount)
            .def_rw("dynamic_shape_count", &b2Capacity::dynamicShapeCount)
            .def_rw("static_body_count", &b2Capacity::staticBodyCount)
            .def_rw("dynamic_body_count", &b2Capacity::dynamicBodyCount)
            .def_rw("contact_count", &b2Capacity::contactCount)
            .def_rw("arena_byte_count", &b2Capacity::arenaByteCount);

        auto world_def = def_class<b2WorldDef, b2DefaultWorldDef>(m, "WorldDef");
        world_def.def_rw("gravity", &b2WorldDef::gravity)
            .def_rw("restitution_threshold", &b2WorldDef::restitutionThreshold)
            .def_rw("restitution_iterations", &b2WorldDef::restitutionIterations)
            .def_rw("enable_restitution_propagation", &b2WorldDef::enableRestitutionPropagation)
            .def_rw("hit_event_threshold", &b2WorldDef::hitEventThreshold)
            .def_rw("contact_hertz", &b2WorldDef::contactHertz)
            .def_rw("contact_damping_ratio", &b2WorldDef::contactDampingRatio)
            .def_rw("contact_speed", &b2WorldDef::contactSpeed)
            .def_rw("maximum_linear_speed", &b2WorldDef::maximumLinearSpeed)
            .def_rw("enable_sleep", &b2WorldDef::enableSleep)
            .def_rw("enable_continuous", &b2WorldDef::enableContinuous)
            .def_rw("worker_count", &b2WorldDef::workerCount)
            .def_rw("capacity", &b2WorldDef::capacity);
        def_user_data(world_def);
#ifndef PYB2D3_NO_THREADING
        world_def.def("_install_thread_pool", &install_thread_pool, nb::arg("thread_pool"));
#endif

        // ---- body ------------------------------------------------------------------------
        nb::class_<b2MotionLocks>(m, "MotionLocks")
            .def(
                "__init__",
                [](b2MotionLocks* t, bool linear_x, bool linear_y, bool angular_z)
                {
                    new (t) b2MotionLocks{linear_x, linear_y, angular_z};
                },
                nb::arg("linear_x") = false,
                nb::arg("linear_y") = false,
                nb::arg("angular_z") = false
            )
            .def_rw("linear_x", &b2MotionLocks::linearX)
            .def_rw("linear_y", &b2MotionLocks::linearY)
            .def_rw("angular_z", &b2MotionLocks::angularZ);

        auto body_def = def_class<b2BodyDef, b2DefaultBodyDef>(m, "BodyDef");
        body_def.def_rw("type", &b2BodyDef::type)
            .def_rw("position", &b2BodyDef::position)
            .def_rw("rotation", &b2BodyDef::rotation)
            .def_rw("linear_velocity", &b2BodyDef::linearVelocity)
            .def_rw("angular_velocity", &b2BodyDef::angularVelocity)
            .def_rw("linear_damping", &b2BodyDef::linearDamping)
            .def_rw("angular_damping", &b2BodyDef::angularDamping)
            .def_rw("gravity_scale", &b2BodyDef::gravityScale)
            .def_rw("sleep_threshold", &b2BodyDef::sleepThreshold)
            .def_rw("safety_factor", &b2BodyDef::safetyFactor)
            .def_rw("motion_locks", &b2BodyDef::motionLocks)
            .def_rw("enable_sleep", &b2BodyDef::enableSleep)
            .def_rw("is_awake", &b2BodyDef::isAwake)
            .def_rw("is_bullet", &b2BodyDef::isBullet)
            .def_rw("is_enabled", &b2BodyDef::isEnabled)
            .def_rw("allow_fast_rotation", &b2BodyDef::allowFastRotation)
            .def_rw("enable_contact_recycling", &b2BodyDef::enableContactRecycling)
            .def_prop_rw(
                "name",
                [](const b2BodyDef& d)
                {
                    return d.name ? std::string(d.name) : std::string();
                },
                [](b2BodyDef& d, const std::string& name)
                {
                    d.name = intern(name);
                }
            )
            // convenience: shorthand for motion_locks.angular_z
            .def_prop_rw(
                "fixed_rotation",
                [](const b2BodyDef& d)
                {
                    return d.motionLocks.angularZ;
                },
                [](b2BodyDef& d, bool flag)
                {
                    d.motionLocks.angularZ = flag;
                }
            );
        def_user_data(body_def);

        // ---- filters / materials ---------------------------------------------------------
        def_class<b2Filter, b2DefaultFilter>(m, "Filter")
            .def_rw("category_bits", &b2Filter::categoryBits)
            .def_rw("mask_bits", &b2Filter::maskBits)
            .def_rw("group_index", &b2Filter::groupIndex);

        def_class<b2QueryFilter, b2DefaultQueryFilter>(m, "QueryFilter")
            .def_rw("category_bits", &b2QueryFilter::categoryBits)
            .def_rw("mask_bits", &b2QueryFilter::maskBits);

        def_class<b2SurfaceMaterial, b2DefaultSurfaceMaterial>(m, "SurfaceMaterial")
            .def_rw("friction", &b2SurfaceMaterial::friction)
            .def_rw("restitution", &b2SurfaceMaterial::restitution)
            .def_rw("rolling_resistance", &b2SurfaceMaterial::rollingResistance)
            .def_rw("tangent_speed", &b2SurfaceMaterial::tangentSpeed)
            .def_rw("user_material_id", &b2SurfaceMaterial::userMaterialId)
            .def_rw("custom_color", &b2SurfaceMaterial::customColor);

        // ---- shape -----------------------------------------------------------------------
        auto shape_def = def_class<b2ShapeDef, b2DefaultShapeDef>(m, "ShapeDef");
        shape_def.def_rw("material", &b2ShapeDef::material)
            .def_rw("density", &b2ShapeDef::density)
            .def_rw("filter", &b2ShapeDef::filter)
            .def_rw("enable_custom_filtering", &b2ShapeDef::enableCustomFiltering)
            .def_rw("is_sensor", &b2ShapeDef::isSensor)
            .def_rw("enable_sensor_events", &b2ShapeDef::enableSensorEvents)
            .def_rw("enable_contact_events", &b2ShapeDef::enableContactEvents)
            .def_rw("enable_hit_events", &b2ShapeDef::enableHitEvents)
            .def_rw("enable_pre_solve_events", &b2ShapeDef::enablePreSolveEvents)
            .def_rw("invoke_contact_creation", &b2ShapeDef::invokeContactCreation)
            .def_rw("update_body_mass", &b2ShapeDef::updateBodyMass);
        def_user_data(shape_def);

        // ---- chain (owns its points / materials) -----------------------------------------
        nb::class_<PyChainDef>(m, "ChainDef")
            .def(nb::init<>())
            .def(
                "copy",
                [](const PyChainDef& self)
                {
                    return PyChainDef(self);
                }
            )
            .def_prop_rw(
                "points",
                [](const PyChainDef& self)
                {
                    // a copy: the def may reallocate its storage later
                    float* data = nullptr;
                    nb::object arr = detail::make_array<float>(self.points.size(), 2, data);
                    for (std::size_t i = 0; i < self.points.size(); ++i)
                    {
                        batch_value<b2Vec2>::store(data + 2 * i, self.points[i]);
                    }
                    return arr;
                },
                [](PyChainDef& self, const Points& value)
                {
                    self.points.assign(value.data(), value.data() + value.size());
                    self.sync();
                }
            )
            .def_prop_rw(
                "materials",
                [](const PyChainDef& self)
                {
                    return self.materials;
                },
                [](PyChainDef& self, const std::vector<b2SurfaceMaterial>& value)
                {
                    self.materials = value;
                    self.sync();
                }
            )
            .def_prop_rw(
                "filter",
                [](const PyChainDef& self)
                {
                    return self.chain_def.filter;
                },
                [](PyChainDef& self, b2Filter value)
                {
                    self.chain_def.filter = value;
                }
            )
            .def_prop_rw(
                "ghost1",
                [](const PyChainDef& self)
                {
                    return self.prepared().ghost1;
                },
                [](PyChainDef& self, b2Vec2 value)
                {
                    self.chain_def.ghost1 = value;
                    self.ghost1_set = true;
                },
                "Leading ghost point of an open chain (default: continues the first segment)."
            )
            .def_prop_rw(
                "ghost2",
                [](const PyChainDef& self)
                {
                    return self.prepared().ghost2;
                },
                [](PyChainDef& self, b2Vec2 value)
                {
                    self.chain_def.ghost2 = value;
                    self.ghost2_set = true;
                },
                "Trailing ghost point of an open chain (default: continues the last segment)."
            )
            .def_prop_rw(
                "is_loop",
                [](const PyChainDef& self)
                {
                    return self.chain_def.isLoop;
                },
                [](PyChainDef& self, bool value)
                {
                    self.chain_def.isLoop = value;
                }
            )
            .def_prop_rw(
                "enable_sensor_events",
                [](const PyChainDef& self)
                {
                    return self.chain_def.enableSensorEvents;
                },
                [](PyChainDef& self, bool value)
                {
                    self.chain_def.enableSensorEvents = value;
                }
            )
            .def_prop_rw(
                "user_data",
                [](const PyChainDef& self)
                {
                    return reinterpret_cast<user_data_uint>(self.chain_def.userData);
                },
                [](PyChainDef& self, user_data_uint value)
                {
                    self.chain_def.userData = reinterpret_cast<void*>(value);
                }
            );

        // ---- explosion ---------------------------------------------------------------------
        def_class<b2ExplosionDef, b2DefaultExplosionDef>(m, "ExplosionDef")
            .def_rw("mask_bits", &b2ExplosionDef::maskBits)
            .def_rw("position", &b2ExplosionDef::position)
            .def_rw("radius", &b2ExplosionDef::radius)
            .def_rw("falloff", &b2ExplosionDef::falloff)
            .def_rw("impulse_per_length", &b2ExplosionDef::impulsePerLength);

        // ---- profiling -----------------------------------------------------------------------
        nb::class_<b2Profile>(m, "Profile")
            .def_ro("step", &b2Profile::step)
            .def_ro("pairs", &b2Profile::pairs)
            .def_ro("collide", &b2Profile::collide)
            .def_ro("solve", &b2Profile::solve)
            .def_ro("solver_setup", &b2Profile::solverSetup)
            .def_ro("constraints", &b2Profile::constraints)
            .def_ro("prepare_constraints", &b2Profile::prepareConstraints)
            .def_ro("integrate_velocities", &b2Profile::integrateVelocities)
            .def_ro("warm_start", &b2Profile::warmStart)
            .def_ro("solve_impulses", &b2Profile::solveImpulses)
            .def_ro("integrate_positions", &b2Profile::integratePositions)
            .def_ro("relax_impulses", &b2Profile::relaxImpulses)
            .def_ro("restitution", &b2Profile::restitution)
            .def_ro("store_impulses", &b2Profile::storeImpulses)
            .def_ro("split_islands", &b2Profile::splitIslands)
            .def_ro("transforms", &b2Profile::transforms)
            .def_ro("sensor_hits", &b2Profile::sensorHits)
            .def_ro("joint_events", &b2Profile::jointEvents)
            .def_ro("hit_events", &b2Profile::hitEvents)
            .def_ro("refit", &b2Profile::refit)
            .def_ro("bullets", &b2Profile::bullets)
            .def_ro("sleep_islands", &b2Profile::sleepIslands)
            .def_ro("sensors", &b2Profile::sensors);

        nb::class_<b2Counters>(m, "Counters")
            .def_ro("byte_count", &b2Counters::byteCount)
            .def_ro("body_count", &b2Counters::bodyCount)
            .def_ro("shape_count", &b2Counters::shapeCount)
            .def_ro("contact_count", &b2Counters::contactCount)
            .def_ro("joint_count", &b2Counters::jointCount)
            .def_ro("island_count", &b2Counters::islandCount)
            .def_ro("stack_used", &b2Counters::stackUsed)
            .def_ro("static_tree_height", &b2Counters::staticTreeHeight)
            .def_ro("tree_height", &b2Counters::treeHeight)
            .def_ro("task_count", &b2Counters::taskCount)
            .def_ro("awake_contact_count", &b2Counters::awakeContactCount)
            .def_ro("recycled_contact_count", &b2Counters::recycledContactCount)
            .def_prop_ro(
                "color_counts",
                [](const b2Counters& c)
                {
                    return std::vector<int>(std::begin(c.colorCounts), std::end(c.colorCounts));
                }
            );
    }
}  // namespace pyb2d3::bind
