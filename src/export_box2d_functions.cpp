#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <pyb2d/py_converter.hpp>

#include "py_chain_def.hpp"
#include "py_debug_draw.hpp"
#include "pyb2d/wrapper_structs.hpp"


// C
// extern "C"
// {
#include <box2d/box2d.h>
#include <box2d/math_functions.h>
// }

// nanobind namespace
namespace nb = nanobind;

void export_world_class(nb::module_& m)
{
    nb::class_<WorldView>(m, "WorldView")
        .def(nb::init<uint64_t>(), nb::arg("world_id"))
        .def_prop_ro(
            "id",
            [](WorldView& self)
            {
                return (uint32_t) ((self.id.index1 << 16) | self.id.generation);
            }
        )
        .def("destroy", &WorldView::Destroy)
        .def("is_valid", &WorldView::IsValid)
        .def("step", &WorldView::Step, nb::arg("time_step"), nb::arg("sub_step_count"))
        .def(
            "draw",
            [](WorldView& self, PyDebugDraw* py_draw)
            {
                b2DebugDraw* draw = static_cast<b2DebugDraw*>(py_draw);
                self.Draw(draw);
            },
            nb::arg("draw")
        )
        .def("get_body_events", &WorldView::GetBodyEvents)
        .def("get_sensor_events", &WorldView::GetSensorEvents)
        .def("get_contact_events", &WorldView::GetContactEvents)
        .def(
            "overlap_aabb",
            [](WorldView& self, b2AABB aabb, b2QueryFilter filter, nanobind::object& fcn)
            {
                // lambda without captures st. we can pass it to the C function
                auto fcn_lambda = [](b2ShapeId shape_id, void* context) -> bool
                {
                    auto callable = static_cast<nanobind::object*>(context);
                    return nanobind::cast<bool>(callable->operator()(shape_id));
                };

                void* context = &fcn;
                b2TreeStats stats = b2World_OverlapAABB(self.id, aabb, filter, fcn_lambda, context);
                return stats;
            },
            nb::arg("aabb"),
            nb::arg("filter"),
            nb::arg("fcn")
        )
        .def(
            "cast_ray",
            &WorldView::CastRay,
            nb::arg("origin"),
            nb::arg("translation"),
            nb::arg("filter"),
            nb::arg("fcn"),
            nb::arg("context")
        )
        .def(
            "cast_ray_closest",
            &WorldView::CastRayClosest,
            nb::arg("origin"),
            nb::arg("translation"),
            nb::arg("filter")
        )
        .def_prop_rw("sleeping_enabled", &WorldView::IsSleepingEnabled, &WorldView::EnableSleeping, nb::arg("flag"))
        .def_prop_rw(
            "continuous_enabled",
            &WorldView::IsContinuousEnabled,
            &WorldView::EnableContinuous,
            nb::arg("flag")
        )
        .def_prop_rw(
            "restitution_threshold",
            &WorldView::GetRestitutionThreshold,
            &WorldView::SetRestitutionThreshold,
            nb::arg("value")
        )
        .def_prop_rw(
            "hit_event_threshold",
            &WorldView::GetHitEventThreshold,
            &WorldView::SetHitEventThreshold,
            nb::arg("value")
        )
        .def_prop_rw("gravity", &WorldView::GetGravity, &WorldView::SetGravity, nb::arg("gravity"))
        .def_prop_rw(
            "user_data",
            [](WorldView& self) -> user_data_uint
            {
                return (user_data_uint) b2World_GetUserData(self.id);
            },
            [](WorldView& self, user_data_uint user_data)
            {
                b2World_SetUserData(self.id, (void*) user_data);
            },
            nb::arg("user_data")
        )

        .def("explode", &WorldView::Explode, nb::arg("explosion_def"))
        .def(
            "set_contact_tuning",
            &WorldView::SetContactTuning,
            nb::arg("hertz"),
            nb::arg("damping_ratio"),
            nb::arg("push_velocity")
        )
        .def("set_joint_tuning", &WorldView::SetJointTuning, nb::arg("hertz"), nb::arg("damping_ratio"))
        .def("create_body_from_def", &WorldView::CreateBodyId, nb::arg("def"))
        // .def("create_body_id_from_def", &WorldView::CreateBodyId, nb::arg("def"))
        ;

    m.def(
        "create_world_id",
        [](b2WorldDef def)
        {
            b2WorldId world_id = b2CreateWorld(&def);
            return b2StoreWorldId(world_id);
        },
        nb::arg("def")
    );
}

