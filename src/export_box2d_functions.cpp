#include <nanobind/nanobind.h>
#include <pyb2d/py_converter.hpp>

#include "py_debug_draw.hpp"

// C
extern "C"
{
#include <box2d/box2d.h>
#include <box2d/math_functions.h>
}

// nanobind namespace
namespace nb = nanobind;

void export_world_functions(nb::module_& m)
{
    m.def("create_world", &b2CreateWorld, nb::arg("world_def"));
    m.def("destroy_world", &b2DestroyWorld, nb::arg("world_id"));
    m.def("world_is_valid", &b2World_IsValid, nb::arg("id"));
    m.def("world_step", &b2World_Step, nb::arg("world_id"), nb::arg("time_step"), nb::arg("sub_step_count"));
    m.def(
        "world_draw",
        [](b2WorldId world_id, PyDebugDraw* py_draw)
        {
            b2DebugDraw* draw = static_cast<b2DebugDraw*>(py_draw);
            b2World_Draw(world_id, draw);
        },
        nb::arg("world_id"),
        nb::arg("draw")
    );
    m.def("world_get_body_events", &b2World_GetBodyEvents, nb::arg("world_id"));
    m.def("world_get_sensor_events", &b2World_GetSensorEvents, nb::arg("world_id"));
    m.def("world_get_contact_events", &b2World_GetContactEvents, nb::arg("world_id"));
    m.def(
        "world_overlap_aabb",
        &b2World_OverlapAABB,
        nb::arg("world_id"),
        nb::arg("aabb"),
        nb::arg("filter"),
        nb::arg("fcn"),
        nb::arg("context")
    );
    m.def(
        "world_overlap_point",
        &b2World_OverlapPoint,
        nb::arg("world_id"),
        nb::arg("point"),
        nb::arg("transform"),
        nb::arg("filter"),
        nb::arg("fcn"),
        nb::arg("context")
    );
    m.def(
        "world_overlap_circle",
        &b2World_OverlapCircle,
        nb::arg("world_id"),
        nb::arg("circle"),
        nb::arg("transform"),
        nb::arg("filter"),
        nb::arg("fcn"),
        nb::arg("context")
    );
    m.def(
        "world_overlap_capsule",
        &b2World_OverlapCapsule,
        nb::arg("world_id"),
        nb::arg("capsule"),
        nb::arg("transform"),
        nb::arg("filter"),
        nb::arg("fcn"),
        nb::arg("context")
    );
    m.def(
        "world_cast_ray",
        &b2World_CastRay,
        nb::arg("world_id"),
        nb::arg("origin"),
        nb::arg("translation"),
        nb::arg("filter"),
        nb::arg("fcn"),
        nb::arg("context")
    );
    m.def(
        "world_cast_ray_closest",
        &b2World_CastRayClosest,
        nb::arg("world_id"),
        nb::arg("origin"),
        nb::arg("translation"),
        nb::arg("filter")
    );
    m.def(
        "world_cast_circle",
        &b2World_CastCircle,
        nb::arg("world_id"),
        nb::arg("circle"),
        nb::arg("origin_transform"),
        nb::arg("translation"),
        nb::arg("filter"),
        nb::arg("fcn"),
        nb::arg("context")
    );
    m.def(
        "world_cast_capsule",
        &b2World_CastCapsule,
        nb::arg("world_id"),
        nb::arg("capsule"),
        nb::arg("origin_transform"),
        nb::arg("translation"),
        nb::arg("filter"),
        nb::arg("fcn"),
        nb::arg("context")
    );
    m.def(
        "world_cast_polygon",
        &b2World_CastPolygon,
        nb::arg("world_id"),
        nb::arg("polygon"),
        nb::arg("origin_transform"),
        nb::arg("translation"),
        nb::arg("filter"),
        nb::arg("fcn"),
        nb::arg("context")
    );
    m.def("world_enable_sleeping", &b2World_EnableSleeping, nb::arg("world_id"), nb::arg("flag"));
    m.def("world_is_sleeping_enabled", &b2World_IsSleepingEnabled, nb::arg("world_id"));
    m.def("world_enable_continuous", &b2World_EnableContinuous, nb::arg("world_id"), nb::arg("flag"));
    m.def("world_is_continuous_enabled", &b2World_IsContinuousEnabled, nb::arg("world_id"));
    m.def(
        "world_set_restitution_threshold",
        &b2World_SetRestitutionThreshold,
        nb::arg("world_id"),
        nb::arg("value")
    );
    m.def("world_get_restitution_threshold", &b2World_GetRestitutionThreshold, nb::arg("world_id"));
    m.def("world_set_hit_event_threshold", &b2World_SetHitEventThreshold, nb::arg("world_id"), nb::arg("value"));
    m.def("world_get_hit_event_threshold", &b2World_GetHitEventThreshold, nb::arg("world_id"));
    // m.def("world_set_custom_filter_callback",
    // &b2World_SetCustomFilterCallback,nb::arg("world_id"),nb::arg("fcn"),nb::arg("context"));
    // m.def("world_set_pre_solve_callback",
    // &b2World_SetPreSolveCallback,nb::arg("world_id"),nb::arg("fcn"),nb::arg("context"));
    m.def("world_set_gravity", &b2World_SetGravity, nb::arg("world_id"), nb::arg("gravity"));
    m.def("world_get_gravity", &b2World_GetGravity, nb::arg("world_id"));
    m.def("world_explode", &b2World_Explode, nb::arg("world_id"), nb::arg("explosion_def"));
    m.def(
        "world_set_contact_tuning",
        &b2World_SetContactTuning,
        nb::arg("world_id"),
        nb::arg("hertz"),
        nb::arg("damping_ratio"),
        nb::arg("push_velocity")
    );
    m.def(
        "world_set_joint_tuning",
        &b2World_SetJointTuning,
        nb::arg("world_id"),
        nb::arg("hertz"),
        nb::arg("damping_ratio")
    );
    // m.def("world_set_maximum_linear_velocity",
    // &b2World_SetMaximumLinearVelocity,nb::arg("world_id"),nb::arg("maximum_linear_velocity"));
    // m.def("world_get_maximum_linear_velocity", &b2World_GetMaximumLinearVelocity,nb::arg("world_id"));
    m.def("world_enable_warm_starting", &b2World_EnableWarmStarting, nb::arg("world_id"), nb::arg("flag"));
    m.def("world_is_warm_starting_enabled", &b2World_IsWarmStartingEnabled, nb::arg("world_id"));
    m.def("world_get_profile", &b2World_GetProfile, nb::arg("world_id"));
    m.def("world_get_counters", &b2World_GetCounters, nb::arg("world_id"));
    m.def(
        "world_set_user_data",
        [](b2WorldId world_id, user_data_uint user_data)
        {
            b2World_SetUserData(world_id, (void*) user_data);
        },
        nb::arg("world_id"),
        nb::arg("user_data")
    );
    m.def(
        "world_get_user_data",
        [](b2WorldId world_id)
        {
            return (user_data_uint) b2World_GetUserData(world_id);
        },
        nb::arg("world_id")
    );
    m.def("world_dump_memory_stats", &b2World_DumpMemoryStats, nb::arg("world_id"));
    m.def("world_rebuild_static_tree", &b2World_RebuildStaticTree, nb::arg("world_id"));
    m.def("world_enable_speculative", &b2World_EnableSpeculative, nb::arg("world_id"), nb::arg("flag"));
}

