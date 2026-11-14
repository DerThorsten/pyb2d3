#include <vector>

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

#include "bind.hpp"
#include "pyb2d3/core/binder.hpp"
#include "pyb2d3/py_converter.hpp"

namespace pyb2d3::bind
{
    namespace
    {
        // small extras that are not a 1:1 box2d function
        float get_angle(b2BodyId id)
        {
            return b2Rot_GetAngle(b2Body_GetRotation(id));
        }

        float get_speed(b2BodyId id)
        {
            return b2Length(b2Body_GetLinearVelocity(id));
        }

        float get_distance_to(b2BodyId id, b2Vec2 point)
        {
            return b2Distance(b2Body_GetPosition(id), point);
        }

        void set_enabled(b2BodyId id, bool flag)
        {
            flag ? b2Body_Enable(id) : b2Body_Disable(id);
        }

        bool get_fixed_rotation(b2BodyId id)
        {
            return b2Body_GetMotionLocks(id).angularZ;
        }

        void set_fixed_rotation(b2BodyId id, bool flag)
        {
            b2MotionLocks locks = b2Body_GetMotionLocks(id);
            locks.angularZ = flag;
            b2Body_SetMotionLocks(id, locks);
        }

        template <class IdT, int (*Count)(b2BodyId), int (*Fill)(b2BodyId, IdT*, int)>
        std::vector<IdT> collect(const Body& self)
        {
            std::vector<IdT> ids(Count(self.id));
            ids.resize(Fill(self.id, ids.data(), static_cast<int>(ids.size())));
            return ids;
        }
    }  // namespace