void export_body_class(nb::module_& m)
{
    nb::class_<Body>(m, "Body")
        .def(nb::init<uint64_t>(), nb::arg("body_id"))
        .def_prop_ro(
            "id",
            [](Body& self)
            {
                return b2StoreBodyId(self.id);
            }
        )
        .def("is_valid", &Body::IsValid)

        .def_prop_rw("type", &Body::GetType, &Body::SetType, nb::arg("type"))
        .def_prop_ro("position", &Body::GetPosition)

        .def_prop_rw("linear_velocity", &Body::GetLinearVelocity, &Body::SetLinearVelocity, nb::arg("velocity"))
        .def_prop_ro("linear_velocity_magnitude", &Body::GetLinearVelocityMagnitude)
        .def_prop_rw("angular_velocity", &Body::GetAngularVelocity, &Body::SetAngularVelocity, nb::arg("velocity"))

        // forces
        .def("apply_force_to_center", &Body::ApplyForceToCenter, nb::arg("force"), nb::arg("wake") = true)
        .def("apply_force", &Body::ApplyForce, nb::arg("force"), nb::arg("point"), nb::arg("wake") = true)
        .def("apply_torque", &Body::ApplyTorque, nb::arg("torque"), nb::arg("wake") = true)
        .def(
            "apply_linear_impulse_to_center",
            &Body::ApplyLinearImpulseToCenter,
            nb::arg("impulse"),
            nb::arg("wake") = true
        )
        .def(
            "apply_linear_impulse",
            &Body::ApplyLinearImpulse,
            nb::arg("impulse"),
            nb::arg("point"),
            nb::arg("wake") = true
        )
        .def("apply_angular_impulse", &Body::ApplyAngularImpulse, nb::arg("impulse"), nb::arg("wake") = true)
        .def("rotational_inertia", &Body::GetRotationalInertia)
        .def("local_center_of_mass", &Body::GetLocalCenterOfMass)
        .def("world_center_of_mass", &Body::GetWorldCenterOfMass)
        .def_prop_rw("mass_data", &Body::GetMassData, &Body::SetMassData, nb::arg("mass_data"))
        .def("apply_mass_from_shapes", &Body::ApplyMassFromShapes)
        .def_prop_rw("linear_damping", &Body::GetLinearDamping, &Body::SetLinearDamping, nb::arg("linear_damping"))
        .def_prop_rw(
            "angular_damping",
            &Body::GetAngularDamping,
            &Body::SetAngularDamping,
            nb::arg("angular_damping")
        )
        .def_prop_rw(
            "sleep_threshold",
            &Body::GetSleepThreshold,
            &Body::SetSleepThreshold,
            nb::arg("sleep_threshold")
        )
        .def_prop_rw("awake", &Body::IsAwake, &Body::SetAwake, nb::arg("awake"))
        .def_prop_rw("enabled_sleep", &Body::IsSleepEnabled, &Body::EnableSleep, nb::arg("enabled"))
        .def_prop_rw("enabled", &Body::IsEnabled, &Body::SetEnabled, nb::arg("enabled"))
        .def("set_transform", &Body::SetTransform, nb::arg("position"), nb::arg("rotation"))
        .def_prop_ro("transform", &Body::GetTransform)
        .def("local_point", &Body::GetLocalPoint)
        .def("world_point", &Body::GetWorldPoint)
        .def("local_vector", &Body::GetLocalVector)
        .def("world_vector", &Body::GetWorldVector)
        .def_prop_rw("fixed_rotation", &Body::IsFixedRotation, &Body::SetFixedRotation, nb::arg("flag"))
        .def_prop_rw(
            "user_data",
            [](Body& self) -> user_data_uint
            {
                return (user_data_uint) b2Body_GetUserData(self.id);
            },
            [](Body& self, user_data_uint user_data)
            {
                b2Body_SetUserData(self.id, (void*) user_data);
            },
            nb::arg("user_data")
        )
        .def_prop_rw("bullet", &Body::IsBullet, &Body::SetBullet, nb::arg("flag"))
        .def_prop_rw("name", &Body::GetName, &Body::SetName, nb::arg("name"))
        .def_prop_ro(
            "world",
            [](Body& self)
            {
                return WorldView(b2Body_GetWorld(self.id));
            }
        )
        .def_prop_ro("shape_count", &Body::GetShapeCount)
        .def("compute_aabb", &Body::ComputeAABB)
        // get all shapes
        .def_prop_ro(
            "shapes",
            [](Body& self)
            {
                int capacity = self.GetShapeCount();
                std::vector<b2ShapeId> shape_ids(capacity);
                int count = self.GetShapes(shape_ids.data(), capacity);
                return shape_ids;
            }
        )


        // Shape creation methods
        .def("create_circle_shape", &Body::CreateCircleShape, nb::arg("def"), nb::arg("circle"))
        .def("create_segment_shape", &Body::CreateSegmentShape, nb::arg("def"), nb::arg("segment"))
        .def("create_capsule_shape", &Body::CreateCapsuleShape, nb::arg("def"), nb::arg("capsule"))
        .def("create_polygon_shape", &Body::CreatePolygonShape, nb::arg("def"), nb::arg("polygon"));
}