void export_body_functions(nb::module_& m)
{
    m.def("create_body_from_def", &b2CreateBody, nb::arg("world_id"), nb::arg("def"));
    m.def("destroy_body", &b2DestroyBody, nb::arg("body_id"));
    m.def("body_is_valid", &b2Body_IsValid, nb::arg("id"));
    m.def("body_get_type", &b2Body_GetType, nb::arg("body_id"));
    m.def("body_set_type", &b2Body_SetType, nb::arg("body_id"), nb::arg("type"));
    m.def("body_get_position", &b2Body_GetPosition, nb::arg("body_id"));
    m.def("body_get_rotation", &b2Body_GetRotation, nb::arg("body_id"));
    m.def("body_get_transform", &b2Body_GetTransform, nb::arg("body_id"));
    m.def("body_set_transform", &b2Body_SetTransform, nb::arg("body_id"), nb::arg("position"), nb::arg("rotation"));
    m.def("body_get_local_point", &b2Body_GetLocalPoint, nb::arg("body_id"), nb::arg("world_point"));
    m.def("body_get_world_point", &b2Body_GetWorldPoint, nb::arg("body_id"), nb::arg("local_point"));


    m.def("body_get_local_vector", &b2Body_GetLocalVector, nb::arg("body_id"), nb::arg("world_vector"));
    m.def("body_get_world_vector", &b2Body_GetWorldVector, nb::arg("body_id"), nb::arg("local_vector"));
    m.def("body_get_linear_velocity", &b2Body_GetLinearVelocity, nb::arg("body_id"));
    m.def("body_get_angular_velocity", &b2Body_GetAngularVelocity, nb::arg("body_id"));
    m.def("body_set_linear_velocity", &b2Body_SetLinearVelocity, nb::arg("body_id"), nb::arg("linear_velocity"));
    m.def("body_set_angular_velocity", &b2Body_SetAngularVelocity, nb::arg("body_id"), nb::arg("angular_velocity"));
    m.def(
        "body_apply_force",
        &b2Body_ApplyForce,
        nb::arg("body_id"),
        nb::arg("force"),
        nb::arg("point"),
        nb::arg("wake")
    );
    m.def(
        "body_apply_force_to_center",
        &b2Body_ApplyForceToCenter,
        nb::arg("body_id"),
        nb::arg("force"),
        nb::arg("wake")
    );
    m.def("body_apply_torque", &b2Body_ApplyTorque, nb::arg("body_id"), nb::arg("torque"), nb::arg("wake"));
    m.def(
        "body_apply_linear_impulse",
        &b2Body_ApplyLinearImpulse,
        nb::arg("body_id"),
        nb::arg("impulse"),
        nb::arg("point"),
        nb::arg("wake")
    );
    m.def(
        "body_apply_linear_impulse_to_center",
        &b2Body_ApplyLinearImpulseToCenter,
        nb::arg("body_id"),
        nb::arg("impulse"),
        nb::arg("wake")
    );
    m.def(
        "body_apply_angular_impulse",
        &b2Body_ApplyAngularImpulse,
        nb::arg("body_id"),
        nb::arg("impulse"),
        nb::arg("wake")
    );
    m.def("body_get_mass", &b2Body_GetMass, nb::arg("body_id"));
    m.def("body_get_rotational_inertia", &b2Body_GetRotationalInertia, nb::arg("body_id"));
    m.def("body_get_local_center_of_mass", &b2Body_GetLocalCenterOfMass, nb::arg("body_id"));
    m.def("body_get_world_center_of_mass", &b2Body_GetWorldCenterOfMass, nb::arg("body_id"));
    m.def("body_set_mass_data", &b2Body_SetMassData, nb::arg("body_id"), nb::arg("mass_data"));
    m.def("body_get_mass_data", &b2Body_GetMassData, nb::arg("body_id"));
    m.def("body_apply_mass_from_shapes", &b2Body_ApplyMassFromShapes, nb::arg("body_id"));
    m.def("body_set_linear_damping", &b2Body_SetLinearDamping, nb::arg("body_id"), nb::arg("linear_damping"));
    m.def("body_get_linear_damping", &b2Body_GetLinearDamping, nb::arg("body_id"));
    m.def("body_set_angular_damping", &b2Body_SetAngularDamping, nb::arg("body_id"), nb::arg("angular_damping"));
    m.def("body_get_angular_damping", &b2Body_GetAngularDamping, nb::arg("body_id"));
    m.def("body_set_gravity_scale", &b2Body_SetGravityScale, nb::arg("body_id"), nb::arg("gravity_scale"));
    m.def("body_get_gravity_scale", &b2Body_GetGravityScale, nb::arg("body_id"));
    m.def("body_is_awake", &b2Body_IsAwake, nb::arg("body_id"));
    m.def("body_set_awake", &b2Body_SetAwake, nb::arg("body_id"), nb::arg("awake"));
    m.def("body_enable_sleep", &b2Body_EnableSleep, nb::arg("body_id"), nb::arg("enable_sleep"));
    m.def("body_is_sleep_enabled", &b2Body_IsSleepEnabled, nb::arg("body_id"));
    m.def("body_set_sleep_threshold", &b2Body_SetSleepThreshold, nb::arg("body_id"), nb::arg("sleep_threshold"));
    m.def("body_get_sleep_threshold", &b2Body_GetSleepThreshold, nb::arg("body_id"));
    m.def("body_is_enabled", &b2Body_IsEnabled, nb::arg("body_id"));
    m.def("body_disable", &b2Body_Disable, nb::arg("body_id"));
    m.def("body_enable", &b2Body_Enable, nb::arg("body_id"));
    m.def("body_set_fixed_rotation", &b2Body_SetFixedRotation, nb::arg("body_id"), nb::arg("flag"));
    m.def("body_is_fixed_rotation", &b2Body_IsFixedRotation, nb::arg("body_id"));
    m.def("body_set_bullet", &b2Body_SetBullet, nb::arg("body_id"), nb::arg("flag"));
    m.def("body_is_bullet", &b2Body_IsBullet, nb::arg("body_id"));
    m.def("enable_hit_events", &b2Body_EnableHitEvents, nb::arg("body_id"), nb::arg("enable_hit_events"));
    m.def("get_world", &b2Body_GetWorld, nb::arg("body_id"));
    m.def("get_shape_count", &b2Body_GetShapeCount, nb::arg("body_id"));
    m.def("get_shapes", &b2Body_GetShapes, nb::arg("body_id"), nb::arg("shape_array"), nb::arg("capacity"));
    m.def("get_joint_count", &b2Body_GetJointCount, nb::arg("body_id"));
    m.def("get_joints", &b2Body_GetJoints, nb::arg("body_id"), nb::arg("joint_array"), nb::arg("capacity"));
    m.def("get_contact_capacity", &b2Body_GetContactCapacity, nb::arg("body_id"));
    m.def(
        "get_contact_data",
        &b2Body_GetContactData,
        nb::arg("body_id"),
        nb::arg("contact_data"),
        nb::arg("capacity")
    );
    m.def("compute_aabb", &b2Body_ComputeAABB, nb::arg("body_id"));
    // get and set user data
    m.def(
        "body_set_user_data",
        [](b2BodyId body_id, user_data_uint user_data)
        {
            b2Body_SetUserData(body_id, (void*) user_data);
        },
        nb::arg("body_id"),
        nb::arg("user_data")
    );
    m.def(
        "body_get_user_data",
        [](b2BodyId body_id)
        {
            return (user_data_uint) b2Body_GetUserData(body_id);
        },
        nb::arg("body_id")
    );
}