    void export_body(nb::module_& m)
    {
        nb::enum_<b2BodyType>(m, "BodyType")
            .value("STATIC", b2_staticBody)
            .value("KINEMATIC", b2_kinematicBody)
            .value("DYNAMIC", b2_dynamicBody);

        nb::class_<Body> cls(m, "Body");
        nb::class_<Batch<Body>> batch_cls(m, "Bodies");
        bind_handle(cls, batch_cls);

        Binder b(cls, batch_cls);
        b.rw<b2Body_GetType, b2Body_SetType>("type")
            .rw<b2Body_GetName, b2Body_SetName>("name")

            // pose
            .ro<b2Body_GetPosition>("position")
            .ro<b2Body_GetRotation>("rotation")
            .ro<&get_angle>("angle")
            .ro<b2Body_GetTransform>("transform")
            .def<b2Body_SetTransform>("set_transform", nb::arg("position"), nb::arg("rotation"))
            .def<b2Body_SetTargetTransform>(
                "set_target_transform",
                nb::arg("target"),
                nb::arg("time_step"),
                nb::arg("wake") = true
            )

            // frames
            .def<b2Body_GetLocalPoint>("local_point", nb::arg("world_point"))
            .def<b2Body_GetWorldPoint>("world_point", nb::arg("local_point"))
            .def<b2Body_GetLocalVector>("local_vector", nb::arg("world_vector"))
            .def<b2Body_GetWorldVector>("world_vector", nb::arg("local_vector"))
            .def<b2Body_GetLocalPointVelocity>("local_point_velocity", nb::arg("local_point"))
            .def<b2Body_GetWorldPointVelocity>("world_point_velocity", nb::arg("world_point"))
            .def<&get_distance_to>("distance_to", nb::arg("point"))

            // velocity
            .rw<b2Body_GetLinearVelocity, b2Body_SetLinearVelocity>("linear_velocity")
            .ro<&get_speed>("speed")
            .rw<b2Body_GetAngularVelocity, b2Body_SetAngularVelocity>("angular_velocity")

            // forces and impulses
            .def<b2Body_ApplyForce>("apply_force", nb::arg("force"), nb::arg("point"), nb::arg("wake") = true)
            .def<b2Body_ApplyForceToCenter>("apply_force_to_center", nb::arg("force"), nb::arg("wake") = true)
            .def<b2Body_ApplyTorque>("apply_torque", nb::arg("torque"), nb::arg("wake") = true)
            .def<b2Body_ClearForces>("clear_forces")
            .def<b2Body_ApplyLinearImpulse>(
                "apply_linear_impulse",
                nb::arg("impulse"),
                nb::arg("point"),
                nb::arg("wake") = true
            )
            .def<b2Body_ApplyLinearImpulseToCenter>(
                "apply_linear_impulse_to_center",
                nb::arg("impulse"),
                nb::arg("wake") = true
            )
            .def<b2Body_ApplyAngularImpulse>("apply_angular_impulse", nb::arg("impulse"), nb::arg("wake") = true)

            // mass
            .ro<b2Body_GetMass>("mass")
            .ro<b2Body_GetRotationalInertia>("rotational_inertia")
            .ro<b2Body_GetLocalCenter>("local_center")
            .ro<b2Body_GetWorldCenter>("world_center")
            .rw<b2Body_GetMassData, b2Body_SetMassData>("mass_data")
            .def<b2Body_UpdateMassFromShapes>("update_mass_from_shapes")

            // damping / gravity
            .rw<b2Body_GetLinearDamping, b2Body_SetLinearDamping>("linear_damping")
            .rw<b2Body_GetAngularDamping, b2Body_SetAngularDamping>("angular_damping")
            .rw<b2Body_GetGravityScale, b2Body_SetGravityScale>("gravity_scale")

            // sleep
            .rw<b2Body_IsAwake, b2Body_SetAwake>("awake")
            .def<b2Body_WakeTouching>("wake_touching")
            .rw<b2Body_IsSleepingEnabled, b2Body_EnableSleeping>("sleep_enabled")
            .rw<b2Body_GetSleepThreshold, b2Body_SetSleepThreshold>("sleep_threshold")

            // flags
            .rw<b2Body_IsEnabled, &set_enabled>("enabled")
            .rw<b2Body_GetMotionLocks, b2Body_SetMotionLocks>("motion_locks")
            .rw<&get_fixed_rotation, &set_fixed_rotation>("fixed_rotation")
            .rw<b2Body_IsBullet, b2Body_SetBullet>("bullet")
            .rw<b2Body_GetSafetyFactor, b2Body_SetSafetyFactor>("safety_factor")
            .rw<b2Body_IsContactRecyclingEnabled, b2Body_EnableContactRecycling>("contact_recycling_enabled")
            .def<b2Body_EnableContactEvents>("enable_contact_events", nb::arg("flag"))
            .def<b2Body_EnableHitEvents>("enable_hit_events", nb::arg("flag"))

            // extents / bounds
            .def<b2Body_ComputeBounds>("compute_bounds")
            .ro<b2Body_GetMinExtent>("min_extent")
            .ro<b2Body_GetMaxExtent>("max_extent")
            .ro<b2Body_GetMaxExtentFromOrigin>("max_extent_from_origin")

            // attached things
            .ro<b2Body_GetShapeCount>("shape_count")
            .ro<b2Body_GetJointCount>("joint_count")
            .ro<b2Body_GetContactCapacity>("contact_capacity")

            // shape creation
            .def<b2CreateCircleShape>("create_circle_shape", nb::arg("shape_def"), nb::arg("circle"))
            .def<b2CreateSegmentShape>("create_segment_shape", nb::arg("shape_def"), nb::arg("segment"))
            .def<b2CreateChainSegmentShape>(
                "create_chain_segment_shape",
                nb::arg("shape_def"),
                nb::arg("chain_segment")
            )
            .def<b2CreateCapsuleShape>("create_capsule_shape", nb::arg("shape_def"), nb::arg("capsule"))
            .def<b2CreatePolygonShape>("create_polygon_shape", nb::arg("shape_def"), nb::arg("polygon"));

        cls.def("destroy", &Body::Destroy)
            .def_prop_ro(
                "world",
                [](const Body& self)
                {
                    return b2Body_GetWorld(self.id);
                }
            )
            .def_prop_ro("shapes", &collect<b2ShapeId, b2Body_GetShapeCount, b2Body_GetShapes>)
            .def_prop_ro("joints", &collect<b2JointId, b2Body_GetJointCount, b2Body_GetJoints>)
            .def_prop_ro(
                "contact_data",
                [](const Body& self)
                {
                    std::vector<b2ContactData> data(b2Body_GetContactCapacity(self.id));
                    data.resize(b2Body_GetContactData(self.id, data.data(), static_cast<int>(data.size())));
                    return data;
                }
            )
            .def(
                "create_chain",
                [](const Body& self, const PyChainDef& def)
                {
                    PyChainDef copy = def;  // re-syncs the raw pointers
                    const b2ChainDef prepared = copy.prepared();
                    return b2CreateChain(self.id, &prepared);
                },
                nb::arg("chain_def")
            );
    }
}  // namespace pyb2d3::bind