void export_shape_class(nb::module_& m)
{
    // shape type enum
    nb::enum_<b2ShapeType>(m, "ShapeType")
        .value("circle", b2_circleShape)
        .value("capsule", b2_capsuleShape)
        .value("segment", b2_segmentShape)
        .value("polygon", b2_polygonShape)
        .value("chain_segment", b2_chainSegmentShape)
        .export_values();

    nb::class_<Shape>(m, "Shape")
        .def(nb::init<uint64_t>(), nb::arg("shape_id"))
        .def_prop_ro(
            "id",
            [](Shape& self)
            {
                return b2StoreShapeId(self.id);
            }
        )
        .def_prop_ro("is_valid", &Shape::IsValid)
        .def_prop_ro("type", &Shape::GetType)
        .def_prop_ro("body", &Shape::GetBody)
        .def_prop_ro("world", &Shape::GetWorld)
        .def_prop_ro("is_sensor", &Shape::IsSensor)
        .def_prop_rw(
            "user_data",
            [](Shape& self) -> user_data_uint
            {
                return (user_data_uint) b2Shape_GetUserData(self.id);
            },
            [](Shape& self, user_data_uint user_data)
            {
                b2Shape_SetUserData(self.id, (void*) user_data);
            },
            nb::arg("user_data")
        )
        .def("set_density", &Shape::SetDensity, nb::arg("density"), nb::arg("update_body_mass") = true)
        .def_prop_ro("density", &Shape::GetDensity)
        .def_prop_rw("friction", &Shape::GetFriction, &Shape::SetFriction, nb::arg("friction"))
        .def_prop_rw("restitution", &Shape::GetRestitution, &Shape::SetRestitution, nb::arg("restitution"))
        .def_prop_rw("material", &Shape::GetMaterial, &Shape::SetMaterial, nb::arg("material"))
        .def_prop_rw(
            "surface_material",
            &Shape::GetSurfaceMaterial,
            &Shape::SetSurfaceMaterial,
            nb::arg("surface_material")
        )
        .def_prop_rw("filter", &Shape::GetFilter, &Shape::SetFilter, nb::arg("filter"))
        .def_prop_rw(
            "sensor_events_enabled",
            &Shape::AreSensorEventsEnabled,
            &Shape::EnableSensorEvents,
            nb::arg("flag")
        )
        .def_prop_rw(
            "contact_events_enabled",
            &Shape::AreContactEventsEnabled,
            &Shape::EnableContactEvents,
            nb::arg("flag")
        )
        .def_prop_rw(
            "pre_solve_events_enabled",
            &Shape::ArePreSolveEventsEnabled,
            &Shape::EnablePreSolveEvents,
            nb::arg("flag")
        )
        .def_prop_rw("hit_events_enabled", &Shape::AreHitEventsEnabled, &Shape::EnableHitEvents, nb::arg("flag"))
        .def("test_point", &Shape::TestPoint, nb::arg("point"))
        .def("ray_cast", &Shape::RayCast, nb::arg("input"))
        .def(
            "cast",
            [](Shape& self)
            {
                return GetCastedShape(self.id);
            }
        );

    nb::class_<CircleShape, Shape>(m, "CircleShape")
        .def(nb::init<uint64_t>(), nb::arg("shape_id"))
        .def_prop_rw(
            "circle",
            [](CircleShape& self)
            {
                return b2Shape_GetCircle(self.id);
            },
            [](CircleShape& self, const b2Circle* circle)
            {
                b2Shape_SetCircle(self.id, circle);
            },
            nb::arg("circle")
        );

    nb::class_<CapsuleShape, Shape>(m, "CapsuleShape")
        .def(nb::init<uint64_t>(), nb::arg("shape_id"))
        .def_prop_rw(
            "capsule",
            [](CapsuleShape& self)
            {
                return b2Shape_GetCapsule(self.id);
            },
            [](CapsuleShape& self, const b2Capsule* capsule)
            {
                b2Shape_SetCapsule(self.id, capsule);
            },
            nb::arg("capsule")
        );

    nb::class_<SegmentShape, Shape>(m, "SegmentShape")
        .def(nb::init<uint64_t>(), nb::arg("shape_id"))
        .def_prop_rw(
            "segment",
            [](SegmentShape& self)
            {
                return b2Shape_GetSegment(self.id);
            },
            [](SegmentShape& self, const b2Segment* segment)
            {
                b2Shape_SetSegment(self.id, segment);
            },
            nb::arg("segment")
        );

    nb::class_<PolygonShape, Shape>(m, "PolygonShape")
        .def(nb::init<uint64_t>(), nb::arg("shape_id"))
        .def_prop_rw(
            "polygon",
            [](PolygonShape& self)
            {
                return b2Shape_GetPolygon(self.id);
            },
            [](PolygonShape& self, const b2Polygon* polygon)
            {
                b2Shape_SetPolygon(self.id, polygon);
            },
            nb::arg("polygon")
        );

    m.def(
        "get_casted_shape",
        [](uint64_t shape_id)
        {
            b2ShapeId id = b2LoadShapeId(shape_id);
            return GetCastedShape(id);
        },
        nb::arg("shape_id")
    );
}