void export_shape_functions(nb::module_& m)
{
    m.def("create_circle_shape", &b2CreateCircleShape, nb::arg("body_id"), nb::arg("def"), nb::arg("circle"));
    m.def("create_segment_shape", &b2CreateSegmentShape, nb::arg("body_id"), nb::arg("def"), nb::arg("segment"));
    m.def("create_capsule_shape", &b2CreateCapsuleShape, nb::arg("body_id"), nb::arg("def"), nb::arg("capsule"));
    m.def("create_polygon_shape", &b2CreatePolygonShape, nb::arg("body_id"), nb::arg("def"), nb::arg("polygon"));
    m.def("destroy_shape", &b2DestroyShape, nb::arg("shape_id"), nb::arg("update_body_mass"));
    m.def("shape_is_valid", &b2Shape_IsValid, nb::arg("id"));
    m.def("shape_get_type", &b2Shape_GetType, nb::arg("shape_id"));
    m.def("shape_get_body", &b2Shape_GetBody, nb::arg("shape_id"));
    m.def("shape_get_world", &b2Shape_GetWorld, nb::arg("shape_id"));
    m.def("shape_is_sensor", &b2Shape_IsSensor, nb::arg("shape_id"));
    m.def(
        "shape_set_density",
        &b2Shape_SetDensity,
        nb::arg("shape_id"),
        nb::arg("density"),
        nb::arg("update_body_mass")
    );
    m.def("shape_get_density", &b2Shape_GetDensity, nb::arg("shape_id"));
    m.def("shape_set_friction", &b2Shape_SetFriction, nb::arg("shape_id"), nb::arg("friction"));
    m.def("shape_get_friction", &b2Shape_GetFriction, nb::arg("shape_id"));
    m.def("shape_set_restitution", &b2Shape_SetRestitution, nb::arg("shape_id"), nb::arg("restitution"));
    m.def("shape_get_restitution", &b2Shape_GetRestitution, nb::arg("shape_id"));
    m.def("shape_get_filter", &b2Shape_GetFilter, nb::arg("shape_id"));
    m.def("shape_set_filter", &b2Shape_SetFilter, nb::arg("shape_id"), nb::arg("filter"));
    m.def("shape_enable_sensor_events", &b2Shape_EnableSensorEvents, nb::arg("shape_id"), nb::arg("flag"));
    m.def("shape_are_sensor_events_enabled", &b2Shape_AreSensorEventsEnabled, nb::arg("shape_id"));
    m.def("shape_enable_contact_events", &b2Shape_EnableContactEvents, nb::arg("shape_id"), nb::arg("flag"));
    m.def("shape_are_contact_events_enabled", &b2Shape_AreContactEventsEnabled, nb::arg("shape_id"));
    m.def("shape_enable_pre_solve_events", &b2Shape_EnablePreSolveEvents, nb::arg("shape_id"), nb::arg("flag"));
    m.def("shape_are_pre_solve_events_enabled", &b2Shape_ArePreSolveEventsEnabled, nb::arg("shape_id"));
    m.def("shape_enable_hit_events", &b2Shape_EnableHitEvents, nb::arg("shape_id"), nb::arg("flag"));
    m.def("shape_are_hit_events_enabled", &b2Shape_AreHitEventsEnabled, nb::arg("shape_id"));
    m.def("shape_test_point", &b2Shape_TestPoint, nb::arg("shape_id"), nb::arg("point"));
    m.def("shape_ray_cast", &b2Shape_RayCast, nb::arg("shape_id"), nb::arg("input"));
    m.def("shape_get_circle", &b2Shape_GetCircle, nb::arg("shape_id"));
    m.def("shape_get_segment", &b2Shape_GetSegment, nb::arg("shape_id"));
    m.def("shape_get_chain_segment", &b2Shape_GetChainSegment, nb::arg("shape_id"));
    m.def("shape_get_capsule", &b2Shape_GetCapsule, nb::arg("shape_id"));
    m.def("shape_get_polygon", &b2Shape_GetPolygon, nb::arg("shape_id"));
    m.def("shape_set_circle", &b2Shape_SetCircle, nb::arg("shape_id"), nb::arg("circle"));
    m.def("shape_set_capsule", &b2Shape_SetCapsule, nb::arg("shape_id"), nb::arg("capsule"));
    m.def("shape_set_segment", &b2Shape_SetSegment, nb::arg("shape_id"), nb::arg("segment"));
    m.def("shape_set_polygon", &b2Shape_SetPolygon, nb::arg("shape_id"), nb::arg("polygon"));
    m.def("shape_get_parent_chain", &b2Shape_GetParentChain, nb::arg("shape_id"));
    m.def("shape_get_contact_capacity", &b2Shape_GetContactCapacity, nb::arg("shape_id"));
    m.def(
        "shape_get_contact_data",
        &b2Shape_GetContactData,
        nb::arg("shape_id"),
        nb::arg("contact_data"),
        nb::arg("capacity")
    );
    m.def("shape_get_aabb", &b2Shape_GetAABB, nb::arg("shape_id"));
    m.def("shape_get_closest_point", &b2Shape_GetClosestPoint, nb::arg("shape_id"), nb::arg("target"));
    m.def(
        "shape_set_user_data",
        [](b2ShapeId shape_id, user_data_uint user_data)
        {
            b2Shape_SetUserData(shape_id, (void*) user_data);
        },
        nb::arg("shape_id"),
        nb::arg("user_data")
    );
    m.def(
        "shape_get_user_data",
        [](b2ShapeId shape_id)
        {
            return (user_data_uint) b2Shape_GetUserData(shape_id);
        },
        nb::arg("shape_id")
    );
}

void export_chain_functions(nb::module_& m)
{
    m.def("create_chain", &b2CreateChain, nb::arg("body_id"), nb::arg("def"));
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

void export_null_joint_functions(nb::module_& m)
{
    m.def("create_null_joint", &b2CreateNullJoint, nb::arg("world_id"), nb::arg("def"));
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
    export_null_joint_functions(m);
    export_prismatic_joint_functions(m);
    export_revolute_joint_functions(m);
    export_weld_joint_functions(m);
    export_wheel_joint_functions(m);
}

void export_box2d_functions(nb::module_& m)
{
    export_world_functions(m);
    export_body_functions(m);
    export_shape_functions(m);
    export_chain_functions(m);
    export_joint_functions(m);
}
