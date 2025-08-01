#include <optional>

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/vector.h>
#include <pyb2d3/py_converter.hpp>

#include "py_debug_draw.hpp"
#include "pyb2d3/py_chain_def.hpp"
#include "pyb2d3/wrapper_structs.hpp"

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
        .def("_draw", &WorldView::Draw, nb::arg("debug_draw"))
        .def("get_body_events", &WorldView::GetBodyEvents)
        .def("get_sensor_events", &WorldView::GetSensorEvents)
        .def("get_contact_events", &WorldView::GetContactEvents)
        .def(
            "_overlap_aabb",
            [](WorldView& self, b2AABB aabb, b2QueryFilter filter, nanobind::object& fcn)
            {
                // lambda without captures st. we can pass it to the C function
                auto fcn_lambda = [](b2ShapeId shape_id, void* context) -> bool
                {
                    auto callable = static_cast<nanobind::object*>(context);
                    auto result = callable->operator()(shape_id);
                    const bool casted_result = nanobind::cast<bool>(result);
                    return casted_result;
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
            "_cast_ray",
            [](WorldView& self, b2Vec2 origin, b2Vec2 translation, b2QueryFilter filter, nanobind::object& fcn)
            {
                // lambda without captures st. we can pass it to the C function
                auto fcn_lambda =
                    [](b2ShapeId shape_id, b2Vec2 point, b2Vec2 normal, float fraction, void* context) -> float
                {
                    auto callable = static_cast<nanobind::object*>(context);
                    auto result = callable->operator()(shape_id, point, normal, fraction);
                    const float casted_result = nanobind::cast<float>(result);
                    return casted_result;
                };

                void* context = &fcn;
                b2TreeStats stats = b2World_CastRay(self.id, origin, translation, filter, fcn_lambda, context);
                return stats;
            },
            nb::arg("origin"),
            nb::arg("translation"),
            nb::arg("filter"),
            nb::arg("fcn")
        )
        .def(
            "cast_ray_closest",
            &WorldView::CastRayClosest,
            nb::arg("origin"),
            nb::arg("translation"),
            nb::arg("filter") = b2DefaultQueryFilter()
        )
        .def(
            "shape_at_point",
            &WorldView::ShapeAtPoint,
            nb::arg("point"),
            nb::arg("filter") = b2DefaultQueryFilter()
        )
        .def(
            "dyanmic_body_shape_at_point",
            &WorldView::ShapeAtPoint,
            nb::arg("point"),
            nb::arg("filter") = b2DefaultQueryFilter()
        )
        .def("body_at_point", &WorldView::BodyAtPoint, nb::arg("point"), nb::arg("filter") = b2DefaultQueryFilter())
        .def(
            "dynamic_body_at_point",
            &WorldView::DynamicBodyAtPoint,
            nb::arg("point"),
            nb::arg("filter") = b2DefaultQueryFilter()
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

        .def("_explode", &WorldView::Explode, nb::arg("explosion_def"))
        .def(
            "set_contact_tuning",
            &WorldView::SetContactTuning,
            nb::arg("hertz"),
            nb::arg("damping_ratio"),
            nb::arg("push_velocity")
        )
        .def("create_body_from_def", &WorldView::CreateBodyId, nb::arg("def"))

        // extra functions to create joints
        .def("_create_distance_joint", &WorldView::CreateDistanceJoint, nb::arg("def"))
        .def("_create_filter_joint", &WorldView::CreateFilterJoint, nb::arg("def"))
        .def("_create_motor_joint", &WorldView::CreateMotorJoint, nb::arg("def"))
        .def("_create_mouse_joint", &WorldView::CreateMouseJoint, nb::arg("def"))
        .def("_create_prismatic_joint", &WorldView::CreatePrismaticJoint, nb::arg("def"))
        .def("_create_revolute_joint", &WorldView::CreateRevoluteJoint, nb::arg("def"))
        .def("_create_weld_joint", &WorldView::CreateWeldJoint, nb::arg("def"))
        .def("_create_wheel_joint", &WorldView::CreateWheelJoint, nb::arg("def"))

        .def(
            "__eq__",
            [](const WorldView& self, const WorldView& other)
            {
                return b2StoreWorldId(self.id) == b2StoreWorldId(other.id);
            }
        )
        .def(
            "__ne__",
            [](const WorldView& self, const WorldView& other)
            {
                return b2StoreWorldId(self.id) != b2StoreWorldId(other.id);
            }
        )

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
        .def("destroy", &Body::Destroy)

        .def_prop_rw("type", &Body::GetType, &Body::SetType, nb::arg("type"))
        .def_prop_ro("position", &Body::GetPosition)
        .def_prop_ro("angle", &Body::GetAngle)
        .def_prop_ro("rotation", &Body::GetRotation)

        .def_prop_rw("linear_velocity", &Body::GetLinearVelocity, &Body::SetLinearVelocity, nb::arg("velocity"))
        .def("linear_velocity_magnitude", &Body::GetLinearVelocityMagnitude)
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
        .def_prop_rw("gravity_scale", &Body::GetGravityScale, &Body::SetGravityScale, nb::arg("gravity_scale"))
        .def_prop_ro("mass", &Body::GetMass)
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
        .def("create_circle_shape", &Body::CreateCircleShape, nb::arg("shape_def"), nb::arg("circle"))
        .def("create_segment_shape", &Body::CreateSegmentShape, nb::arg("shape_def"), nb::arg("segment"))
        .def("create_capsule_shape", &Body::CreateCapsuleShape, nb::arg("shape_def"), nb::arg("capsule"))
        .def("create_polygon_shape", &Body::CreatePolygonShape, nb::arg("shape_def"), nb::arg("polygon"))

        // chain
        .def("create_chain", &Body::CreateChain, nb::arg("chain_def"))

        // some convienient extra methods
        .def("get_distance_to", &Body::GetDistanceTo, nb::arg("point"))

        // operator == and !=
        .def(
            "__eq__",
            [](const Body& self, const Body& other)
            {
                return b2StoreBodyId(self.id) == b2StoreBodyId(other.id);
            }
        )
        .def(
            "__ne__",
            [](const Body& self, const Body& other)
            {
                return b2StoreBodyId(self.id) != b2StoreBodyId(other.id);
            }
        );
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
        )
        .def(
            "__eq__",
            [](const Shape& self, const Shape& other)
            {
                return b2StoreShapeId(self.id) == b2StoreShapeId(other.id);
            }
        )
        .def(
            "__ne__",
            [](const Shape& self, const Shape& other)
            {
                return b2StoreShapeId(self.id) != b2StoreShapeId(other.id);
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

    // chain segment shape
    nb::class_<ChainSegmentShape, Shape>(m, "ChainSegmentShape")
        .def(nb::init<uint64_t>(), nb::arg("shape_id"))
        .def_prop_ro(
            "segment",
            [](ChainSegmentShape& self)
            {
                return b2Shape_GetSegment(self.id);
            }
        )
        .def_prop_ro(
            "parent_chain",
            [](ChainSegmentShape& self)
            {
                return b2Shape_GetParentChain(self.id);
            }
        );
}

void export_chain_class(nb::module_& m)
{
    nb::class_<Chain>(m, "Chain")
        .def(nb::init<uint64_t>(), nb::arg("chain_id"))
        .def_prop_ro(
            "id",
            [](Chain& self)
            {
                return b2StoreChainId(self.id);
            }
        )
        .def_prop_ro("is_valid", &Chain::IsValid)
        .def_prop_ro("world", &Chain::GetWorld)
        .def_prop_ro("segment_count", &Chain::GetSegmentCount)
        .def(
            "get_segments",
            [](Chain& self)
            {
                int capacity = self.GetSegmentCount();
                std::vector<b2ShapeId> segment_ids(capacity);
                int count = self.GetSegments(segment_ids.data(), capacity);
                return segment_ids;
            }
        )
        .def_prop_rw("friction", &Chain::GetFriction, &Chain::SetFriction, nb::arg("friction"))
        .def_prop_rw("restitution", &Chain::GetRestitution, &Chain::SetRestitution, nb::arg("restitution"))
        .def_prop_rw("material", &Chain::GetMaterial, &Chain::SetMaterial, nb::arg("material"))

        ;
}

void export_joint_classes(nb::module_& m)
{
    nb::class_<Joint>(m, "Joint")
        .def(nb::init<uint64_t>(), nb::arg("joint_id"))
        .def_prop_ro(
            "id",
            [](Joint& self)
            {
                return b2StoreJointId(self.id);
            }
        )

        .def_prop_ro("is_valid", &Joint::IsValid)
        .def("destroy", &Joint::Destroy)
        .def_prop_ro("type", &Joint::GetType)
        .def_prop_ro("body_a", &Joint::GetBodyA)
        .def_prop_ro("body_b", &Joint::GetBodyB)
        .def_prop_ro("world", &Joint::GetWorld)
        .def_prop_ro("local_anchor_a", &Joint::GetLocalAnchorA)
        .def_prop_ro("local_anchor_b", &Joint::GetLocalAnchorB)
        .def("wake_bodies", &Joint::WakeBodies)
        .def("get_constraint_force", &Joint::GetConstraintForce)
        .def("get_constraint_torque", &Joint::GetConstraintTorque)
        .def_prop_rw(
            "user_data",
            [](Joint& self)
            {
                return (user_data_uint) b2Joint_GetUserData(self.id);
            },
            [](Joint& self, user_data_uint user_data)
            {
                b2Joint_SetUserData(self.id, (void*) user_data);
            },
            nb::arg("user_data")
        )
        .def(
            "__eq__",
            [](const Joint& self, const Joint& other)
            {
                return b2StoreJointId(self.id) == b2StoreJointId(other.id);
            }
        )
        .def(
            "__ne__",
            [](const Joint& self, const Joint& other)
            {
                return b2StoreJointId(self.id) != b2StoreJointId(other.id);
            }
        );


    nb::class_<DistanceJoint, Joint>(m, "DistanceJoint")
        .def(nb::init<uint64_t>(), nb::arg("joint_id"))
        .def_prop_rw("length", &DistanceJoint::GetLength, &DistanceJoint::SetLength, nb::arg("length"))
        .def_prop_rw(
            "spring_enabled",
            &DistanceJoint::IsSpringEnabled,
            &DistanceJoint::EnableSpring,
            nb::arg("enabled")
        )
        .def_prop_rw("spring_hertz", &DistanceJoint::GetSpringHertz, &DistanceJoint::SetSpringHertz, nb::arg("hertz"))
        .def_prop_rw(
            "spring_damping_ratio",
            &DistanceJoint::GetSpringDampingRatio,
            &DistanceJoint::SetSpringDampingRatio,
            nb::arg("damping_ratio")
        )
        .def_prop_rw("limit_enabled", &DistanceJoint::IsLimitEnabled, &DistanceJoint::EnableLimit, nb::arg("enabled"))
        .def_prop_ro("min_length", &DistanceJoint::GetMinLength)
        .def_prop_ro("max_length", &DistanceJoint::GetMaxLength)
        .def_prop_ro("current_length", &DistanceJoint::GetCurrentLength)
        .def_prop_rw("motor_enabled", &DistanceJoint::IsMotorEnabled, &DistanceJoint::EnableMotor, nb::arg("enabled"))
        .def_prop_rw("motor_speed", &DistanceJoint::GetMotorSpeed, &DistanceJoint::SetMotorSpeed, nb::arg("speed"))
        .def_prop_rw(
            "max_motor_force",
            &DistanceJoint::GetMaxMotorForce,
            &DistanceJoint::SetMaxMotorForce,
            nb::arg("force")
        )
        .def_prop_ro("motor_force", &DistanceJoint::GetMotorForce);

    nb::class_<MotorJoint, Joint>(m, "MotorJoint")
        .def(nb::init<uint64_t>(), nb::arg("joint_id"))
        .def_prop_rw("linear_offset", &MotorJoint::GetLinearOffset, &MotorJoint::SetLinearOffset, nb::arg("offset"))
        .def_prop_ro("angular_offset", &MotorJoint::GetAngularOffset)
        .def_prop_rw("max_force", &MotorJoint::GetMaxForce, &MotorJoint::SetMaxForce, nb::arg("max_force"))
        .def_prop_rw("max_torque", &MotorJoint::GetMaxTorque, &MotorJoint::SetMaxTorque, nb::arg("max_torque"))
        .def_prop_rw(
            "correction_factor",
            &MotorJoint::GetCorrectionFactor,
            &MotorJoint::SetCorrectionFactor,
            nb::arg("correction_factor")
        );

    nb::class_<MouseJoint, Joint>(m, "MouseJoint")
        .def(nb::init<uint64_t>(), nb::arg("joint_id"))
        .def_prop_rw("target", &MouseJoint::GetTarget, &MouseJoint::SetTarget, nb::arg("target"))
        .def_prop_rw("spring_hertz", &MouseJoint::GetSpringHertz, &MouseJoint::SetSpringHertz, nb::arg("hertz"))
        .def_prop_rw(
            "spring_damping_ratio",
            &MouseJoint::GetSpringDampingRatio,
            &MouseJoint::SetSpringDampingRatio,
            nb::arg("damping_ratio")
        )
        .def_prop_rw("max_force", &MouseJoint::GetMaxForce, &MouseJoint::SetMaxForce, nb::arg("max_force"));

    nb::class_<PrismaticJoint, Joint>(m, "PrismaticJoint")
        .def(nb::init<uint64_t>(), nb::arg("joint_id"))
        .def_prop_rw(
            "spring_enabled",
            &PrismaticJoint::IsSpringEnabled,
            &PrismaticJoint::EnableSpring,
            nb::arg("enabled")
        )
        .def_prop_rw(
            "spring_hertz",
            &PrismaticJoint::GetSpringHertz,
            &PrismaticJoint::SetSpringHertz,
            nb::arg("hertz")
        )
        .def_prop_rw(
            "spring_damping_ratio",
            &PrismaticJoint::GetSpringDampingRatio,
            &PrismaticJoint::SetSpringDampingRatio,
            nb::arg("damping_ratio")
        )
        .def_prop_rw(
            "limit_enabled",
            &PrismaticJoint::IsLimitEnabled,
            &PrismaticJoint::EnableLimit,
            nb::arg("enabled")
        )
        .def_prop_ro("lower_limit", &PrismaticJoint::GetLowerLimit)
        .def_prop_ro("upper_limit", &PrismaticJoint::GetUpperLimit)
        .def_prop_rw(
            "motor_enabled",
            &PrismaticJoint::IsMotorEnabled,
            &PrismaticJoint::EnableMotor,
            nb::arg("enabled")
        )
        .def_prop_rw("motor_speed", &PrismaticJoint::GetMotorSpeed, &PrismaticJoint::SetMotorSpeed, nb::arg("speed"))
        .def_prop_rw(
            "max_motor_force",
            &PrismaticJoint::GetMaxMotorForce,
            &PrismaticJoint::SetMaxMotorForce,
            nb::arg("force")
        )
        .def_prop_ro("translation", &PrismaticJoint::GetTranslation)
        .def_prop_ro("speed", &PrismaticJoint::GetSpeed);

    nb::class_<RevoluteJoint, Joint>(m, "RevoluteJoint")
        .def(nb::init<uint64_t>(), nb::arg("joint_id"))
        .def_prop_rw(
            "spring_enabled",
            &RevoluteJoint::IsSpringEnabled,
            &RevoluteJoint::EnableSpring,
            nb::arg("enabled")
        )
        .def_prop_rw("spring_hertz", &RevoluteJoint::GetSpringHertz, &RevoluteJoint::SetSpringHertz, nb::arg("hertz"))
        .def_prop_rw(
            "spring_damping_ratio",
            &RevoluteJoint::GetSpringDampingRatio,
            &RevoluteJoint::SetSpringDampingRatio,
            nb::arg("damping_ratio")
        )
        .def_prop_ro("angle", &RevoluteJoint::GetAngle)
        .def_prop_rw("limit_enabled", &RevoluteJoint::IsLimitEnabled, &RevoluteJoint::EnableLimit, nb::arg("enabled"))
        .def_prop_ro("lower_limit", &RevoluteJoint::GetLowerLimit)
        .def_prop_ro("upper_limit", &RevoluteJoint::GetUpperLimit)
        .def_prop_rw("motor_enabled", &RevoluteJoint::IsMotorEnabled, &RevoluteJoint::EnableMotor, nb::arg("enabled"))
        .def_prop_rw("motor_speed", &RevoluteJoint::GetMotorSpeed, &RevoluteJoint::SetMotorSpeed, nb::arg("speed"))
        .def_prop_rw(
            "max_motor_torque",
            &RevoluteJoint::GetMaxMotorTorque,
            &RevoluteJoint::SetMaxMotorTorque,
            nb::arg("torque")
        )
        .def_prop_ro("motor_torque", &RevoluteJoint::GetMotorTorque);

    nb::class_<WeldJoint, Joint>(m, "WeldJoint")
        .def(nb::init<uint64_t>(), nb::arg("joint_id"))
        .def_prop_ro("reference_angle", &WeldJoint::GetReferenceAngle)
        .def_prop_rw("linear_hertz", &WeldJoint::GetLinearHertz, &WeldJoint::SetLinearHertz, nb::arg("hertz"))
        .def_prop_rw(
            "linear_damping_ratio",
            &WeldJoint::GetLinearDampingRatio,
            &WeldJoint::SetLinearDampingRatio,
            nb::arg("damping_ratio")
        )
        .def_prop_rw("angular_hertz", &WeldJoint::GetAngularHertz, &WeldJoint::SetAngularHertz, nb::arg("hertz"))
        .def_prop_rw(
            "angular_damping_ratio",
            &WeldJoint::GetAngularDampingRatio,
            &WeldJoint::SetAngularDampingRatio,
            nb::arg("damping_ratio")
        );

    nb::class_<WheelJoint, Joint>(m, "WheelJoint")
        .def(nb::init<uint64_t>(), nb::arg("joint_id"))
        .def_prop_rw("spring_enabled", &WheelJoint::IsSpringEnabled, &WheelJoint::EnableSpring, nb::arg("enabled"))
        .def_prop_rw("spring_hertz", &WheelJoint::GetSpringHertz, &WheelJoint::SetSpringHertz, nb::arg("hertz"))
        .def_prop_rw(
            "spring_damping_ratio",
            &WheelJoint::GetSpringDampingRatio,
            &WheelJoint::SetSpringDampingRatio,
            nb::arg("damping_ratio")
        )
        .def_prop_rw("limit_enabled", &WheelJoint::IsLimitEnabled, &WheelJoint::EnableLimit, nb::arg("enabled"))
        .def_prop_ro("lower_limit", &WheelJoint::GetLowerLimit)
        .def_prop_ro("upper_limit", &WheelJoint::GetUpperLimit)
        .def_prop_rw("motor_enabled", &WheelJoint::IsMotorEnabled, &WheelJoint::EnableMotor, nb::arg("enabled"))
        .def_prop_rw("motor_speed", &WheelJoint::GetMotorSpeed, &WheelJoint::SetMotorSpeed, nb::arg("speed"))
        .def_prop_rw(
            "max_motor_torque",
            &WheelJoint::GetMaxMotorTorque,
            &WheelJoint::SetMaxMotorTorque,
            nb::arg("torque")
        )
        .def_prop_ro("motor_torque", &WheelJoint::GetMotorTorque);

    // filter-joint
    nb::class_<FilterJoint, Joint>(m, "FilterJoint")
        .def(nb::init<uint64_t>(), nb::arg("joint_id"))
        .def_prop_rw(
            "user_data",
            [](FilterJoint& self) -> user_data_uint
            {
                return (user_data_uint) b2Joint_GetUserData(self.id);
            },
            [](FilterJoint& self, user_data_uint user_data)
            {
                b2Joint_SetUserData(self.id, (void*) user_data);
            },
            nb::arg("user_data")
        );
}

// Export all Box2D related functions
void export_box2d_functions(nb::module_& m)
{
    export_world_class(m);
    export_body_class(m);
    export_shape_class(m);
    export_chain_class(m);
    export_joint_classes(m);
}