void export_chain_functions(nb::module_& m)
{
    // m.def("create_chain", &b2CreateChain, nb::arg("body_id"), nb::arg("def"));
    m.def(
        "create_chain",
        [](b2BodyId body_id, PyChainDef& def) -> b2ChainId
        {
            return b2CreateChain(body_id, &def.chain_def);
        },
        nb::arg("body_id"),
        nb::arg("chain_def")
    );

    m.def("destroy_chain", &b2DestroyChain, nb::arg("chain_id"));
    m.def("chain_get_world", &b2Chain_GetWorld, nb::arg("chain_id"));
    m.def("chain_get_segment_count", &b2Chain_GetSegmentCount, nb::arg("chain_id"));
    m.def(
        "chain_get_segments",
        &b2Chain_GetSegments,
        nb::arg("chain_id"),
        nb::arg("segment_array"),
        nb::arg("capacity")
    );
    m.def("chain_set_friction", &b2Chain_SetFriction, nb::arg("chain_id"), nb::arg("friction"));
    m.def("chain_get_friction", &b2Chain_GetFriction, nb::arg("chain_id"));
    m.def("chain_set_restitution", &b2Chain_SetRestitution, nb::arg("chain_id"), nb::arg("restitution"));
    m.def("chain_get_restitution", &b2Chain_GetRestitution, nb::arg("chain_id"));
    m.def("chain_is_valid", &b2Chain_IsValid, nb::arg("id"));
}

void export_joint_functions_generic(nb::module_& m)
{
    m.def("destroy_joint", &b2DestroyJoint, nb::arg("joint_id"));
    m.def("joint_is_valid", &b2Joint_IsValid, nb::arg("id"));
    m.def("joint_get_type", &b2Joint_GetType, nb::arg("joint_id"));
    m.def("joint_get_body_a", &b2Joint_GetBodyA, nb::arg("joint_id"));
    m.def("joint_get_body_b", &b2Joint_GetBodyB, nb::arg("joint_id"));
    m.def("joint_get_world", &b2Joint_GetWorld, nb::arg("joint_id"));
    m.def("joint_get_local_anchor_a", &b2Joint_GetLocalAnchorA, nb::arg("joint_id"));
    m.def("joint_get_local_anchor_b", &b2Joint_GetLocalAnchorB, nb::arg("joint_id"));
    m.def(
        "joint_set_collide_connected",
        &b2Joint_SetCollideConnected,
        nb::arg("joint_id"),
        nb::arg("should_collide")
    );
    m.def("joint_get_collide_connected", &b2Joint_GetCollideConnected, nb::arg("joint_id"));
    m.def("joint_wake_bodies", &b2Joint_WakeBodies, nb::arg("joint_id"));
    m.def("joint_get_constraint_force", &b2Joint_GetConstraintForce, nb::arg("joint_id"));
    m.def("joint_get_constraint_torque", &b2Joint_GetConstraintTorque, nb::arg("joint_id"));
    m.def(
        "joint_set_user_data",
        [](b2JointId joint_id, user_data_uint user_data)
        {
            b2Joint_SetUserData(joint_id, (void*) user_data);
        },
        nb::arg("joint_id"),
        nb::arg("user_data")
    );
    m.def(
        "joint_get_user_data",
        [](b2JointId joint_id)
        {
            return (user_data_uint) b2Joint_GetUserData(joint_id);
        },
        nb::arg("joint_id")
    );
}

void export_distance_joint_functions(nb::module_& m)
{
    m.def("create_distance_joint", &b2CreateDistanceJoint, nb::arg("world_id"), nb::arg("def"));
    m.def("distance_joint_set_length", &b2DistanceJoint_SetLength, nb::arg("joint_id"), nb::arg("length"));
    m.def("distance_joint_get_length", &b2DistanceJoint_GetLength, nb::arg("joint_id"));
    m.def(
        "distance_joint_enable_spring",
        &b2DistanceJoint_EnableSpring,
        nb::arg("joint_id"),
        nb::arg("enable_spring")
    );
    m.def("distance_joint_is_spring_enabled", &b2DistanceJoint_IsSpringEnabled, nb::arg("joint_id"));
    m.def("distance_joint_set_spring_hertz", &b2DistanceJoint_SetSpringHertz, nb::arg("joint_id"), nb::arg("hertz"));
    m.def("distance_joint_get_spring_hertz", &b2DistanceJoint_GetSpringHertz, nb::arg("joint_id"));
    m.def(
        "distance_joint_set_spring_damping_ratio",
        &b2DistanceJoint_SetSpringDampingRatio,
        nb::arg("joint_id"),
        nb::arg("damping_ratio")
    );
    m.def("distance_joint_get_spring_damping_ratio", &b2DistanceJoint_GetSpringDampingRatio, nb::arg("joint_id"));
    m.def("distance_joint_enable_limit", &b2DistanceJoint_EnableLimit, nb::arg("joint_id"), nb::arg("enable_limit"));
    m.def("distance_joint_is_limit_enabled", &b2DistanceJoint_IsLimitEnabled, nb::arg("joint_id"));
    m.def(
        "distance_joint_set_length_range",
        &b2DistanceJoint_SetLengthRange,
        nb::arg("joint_id"),
        nb::arg("min_length"),
        nb::arg("max_length")
    );
    m.def("distance_joint_get_min_length", &b2DistanceJoint_GetMinLength, nb::arg("joint_id"));
    m.def("distance_joint_get_max_length", &b2DistanceJoint_GetMaxLength, nb::arg("joint_id"));
    m.def("distance_joint_get_current_length", &b2DistanceJoint_GetCurrentLength, nb::arg("joint_id"));
    m.def("distance_joint_enable_motor", &b2DistanceJoint_EnableMotor, nb::arg("joint_id"), nb::arg("enable_motor"));
    m.def("distance_joint_is_motor_enabled", &b2DistanceJoint_IsMotorEnabled, nb::arg("joint_id"));
    m.def(
        "distance_joint_set_motor_speed",
        &b2DistanceJoint_SetMotorSpeed,
        nb::arg("joint_id"),
        nb::arg("motor_speed")
    );
    m.def("distance_joint_get_motor_speed", &b2DistanceJoint_GetMotorSpeed, nb::arg("joint_id"));
    m.def(
        "distance_joint_set_max_motor_force",
        &b2DistanceJoint_SetMaxMotorForce,
        nb::arg("joint_id"),
        nb::arg("max_force")
    );
    m.def("distance_joint_get_max_motor_force", &b2DistanceJoint_GetMaxMotorForce, nb::arg("joint_id"));
    m.def("distance_joint_get_motor_force", &b2DistanceJoint_GetMotorForce, nb::arg("joint_id"));
}

void export_motor_joint_functions(nb::module_& m)
{
    m.def("create_motor_joint", &b2CreateMotorJoint, nb::arg("world_id"), nb::arg("def"));
    m.def(
        "motor_joint_set_linear_offset",
        &b2MotorJoint_SetLinearOffset,
        nb::arg("joint_id"),
        nb::arg("linear_offset")
    );
    m.def("motor_joint_get_linear_offset", &b2MotorJoint_GetLinearOffset, nb::arg("joint_id"));
    m.def(
        "motor_joint_set_angular_offset",
        &b2MotorJoint_SetAngularOffset,
        nb::arg("joint_id"),
        nb::arg("angular_offset")
    );
    m.def("motor_joint_get_angular_offset", &b2MotorJoint_GetAngularOffset, nb::arg("joint_id"));
    m.def("motor_joint_set_max_force", &b2MotorJoint_SetMaxForce, nb::arg("joint_id"), nb::arg("max_force"));
    m.def("motor_joint_get_max_force", &b2MotorJoint_GetMaxForce, nb::arg("joint_id"));
    m.def("motor_joint_set_max_torque", &b2MotorJoint_SetMaxTorque, nb::arg("joint_id"), nb::arg("max_torque"));
    m.def("motor_joint_get_max_torque", &b2MotorJoint_GetMaxTorque, nb::arg("joint_id"));
    m.def(
        "motor_joint_set_correction_factor",
        &b2MotorJoint_SetCorrectionFactor,
        nb::arg("joint_id"),
        nb::arg("correction_factor")
    );
    m.def("motor_joint_get_correction_factor", &b2MotorJoint_GetCorrectionFactor, nb::arg("joint_id"));
}

void export_mouse_joint_functions(nb::module_& m)
{
    m.def("create_mouse_joint", &b2CreateMouseJoint, nb::arg("world_id"), nb::arg("def"));
    m.def("mouse_joint_set_target", &b2MouseJoint_SetTarget, nb::arg("joint_id"), nb::arg("target"));
    m.def("mouse_joint_get_target", &b2MouseJoint_GetTarget, nb::arg("joint_id"));
    m.def("mouse_joint_set_spring_hertz", &b2MouseJoint_SetSpringHertz, nb::arg("joint_id"), nb::arg("hertz"));
    m.def("mouse_joint_get_spring_hertz", &b2MouseJoint_GetSpringHertz, nb::arg("joint_id"));
    m.def(
        "mouse_joint_set_spring_damping_ratio",
        &b2MouseJoint_SetSpringDampingRatio,
        nb::arg("joint_id"),
        nb::arg("damping_ratio")
    );
    m.def("mouse_joint_get_spring_damping_ratio", &b2MouseJoint_GetSpringDampingRatio, nb::arg("joint_id"));
    m.def("mouse_joint_set_max_force", &b2MouseJoint_SetMaxForce, nb::arg("joint_id"), nb::arg("max_force"));
    m.def("mouse_joint_get_max_force", &b2MouseJoint_GetMaxForce, nb::arg("joint_id"));
}

void export_prismatic_joint_functions(nb::module_& m)
{
    m.def("create_prismatic_joint", &b2CreatePrismaticJoint, nb::arg("world_id"), nb::arg("def"));
    m.def(
        "prismatic_joint_enable_spring",
        &b2PrismaticJoint_EnableSpring,
        nb::arg("joint_id"),
        nb::arg("enable_spring")
    );
    m.def("prismatic_joint_is_spring_enabled", &b2PrismaticJoint_IsSpringEnabled, nb::arg("joint_id"));
    m.def(
        "prismatic_joint_set_spring_hertz",
        &b2PrismaticJoint_SetSpringHertz,
        nb::arg("joint_id"),
        nb::arg("hertz")
    );
    m.def("prismatic_joint_get_spring_hertz", &b2PrismaticJoint_GetSpringHertz, nb::arg("joint_id"));
    m.def(
        "prismatic_joint_set_spring_damping_ratio",
        &b2PrismaticJoint_SetSpringDampingRatio,
        nb::arg("joint_id"),
        nb::arg("damping_ratio")
    );
    m.def("prismatic_joint_get_spring_damping_ratio", &b2PrismaticJoint_GetSpringDampingRatio, nb::arg("joint_id"));
    m.def(
        "prismatic_joint_enable_limit",
        &b2PrismaticJoint_EnableLimit,
        nb::arg("joint_id"),
        nb::arg("enable_limit")
    );
    m.def("prismatic_joint_is_limit_enabled", &b2PrismaticJoint_IsLimitEnabled, nb::arg("joint_id"));
    m.def("prismatic_joint_get_lower_limit", &b2PrismaticJoint_GetLowerLimit, nb::arg("joint_id"));
    m.def("prismatic_joint_get_upper_limit", &b2PrismaticJoint_GetUpperLimit, nb::arg("joint_id"));
    m.def(
        "prismatic_joint_set_limits",
        &b2PrismaticJoint_SetLimits,
        nb::arg("joint_id"),
        nb::arg("lower"),
        nb::arg("upper")
    );
    m.def(
        "prismatic_joint_enable_motor",
        &b2PrismaticJoint_EnableMotor,
        nb::arg("joint_id"),
        nb::arg("enable_motor")
    );
    m.def("prismatic_joint_is_motor_enabled", &b2PrismaticJoint_IsMotorEnabled, nb::arg("joint_id"));
    m.def(
        "prismatic_joint_set_motor_speed",
        &b2PrismaticJoint_SetMotorSpeed,
        nb::arg("joint_id"),
        nb::arg("motor_speed")
    );
    m.def("prismatic_joint_get_motor_speed", &b2PrismaticJoint_GetMotorSpeed, nb::arg("joint_id"));
    m.def("prismatic_joint_get_motor_force", &b2PrismaticJoint_GetMotorForce, nb::arg("joint_id"));
    m.def(
        "prismatic_joint_set_max_motor_force",
        &b2PrismaticJoint_SetMaxMotorForce,
        nb::arg("joint_id"),
        nb::arg("force")
    );
    m.def("prismatic_joint_get_max_motor_force", &b2PrismaticJoint_GetMaxMotorForce, nb::arg("joint_id"));
    m.def("prismatic_joint_get_current_length", &b2PrismaticJoint_GetMotorForce, nb::arg("joint_id"));
    m.def("prismatic_joint_get_translation", &b2PrismaticJoint_GetTranslation, nb::arg("joint_id"));
    m.def("prismatic_joint_get_speed", &b2PrismaticJoint_GetSpeed, nb::arg("joint_id"));
}

void export_revolute_joint_functions(nb::module_& m)
{
    m.def("create_revolute_joint", &b2CreateRevoluteJoint, nb::arg("world_id"), nb::arg("def"));
    m.def(
        "revolute_joint_enable_spring",
        &b2RevoluteJoint_EnableSpring,
        nb::arg("joint_id"),
        nb::arg("enable_spring")
    );
    m.def("revolute_joint_is_spring_enabled", &b2RevoluteJoint_IsSpringEnabled, nb::arg("joint_id"));
    m.def("revolute_joint_set_spring_hertz", &b2RevoluteJoint_SetSpringHertz, nb::arg("joint_id"), nb::arg("hertz"));
    m.def("revolute_joint_get_spring_hertz", &b2RevoluteJoint_GetSpringHertz, nb::arg("joint_id"));
    m.def(
        "revolute_joint_set_spring_damping_ratio",
        &b2RevoluteJoint_SetSpringDampingRatio,
        nb::arg("joint_id"),
        nb::arg("damping_ratio")
    );
    m.def("revolute_joint_get_spring_damping_ratio", &b2RevoluteJoint_GetSpringDampingRatio, nb::arg("joint_id"));
    m.def("revolute_joint_get_angle", &b2RevoluteJoint_GetAngle, nb::arg("joint_id"));
    m.def("revolute_joint_enable_limit", &b2RevoluteJoint_EnableLimit, nb::arg("joint_id"), nb::arg("enable_limit"));
    m.def("revolute_joint_is_limit_enabled", &b2RevoluteJoint_IsLimitEnabled, nb::arg("joint_id"));
    m.def("revolute_joint_get_lower_limit", &b2RevoluteJoint_GetLowerLimit, nb::arg("joint_id"));
    m.def("revolute_joint_get_upper_limit", &b2RevoluteJoint_GetUpperLimit, nb::arg("joint_id"));
    m.def(
        "revolute_joint_set_limits",
        &b2RevoluteJoint_SetLimits,
        nb::arg("joint_id"),
        nb::arg("lower"),
        nb::arg("upper")
    );
    m.def("revolute_joint_enable_motor", &b2RevoluteJoint_EnableMotor, nb::arg("joint_id"), nb::arg("enable_motor"));
    m.def("revolute_joint_is_motor_enabled", &b2RevoluteJoint_IsMotorEnabled, nb::arg("joint_id"));
    m.def(
        "revolute_joint_set_motor_speed",
        &b2RevoluteJoint_SetMotorSpeed,
        nb::arg("joint_id"),
        nb::arg("motor_speed")
    );
    m.def("revolute_joint_get_motor_speed", &b2RevoluteJoint_GetMotorSpeed, nb::arg("joint_id"));
    m.def("revolute_joint_get_motor_torque", &b2RevoluteJoint_GetMotorTorque, nb::arg("joint_id"));
    m.def(
        "revolute_joint_set_max_motor_torque",
        &b2RevoluteJoint_SetMaxMotorTorque,
        nb::arg("joint_id"),
        nb::arg("torque")
    );
    m.def("revolute_joint_get_max_motor_torque", &b2RevoluteJoint_GetMaxMotorTorque, nb::arg("joint_id"));
}

void export_weld_joint_functions(nb::module_& m)
{
    m.def("create_weld_joint", &b2CreateWeldJoint, nb::arg("world_id"), nb::arg("def"));
    m.def("weld_joint_get_reference_angle", &b2WeldJoint_GetReferenceAngle, nb::arg("joint_id"));
    m.def(
        "weld_joint_set_reference_angle",
        &b2WeldJoint_SetReferenceAngle,
        nb::arg("joint_id"),
        nb::arg("angle_in_radians")
    );
    m.def("weld_joint_set_linear_hertz", &b2WeldJoint_SetLinearHertz, nb::arg("joint_id"), nb::arg("hertz"));
    m.def("weld_joint_get_linear_hertz", &b2WeldJoint_GetLinearHertz, nb::arg("joint_id"));
    m.def(
        "weld_joint_set_linear_damping_ratio",
        &b2WeldJoint_SetLinearDampingRatio,
        nb::arg("joint_id"),
        nb::arg("damping_ratio")
    );
    m.def("weld_joint_get_linear_damping_ratio", &b2WeldJoint_GetLinearDampingRatio, nb::arg("joint_id"));
    m.def("weld_joint_set_angular_hertz", &b2WeldJoint_SetAngularHertz, nb::arg("joint_id"), nb::arg("hertz"));
    m.def("weld_joint_get_angular_hertz", &b2WeldJoint_GetAngularHertz, nb::arg("joint_id"));
    m.def(
        "weld_joint_set_angular_damping_ratio",
        &b2WeldJoint_SetAngularDampingRatio,
        nb::arg("joint_id"),
        nb::arg("damping_ratio")
    );
    m.def("weld_joint_get_angular_damping_ratio", &b2WeldJoint_GetAngularDampingRatio, nb::arg("joint_id"));
}

void export_wheel_joint_functions(nb::module_& m)
{
    m.def("create_wheel_joint", &b2CreateWheelJoint, nb::arg("world_id"), nb::arg("def"));
    m.def("wheel_joint_enable_spring", &b2WheelJoint_EnableSpring, nb::arg("joint_id"), nb::arg("enable_spring"));
    m.def("wheel_joint_is_spring_enabled", &b2WheelJoint_IsSpringEnabled, nb::arg("joint_id"));
    m.def("wheel_joint_set_spring_hertz", &b2WheelJoint_SetSpringHertz, nb::arg("joint_id"), nb::arg("hertz"));
    m.def("wheel_joint_get_spring_hertz", &b2WheelJoint_GetSpringHertz, nb::arg("joint_id"));
    m.def(
        "wheel_joint_set_spring_damping_ratio",
        &b2WheelJoint_SetSpringDampingRatio,
        nb::arg("joint_id"),
        nb::arg("damping_ratio")
    );
    m.def("wheel_joint_get_spring_damping_ratio", &b2WheelJoint_GetSpringDampingRatio, nb::arg("joint_id"));
    m.def("wheel_joint_enable_limit", &b2WheelJoint_EnableLimit, nb::arg("joint_id"), nb::arg("enable_limit"));
    m.def("wheel_joint_is_limit_enabled", &b2WheelJoint_IsLimitEnabled, nb::arg("joint_id"));
    m.def("wheel_joint_get_lower_limit", &b2WheelJoint_GetLowerLimit, nb::arg("joint_id"));
    m.def("wheel_joint_get_upper_limit", &b2WheelJoint_GetUpperLimit, nb::arg("joint_id"));
    m.def("wheel_joint_set_limits", &b2WheelJoint_SetLimits, nb::arg("joint_id"), nb::arg("lower"), nb::arg("upper"));
    m.def("wheel_joint_enable_motor", &b2WheelJoint_EnableMotor, nb::arg("joint_id"), nb::arg("enable_motor"));
    m.def("wheel_joint_is_motor_enabled", &b2WheelJoint_IsMotorEnabled, nb::arg("joint_id"));
    m.def("wheel_joint_set_motor_speed", &b2WheelJoint_SetMotorSpeed, nb::arg("joint_id"), nb::arg("motor_speed"));
    m.def("wheel_joint_get_motor_speed", &b2WheelJoint_GetMotorSpeed, nb::arg("joint_id"));
    m.def(
        "wheel_joint_set_max_motor_torque",
        &b2WheelJoint_SetMaxMotorTorque,
        nb::arg("joint_id"),
        nb::arg("torque")
    );
    m.def("wheel_joint_get_max_motor_torque", &b2WheelJoint_GetMaxMotorTorque, nb::arg("joint_id"));
    m.def("wheel_joint_get_motor_torque", &b2WheelJoint_GetMotorTorque, nb::arg("joint_id"));
}

void export_joint_functions(nb::module_& m)
{
    export_joint_functions_generic(m);
    export_distance_joint_functions(m);
    export_motor_joint_functions(m);
    export_mouse_joint_functions(m);
    export_prismatic_joint_functions(m);
    export_revolute_joint_functions(m);
    export_weld_joint_functions(m);
    export_wheel_joint_functions(m);
}

void export_box2d_functions(nb::module_& m)
{
    export_world_class(m);
    export_body_class(m);
    export_shape_class(m);
    // export_shape_class(m);
    export_chain_functions(m);
    export_joint_functions(m);
}
