#include <nanobind/nanobind.h>

// C
extern "C" {
#include <box2d/math_functions.h>
#include <box2d/box2d.h>
}

// nanobind namespace
namespace py = nanobind;


void export_world_functions(py::module_ & m)
{
    m.def("create_world", &b2CreateWorld,py::arg("def"));
    m.def("destroy_world", &b2DestroyWorld,py::arg("world_id"));
    m.def("world_is_valid", &b2World_IsValid,py::arg("id"));
    m.def("world_step", &b2World_Step,py::arg("world_id"),py::arg("time_step"),py::arg("sub_step_count"));
    m.def("world_draw", &b2World_Draw,py::arg("world_id"),py::arg("draw"));
    m.def("world_get_body_events", &b2World_GetBodyEvents,py::arg("world_id"));
    m.def("world_get_sensor_events", &b2World_GetSensorEvents,py::arg("world_id"));
    m.def("world_get_contact_events", &b2World_GetContactEvents,py::arg("world_id"));
    m.def("world_overlap_aabb", &b2World_OverlapAABB,py::arg("world_id"),py::arg("aabb"),py::arg("filter"),py::arg("fcn"),py::arg("context"));
    m.def("world_overlap_point", &b2World_OverlapPoint,py::arg("world_id"),py::arg("point"),py::arg("transform"),py::arg("filter"),py::arg("fcn"),py::arg("context"));
    m.def("world_overlap_circle", &b2World_OverlapCircle,py::arg("world_id"),py::arg("circle"),py::arg("transform"),py::arg("filter"),py::arg("fcn"),py::arg("context"));
    m.def("world_overlap_capsule", &b2World_OverlapCapsule,py::arg("world_id"),py::arg("capsule"),py::arg("transform"),py::arg("filter"),py::arg("fcn"),py::arg("context"));
    m.def("world_cast_ray", &b2World_CastRay,py::arg("world_id"),py::arg("origin"),py::arg("translation"),py::arg("filter"),py::arg("fcn"),py::arg("context"));
    m.def("world_cast_ray_closest", &b2World_CastRayClosest,py::arg("world_id"),py::arg("origin"),py::arg("translation"),py::arg("filter"));
    m.def("world_cast_circle", &b2World_CastCircle,py::arg("world_id"),py::arg("circle"),py::arg("origin_transform"),py::arg("translation"),py::arg("filter"),py::arg("fcn"),py::arg("context"));
    m.def("world_cast_capsule", &b2World_CastCapsule,py::arg("world_id"),py::arg("capsule"),py::arg("origin_transform"),py::arg("translation"),py::arg("filter"),py::arg("fcn"),py::arg("context"));
    m.def("world_cast_polygon", &b2World_CastPolygon,py::arg("world_id"),py::arg("polygon"),py::arg("origin_transform"),py::arg("translation"),py::arg("filter"),py::arg("fcn"),py::arg("context"));
    m.def("world_enable_sleeping", &b2World_EnableSleeping,py::arg("world_id"),py::arg("flag"));
    m.def("world_is_sleeping_enabled", &b2World_IsSleepingEnabled,py::arg("world_id"));
    m.def("world_enable_continuous", &b2World_EnableContinuous,py::arg("world_id"),py::arg("flag"));
    m.def("world_is_continuous_enabled", &b2World_IsContinuousEnabled,py::arg("world_id"));
    m.def("world_set_restitution_threshold", &b2World_SetRestitutionThreshold,py::arg("world_id"),py::arg("value"));
    m.def("world_get_restitution_threshold", &b2World_GetRestitutionThreshold,py::arg("world_id"));
    m.def("world_set_hit_event_threshold", &b2World_SetHitEventThreshold,py::arg("world_id"),py::arg("value"));
    m.def("world_get_hit_event_threshold", &b2World_GetHitEventThreshold,py::arg("world_id"));
    // m.def("world_set_custom_filter_callback", &b2World_SetCustomFilterCallback,py::arg("world_id"),py::arg("fcn"),py::arg("context"));
    // m.def("world_set_pre_solve_callback", &b2World_SetPreSolveCallback,py::arg("world_id"),py::arg("fcn"),py::arg("context"));
    m.def("world_set_gravity", &b2World_SetGravity,py::arg("world_id"),py::arg("gravity"));
    m.def("world_get_gravity", &b2World_GetGravity,py::arg("world_id"));
    m.def("world_explode", &b2World_Explode,py::arg("world_id"),py::arg("explosion_def"));
    m.def("world_set_contact_tuning", &b2World_SetContactTuning,py::arg("world_id"),py::arg("hertz"),py::arg("damping_ratio"),py::arg("push_velocity"));
    m.def("world_set_joint_tuning", &b2World_SetJointTuning,py::arg("world_id"),py::arg("hertz"),py::arg("damping_ratio"));
    m.def("world_set_maximum_linear_velocity", &b2World_SetMaximumLinearVelocity,py::arg("world_id"),py::arg("maximum_linear_velocity"));
    m.def("world_get_maximum_linear_velocity", &b2World_GetMaximumLinearVelocity,py::arg("world_id"));
    m.def("world_enable_warm_starting", &b2World_EnableWarmStarting,py::arg("world_id"),py::arg("flag"));
    m.def("world_is_warm_starting_enabled", &b2World_IsWarmStartingEnabled,py::arg("world_id"));
    m.def("world_get_profile", &b2World_GetProfile,py::arg("world_id"));
    m.def("world_get_counters", &b2World_GetCounters,py::arg("world_id"));
    //m.def("world_set_user_data", &b2World_SetUserData,py::arg("world_id"),py::arg("user_data"));
    //m.def("world_get_user_data", &b2World_GetUserData,py::arg("world_id"));
    m.def("world_dump_memory_stats", &b2World_DumpMemoryStats,py::arg("world_id"));
    m.def("world_rebuild_static_tree", &b2World_RebuildStaticTree,py::arg("world_id"));
    m.def("world_enable_speculative", &b2World_EnableSpeculative,py::arg("world_id"),py::arg("flag"));

}




void export_body_functions(py::module_ & m)
{
    m.def("create_body", &b2CreateBody,py::arg("world_id"),py::arg("def"));
    m.def("destroy_body", &b2DestroyBody,py::arg("body_id"));
    m.def("body_is_valid", &b2Body_IsValid,py::arg("id"));
    m.def("body_get_type", &b2Body_GetType,py::arg("body_id"));
    m.def("body_set_type", &b2Body_SetType,py::arg("body_id"),py::arg("type"));
    m.def("body_set_user_data", &b2Body_SetUserData,py::arg("body_id"),py::arg("user_data"));
    m.def("body_get_user_data", &b2Body_GetUserData,py::arg("body_id"));
    m.def("body_get_position", &b2Body_GetPosition,py::arg("body_id"));
    m.def("body_get_rotation", &b2Body_GetRotation,py::arg("body_id"));
    m.def("body_get_transform", &b2Body_GetTransform,py::arg("body_id"));
    m.def("body_set_transform", &b2Body_SetTransform,py::arg("body_id"),py::arg("position"),py::arg("rotation"));
    m.def("body_get_local_point", &b2Body_GetLocalPoint,py::arg("body_id"),py::arg("world_point"));
    m.def("body_get_world_point", &b2Body_GetWorldPoint,py::arg("body_id"),py::arg("local_point"));
    m.def("body_get_local_vector", &b2Body_GetLocalVector,py::arg("body_id"),py::arg("world_vector"));
    m.def("body_get_world_vector", &b2Body_GetWorldVector,py::arg("body_id"),py::arg("local_vector"));
    m.def("body_get_linear_velocity", &b2Body_GetLinearVelocity,py::arg("body_id"));
    m.def("body_get_angular_velocity", &b2Body_GetAngularVelocity,py::arg("body_id"));
    m.def("body_set_linear_velocity", &b2Body_SetLinearVelocity,py::arg("body_id"),py::arg("linear_velocity"));
    m.def("body_set_angular_velocity", &b2Body_SetAngularVelocity,py::arg("body_id"),py::arg("angular_velocity"));
    m.def("body_apply_force", &b2Body_ApplyForce,py::arg("body_id"),py::arg("force"),py::arg("point"),py::arg("wake"));
    m.def("body_apply_force_to_center", &b2Body_ApplyForceToCenter,py::arg("body_id"),py::arg("force"),py::arg("wake"));
    m.def("body_apply_torque", &b2Body_ApplyTorque,py::arg("body_id"),py::arg("torque"),py::arg("wake"));
    m.def("body_apply_linear_impulse", &b2Body_ApplyLinearImpulse,py::arg("body_id"),py::arg("impulse"),py::arg("point"),py::arg("wake"));
    m.def("body_apply_linear_impulse_to_center", &b2Body_ApplyLinearImpulseToCenter,py::arg("body_id"),py::arg("impulse"),py::arg("wake"));
    m.def("body_apply_angular_impulse", &b2Body_ApplyAngularImpulse,py::arg("body_id"),py::arg("impulse"),py::arg("wake"));
    m.def("body_get_mass", &b2Body_GetMass,py::arg("body_id"));
    m.def("body_get_rotational_inertia", &b2Body_GetRotationalInertia,py::arg("body_id"));
    m.def("body_get_local_center_of_mass", &b2Body_GetLocalCenterOfMass,py::arg("body_id"));
    m.def("body_get_world_center_of_mass", &b2Body_GetWorldCenterOfMass,py::arg("body_id"));
    m.def("body_set_mass_data", &b2Body_SetMassData,py::arg("body_id"),py::arg("mass_data"));
    m.def("body_get_mass_data", &b2Body_GetMassData,py::arg("body_id"));


    m.def("body_apply_mass_from_shapes", &b2Body_ApplyMassFromShapes,py::arg("body_id"));
    m.def("body_set_linear_damping", &b2Body_SetLinearDamping,py::arg("body_id"),py::arg("linear_damping"));
    m.def("body_get_linear_damping", &b2Body_GetLinearDamping,py::arg("body_id"));
    m.def("body_set_angular_damping", &b2Body_SetAngularDamping,py::arg("body_id"),py::arg("angular_damping"));
    m.def("body_get_angular_damping", &b2Body_GetAngularDamping,py::arg("body_id"));
    m.def("body_set_gravity_scale", &b2Body_SetGravityScale,py::arg("body_id"),py::arg("gravity_scale"));
    m.def("body_get_gravity_scale", &b2Body_GetGravityScale,py::arg("body_id"));
    m.def("body_is_awake", &b2Body_IsAwake,py::arg("body_id"));
    m.def("body_set_awake", &b2Body_SetAwake,py::arg("body_id"),py::arg("awake"));
    m.def("body_enable_sleep", &b2Body_EnableSleep,py::arg("body_id"),py::arg("enable_sleep"));
    m.def("body_is_sleep_enabled", &b2Body_IsSleepEnabled,py::arg("body_id"));
    m.def("body_set_sleep_threshold", &b2Body_SetSleepThreshold,py::arg("body_id"),py::arg("sleep_threshold"));
    m.def("body_get_sleep_threshold", &b2Body_GetSleepThreshold,py::arg("body_id"));
    m.def("body_is_enabled", &b2Body_IsEnabled,py::arg("body_id"));
    m.def("body_disable", &b2Body_Disable,py::arg("body_id"));
    m.def("body_enable", &b2Body_Enable,py::arg("body_id"));
    m.def("body_set_fixed_rotation", &b2Body_SetFixedRotation,py::arg("body_id"),py::arg("flag"));
    m.def("body_is_fixed_rotation", &b2Body_IsFixedRotation,py::arg("body_id"));
    m.def("body_set_bullet", &b2Body_SetBullet,py::arg("body_id"),py::arg("flag"));
    m.def("body_is_bullet", &b2Body_IsBullet,py::arg("body_id"));
    

    m.def("enable_hit_events", &b2Body_EnableHitEvents,py::arg("body_id"),py::arg("enable_hit_events"));
    m.def("get_world", &b2Body_GetWorld,py::arg("body_id"));
    m.def("get_shape_count", &b2Body_GetShapeCount,py::arg("body_id"));
    m.def("get_shapes", &b2Body_GetShapes,py::arg("body_id"),py::arg("shape_array"),py::arg("capacity"));
    m.def("get_joint_count", &b2Body_GetJointCount,py::arg("body_id"));
    m.def("get_joints", &b2Body_GetJoints,py::arg("body_id"),py::arg("joint_array"),py::arg("capacity"));
    m.def("get_contact_capacity", &b2Body_GetContactCapacity,py::arg("body_id"));
    m.def("get_contact_data", &b2Body_GetContactData,py::arg("body_id"),py::arg("contact_data"),py::arg("capacity"));
    m.def("compute_aabb", &b2Body_ComputeAABB,py::arg("body_id"));



    
}



void export_shape_functions(py::module_ & m)
{
    m.def("create_circle_shape", &b2CreateCircleShape,py::arg("body_id"),py::arg("def"),py::arg("circle"));
    m.def("create_segment_shape", &b2CreateSegmentShape,py::arg("body_id"),py::arg("def"),py::arg("segment"));
    m.def("create_capsule_shape", &b2CreateCapsuleShape,py::arg("body_id"),py::arg("def"),py::arg("capsule"));
    m.def("create_polygon_shape", &b2CreatePolygonShape,py::arg("body_id"),py::arg("def"),py::arg("polygon"));
    m.def("destroy_shape", &b2DestroyShape,py::arg("shape_id"),py::arg("update_body_mass"));
    m.def("shape_is_valid", &b2Shape_IsValid,py::arg("id"));
    m.def("shape_get_type", &b2Shape_GetType,py::arg("shape_id"));
    m.def("shape_get_body", &b2Shape_GetBody,py::arg("shape_id"));
    m.def("shape_get_world", &b2Shape_GetWorld,py::arg("shape_id"));
    m.def("shape_is_sensor", &b2Shape_IsSensor,py::arg("shape_id"));
    m.def("shape_set_user_data", &b2Shape_SetUserData,py::arg("shape_id"),py::arg("user_data"));
    m.def("shape_get_user_data", &b2Shape_GetUserData,py::arg("shape_id"));
    m.def("shape_set_density", &b2Shape_SetDensity,py::arg("shape_id"),py::arg("density"),py::arg("update_body_mass"));
    m.def("shape_get_density", &b2Shape_GetDensity,py::arg("shape_id"));
    m.def("shape_set_friction", &b2Shape_SetFriction,py::arg("shape_id"),py::arg("friction"));
    m.def("shape_get_friction", &b2Shape_GetFriction,py::arg("shape_id"));
    m.def("shape_set_restitution", &b2Shape_SetRestitution,py::arg("shape_id"),py::arg("restitution"));
    m.def("shape_get_restitution", &b2Shape_GetRestitution,py::arg("shape_id"));
    m.def("shape_get_filter", &b2Shape_GetFilter,py::arg("shape_id"));
    m.def("shape_set_filter", &b2Shape_SetFilter,py::arg("shape_id"),py::arg("filter"));
    m.def("shape_enable_sensor_events", &b2Shape_EnableSensorEvents,py::arg("shape_id"),py::arg("flag"));
    m.def("shape_are_sensor_events_enabled", &b2Shape_AreSensorEventsEnabled,py::arg("shape_id"));
    m.def("shape_enable_contact_events", &b2Shape_EnableContactEvents,py::arg("shape_id"),py::arg("flag"));
    m.def("shape_are_contact_events_enabled", &b2Shape_AreContactEventsEnabled,py::arg("shape_id"));
    m.def("shape_enable_pre_solve_events", &b2Shape_EnablePreSolveEvents,py::arg("shape_id"),py::arg("flag"));
    m.def("shape_are_pre_solve_events_enabled", &b2Shape_ArePreSolveEventsEnabled,py::arg("shape_id"));
    m.def("shape_enable_hit_events", &b2Shape_EnableHitEvents,py::arg("shape_id"),py::arg("flag"));
    m.def("shape_are_hit_events_enabled", &b2Shape_AreHitEventsEnabled,py::arg("shape_id"));


    m.def("shape_test_point", &b2Shape_TestPoint,py::arg("shape_id"),py::arg("point"));
    m.def("shape_ray_cast", &b2Shape_RayCast,py::arg("shape_id"),py::arg("input"));
    m.def("shape_get_circle", &b2Shape_GetCircle,py::arg("shape_id"));
    m.def("shape_get_segment", &b2Shape_GetSegment,py::arg("shape_id"));
    m.def("shape_get_chain_segment", &b2Shape_GetChainSegment,py::arg("shape_id"));
    m.def("shape_get_capsule", &b2Shape_GetCapsule,py::arg("shape_id"));
    m.def("shape_get_polygon", &b2Shape_GetPolygon,py::arg("shape_id"));
    m.def("shape_set_circle", &b2Shape_SetCircle,py::arg("shape_id"),py::arg("circle"));
    m.def("shape_set_capsule", &b2Shape_SetCapsule,py::arg("shape_id"),py::arg("capsule"));
    m.def("shape_set_segment", &b2Shape_SetSegment,py::arg("shape_id"),py::arg("segment"));
    m.def("shape_set_polygon", &b2Shape_SetPolygon,py::arg("shape_id"),py::arg("polygon"));
    m.def("shape_get_parent_chain", &b2Shape_GetParentChain,py::arg("shape_id"));
    m.def("shape_get_contact_capacity", &b2Shape_GetContactCapacity,py::arg("shape_id"));
    m.def("shape_get_contact_data", &b2Shape_GetContactData,py::arg("shape_id"),py::arg("contact_data"),py::arg("capacity"));
    m.def("shape_get_aabb", &b2Shape_GetAABB,py::arg("shape_id"));
    m.def("shape_get_closest_point", &b2Shape_GetClosestPoint,py::arg("shape_id"),py::arg("target"));
}

void export_chain_functions(py::module_ & m){
    m.def("create_chain", &b2CreateChain,py::arg("body_id"),py::arg("def"));
    m.def("destroy_chain", &b2DestroyChain,py::arg("chain_id"));
    m.def("chain_get_world", &b2Chain_GetWorld,py::arg("chain_id"));
    m.def("chain_get_segment_count", &b2Chain_GetSegmentCount,py::arg("chain_id"));
    m.def("chain_get_segments", &b2Chain_GetSegments,py::arg("chain_id"),py::arg("segment_array"),py::arg("capacity"));
    m.def("chain_set_friction", &b2Chain_SetFriction,py::arg("chain_id"),py::arg("friction"));
    m.def("chain_get_friction", &b2Chain_GetFriction,py::arg("chain_id"));
    m.def("chain_set_restitution", &b2Chain_SetRestitution,py::arg("chain_id"),py::arg("restitution"));
    m.def("chain_get_restitution", &b2Chain_GetRestitution,py::arg("chain_id"));
    m.def("chain_is_valid", &b2Chain_IsValid,py::arg("id"));
}



// /** @} */

// /**
//  * @defgroup joint Joint
//  * @brief Joints allow you to connect rigid bodies together while allowing various forms of relative motions.
//  * @{
//  */

// /// Destroy a joint
// B2_API void b2DestroyJoint( b2JointId jointId );

// /// Joint identifier validation. Provides validation for up to 64K allocations.
// B2_API bool b2Joint_IsValid( b2JointId id );

// /// Get the joint type
// B2_API b2JointType b2Joint_GetType( b2JointId jointId );

// /// Get body A id on a joint
// B2_API b2BodyId b2Joint_GetBodyA( b2JointId jointId );

// /// Get body B id on a joint
// B2_API b2BodyId b2Joint_GetBodyB( b2JointId jointId );

// /// Get the world that owns this joint
// B2_API b2WorldId b2Joint_GetWorld( b2JointId jointId );

// /// Get the local anchor on bodyA
// B2_API b2Vec2 b2Joint_GetLocalAnchorA( b2JointId jointId );

// /// Get the local anchor on bodyB
// B2_API b2Vec2 b2Joint_GetLocalAnchorB( b2JointId jointId );

// /// Toggle collision between connected bodies
// B2_API void b2Joint_SetCollideConnected( b2JointId jointId, bool shouldCollide );

// /// Is collision allowed between connected bodies?
// B2_API bool b2Joint_GetCollideConnected( b2JointId jointId );

// /// Set the user data on a joint
// B2_API void b2Joint_SetUserData( b2JointId jointId, void* userData );

// /// Get the user data on a joint
// B2_API void* b2Joint_GetUserData( b2JointId jointId );

// /// Wake the bodies connect to this joint
// B2_API void b2Joint_WakeBodies( b2JointId jointId );

// /// Get the current constraint force for this joint
// B2_API b2Vec2 b2Joint_GetConstraintForce( b2JointId jointId );

// /// Get the current constraint torque for this joint
// B2_API float b2Joint_GetConstraintTorque( b2JointId jointId );


void export_joint_functions_generic(py::module_ & m)
{
    m.def("destroy_joint", &b2DestroyJoint,py::arg("joint_id"));
    m.def("joint_is_valid", &b2Joint_IsValid,py::arg("id"));
    m.def("joint_get_type", &b2Joint_GetType,py::arg("joint_id"));
    m.def("joint_get_body_a", &b2Joint_GetBodyA,py::arg("joint_id"));
    m.def("joint_get_body_b", &b2Joint_GetBodyB,py::arg("joint_id"));
    m.def("joint_get_world", &b2Joint_GetWorld,py::arg("joint_id"));
    m.def("joint_get_local_anchor_a", &b2Joint_GetLocalAnchorA,py::arg("joint_id"));
    m.def("joint_get_local_anchor_b", &b2Joint_GetLocalAnchorB,py::arg("joint_id"));
    m.def("joint_set_collide_connected", &b2Joint_SetCollideConnected,py::arg("joint_id"),py::arg("should_collide"));
    m.def("joint_get_collide_connected", &b2Joint_GetCollideConnected,py::arg("joint_id"));
    m.def("joint_set_user_data", &b2Joint_SetUserData,py::arg("joint_id"),py::arg("user_data"));
    m.def("joint_get_user_data", &b2Joint_GetUserData,py::arg("joint_id"));
    m.def("joint_wake_bodies", &b2Joint_WakeBodies,py::arg("joint_id"));
    m.def("joint_get_constraint_force", &b2Joint_GetConstraintForce,py::arg("joint_id"));
    m.def("joint_get_constraint_torque", &b2Joint_GetConstraintTorque,py::arg("joint_id"));
}



void export_distance_joint_functions(py::module_ & m){

    m.def("create_distance_joint", &b2CreateDistanceJoint,py::arg("world_id"),py::arg("def"));
    m.def("distance_joint_set_length", &b2DistanceJoint_SetLength,py::arg("joint_id"),py::arg("length"));
    m.def("distance_joint_get_length", &b2DistanceJoint_GetLength,py::arg("joint_id"));
    m.def("distance_joint_enable_spring", &b2DistanceJoint_EnableSpring,py::arg("joint_id"),py::arg("enable_spring"));
    m.def("distance_joint_is_spring_enabled", &b2DistanceJoint_IsSpringEnabled,py::arg("joint_id"));
    m.def("distance_joint_set_spring_hertz", &b2DistanceJoint_SetSpringHertz,py::arg("joint_id"),py::arg("hertz"));
    m.def("distance_joint_get_spring_hertz", &b2DistanceJoint_GetSpringHertz,py::arg("joint_id"));
    m.def("distance_joint_set_spring_damping_ratio", &b2DistanceJoint_SetSpringDampingRatio,py::arg("joint_id"),py::arg("damping_ratio"));
    m.def("distance_joint_get_spring_damping_ratio", &b2DistanceJoint_GetSpringDampingRatio,py::arg("joint_id"));
    m.def("distance_joint_enable_limit", &b2DistanceJoint_EnableLimit,py::arg("joint_id"),py::arg("enable_limit"));
    m.def("distance_joint_is_limit_enabled", &b2DistanceJoint_IsLimitEnabled,py::arg("joint_id"));
    m.def("distance_joint_set_length_range", &b2DistanceJoint_SetLengthRange,py::arg("joint_id"),py::arg("min_length"),py::arg("max_length"));
    m.def("distance_joint_get_min_length", &b2DistanceJoint_GetMinLength,py::arg("joint_id"));
    m.def("distance_joint_get_max_length", &b2DistanceJoint_GetMaxLength,py::arg("joint_id"));
    m.def("distance_joint_get_current_length", &b2DistanceJoint_GetCurrentLength,py::arg("joint_id"));
    m.def("distance_joint_enable_motor", &b2DistanceJoint_EnableMotor,py::arg("joint_id"),py::arg("enable_motor"));
    m.def("distance_joint_is_motor_enabled", &b2DistanceJoint_IsMotorEnabled,py::arg("joint_id"));
    m.def("distance_joint_set_motor_speed", &b2DistanceJoint_SetMotorSpeed,py::arg("joint_id"),py::arg("motor_speed"));
    m.def("distance_joint_get_motor_speed", &b2DistanceJoint_GetMotorSpeed,py::arg("joint_id"));
    m.def("distance_joint_set_max_motor_force", &b2DistanceJoint_SetMaxMotorForce,py::arg("joint_id"),py::arg("max_force"));
    m.def("distance_joint_get_max_motor_force", &b2DistanceJoint_GetMaxMotorForce,py::arg("joint_id"));
    m.def("distance_joint_get_motor_force", &b2DistanceJoint_GetMotorForce,py::arg("joint_id"));
}



void export_motor_joint_functions(py::module_ & m){
    m.def("create_motor_joint", &b2CreateMotorJoint,py::arg("world_id"),py::arg("def"));
    m.def("motor_joint_set_linear_offset", &b2MotorJoint_SetLinearOffset,py::arg("joint_id"),py::arg("linear_offset"));
    m.def("motor_joint_get_linear_offset", &b2MotorJoint_GetLinearOffset,py::arg("joint_id"));
    m.def("motor_joint_set_angular_offset", &b2MotorJoint_SetAngularOffset,py::arg("joint_id"),py::arg("angular_offset"));
    m.def("motor_joint_get_angular_offset", &b2MotorJoint_GetAngularOffset,py::arg("joint_id"));
    m.def("motor_joint_set_max_force", &b2MotorJoint_SetMaxForce,py::arg("joint_id"),py::arg("max_force"));
    m.def("motor_joint_get_max_force", &b2MotorJoint_GetMaxForce,py::arg("joint_id"));
    m.def("motor_joint_set_max_torque", &b2MotorJoint_SetMaxTorque,py::arg("joint_id"),py::arg("max_torque"));
    m.def("motor_joint_get_max_torque", &b2MotorJoint_GetMaxTorque,py::arg("joint_id"));
    m.def("motor_joint_set_correction_factor", &b2MotorJoint_SetCorrectionFactor,py::arg("joint_id"),py::arg("correction_factor"));
    m.def("motor_joint_get_correction_factor", &b2MotorJoint_GetCorrectionFactor,py::arg("joint_id"));
}



void export_mouse_joint_functions(py::module_ & m){

    m.def("create_mouse_joint", &b2CreateMouseJoint,py::arg("world_id"),py::arg("def"));
    m.def("mouse_joint_set_target", &b2MouseJoint_SetTarget,py::arg("joint_id"),py::arg("target"));
    m.def("mouse_joint_get_target", &b2MouseJoint_GetTarget,py::arg("joint_id"));
    m.def("mouse_joint_set_spring_hertz", &b2MouseJoint_SetSpringHertz,py::arg("joint_id"),py::arg("hertz"));
    m.def("mouse_joint_get_spring_hertz", &b2MouseJoint_GetSpringHertz,py::arg("joint_id"));
    m.def("mouse_joint_set_spring_damping_ratio", &b2MouseJoint_SetSpringDampingRatio,py::arg("joint_id"),py::arg("damping_ratio"));
    m.def("mouse_joint_get_spring_damping_ratio", &b2MouseJoint_GetSpringDampingRatio,py::arg("joint_id"));
    m.def("mouse_joint_set_max_force", &b2MouseJoint_SetMaxForce,py::arg("joint_id"),py::arg("max_force"));
    m.def("mouse_joint_get_max_force", &b2MouseJoint_GetMaxForce,py::arg("joint_id"));
}

void export_null_joint_functions(py::module_ & m){
    m.def("create_null_joint", &b2CreateNullJoint,py::arg("world_id"),py::arg("def"));
}   

void export_prismatic_joint_functions(py::module_ & m){
    m.def("create_prismatic_joint", &b2CreatePrismaticJoint,py::arg("world_id"),py::arg("def"));
    m.def("prismatic_joint_enable_spring", &b2PrismaticJoint_EnableSpring,py::arg("joint_id"),py::arg("enable_spring"));
    m.def("prismatic_joint_is_spring_enabled", &b2PrismaticJoint_IsSpringEnabled,py::arg("joint_id"));
    m.def("prismatic_joint_set_spring_hertz", &b2PrismaticJoint_SetSpringHertz,py::arg("joint_id"),py::arg("hertz"));
    m.def("prismatic_joint_get_spring_hertz", &b2PrismaticJoint_GetSpringHertz,py::arg("joint_id"));
    m.def("prismatic_joint_set_spring_damping_ratio", &b2PrismaticJoint_SetSpringDampingRatio,py::arg("joint_id"),py::arg("damping_ratio"));
    m.def("prismatic_joint_get_spring_damping_ratio", &b2PrismaticJoint_GetSpringDampingRatio,py::arg("joint_id"));
    m.def("prismatic_joint_enable_limit", &b2PrismaticJoint_EnableLimit,py::arg("joint_id"),py::arg("enable_limit"));
    m.def("prismatic_joint_is_limit_enabled", &b2PrismaticJoint_IsLimitEnabled,py::arg("joint_id"));
    m.def("prismatic_joint_get_lower_limit", &b2PrismaticJoint_GetLowerLimit,py::arg("joint_id"));
    m.def("prismatic_joint_get_upper_limit", &b2PrismaticJoint_GetUpperLimit,py::arg("joint_id"));
    m.def("prismatic_joint_set_limits", &b2PrismaticJoint_SetLimits,py::arg("joint_id"),py::arg("lower"),py::arg("upper"));
    m.def("prismatic_joint_enable_motor", &b2PrismaticJoint_EnableMotor,py::arg("joint_id"),py::arg("enable_motor"));
    m.def("prismatic_joint_is_motor_enabled", &b2PrismaticJoint_IsMotorEnabled,py::arg("joint_id"));
    m.def("prismatic_joint_set_motor_speed", &b2PrismaticJoint_SetMotorSpeed,py::arg("joint_id"),py::arg("motor_speed"));
    m.def("prismatic_joint_get_motor_speed", &b2PrismaticJoint_GetMotorSpeed,py::arg("joint_id"));
    m.def("prismatic_joint_get_motor_force", &b2PrismaticJoint_GetMotorForce,py::arg("joint_id"));
    m.def("prismatic_joint_set_max_motor_force", &b2PrismaticJoint_SetMaxMotorForce,py::arg("joint_id"),py::arg("force"));
    m.def("prismatic_joint_get_max_motor_force", &b2PrismaticJoint_GetMaxMotorForce,py::arg("joint_id"));
    m.def("prismatic_joint_get_current_length", &b2PrismaticJoint_GetMotorForce,py::arg("joint_id"));
    m.def("prismatic_joint_get_translation", &b2PrismaticJoint_GetTranslation,py::arg("joint_id"));
    m.def("prismatic_joint_get_speed", &b2PrismaticJoint_GetSpeed,py::arg("joint_id"));
}

void export_revolute_joint_functions(py::module_ & m){
    
    m.def("create_revolute_joint", &b2CreateRevoluteJoint,py::arg("world_id"),py::arg("def"));
    m.def("revolute_joint_enable_spring", &b2RevoluteJoint_EnableSpring,py::arg("joint_id"),py::arg("enable_spring"));
    m.def("revolute_joint_is_spring_enabled", &b2RevoluteJoint_IsSpringEnabled,py::arg("joint_id"));
    m.def("revolute_joint_set_spring_hertz", &b2RevoluteJoint_SetSpringHertz,py::arg("joint_id"),py::arg("hertz"));
    m.def("revolute_joint_get_spring_hertz", &b2RevoluteJoint_GetSpringHertz,py::arg("joint_id"));
    m.def("revolute_joint_set_spring_damping_ratio", &b2RevoluteJoint_SetSpringDampingRatio,py::arg("joint_id"),py::arg("damping_ratio"));
    m.def("revolute_joint_get_spring_damping_ratio", &b2RevoluteJoint_GetSpringDampingRatio,py::arg("joint_id"));
    m.def("revolute_joint_get_angle", &b2RevoluteJoint_GetAngle,py::arg("joint_id"));
    m.def("revolute_joint_enable_limit", &b2RevoluteJoint_EnableLimit,py::arg("joint_id"),py::arg("enable_limit"));
    m.def("revolute_joint_is_limit_enabled", &b2RevoluteJoint_IsLimitEnabled,py::arg("joint_id"));
    m.def("revolute_joint_get_lower_limit", &b2RevoluteJoint_GetLowerLimit,py::arg("joint_id"));
    m.def("revolute_joint_get_upper_limit", &b2RevoluteJoint_GetUpperLimit,py::arg("joint_id"));
    m.def("revolute_joint_set_limits", &b2RevoluteJoint_SetLimits,py::arg("joint_id"),py::arg("lower"),py::arg("upper"));
    m.def("revolute_joint_enable_motor", &b2RevoluteJoint_EnableMotor,py::arg("joint_id"),py::arg("enable_motor"));
    m.def("revolute_joint_is_motor_enabled", &b2RevoluteJoint_IsMotorEnabled,py::arg("joint_id"));
    m.def("revolute_joint_set_motor_speed", &b2RevoluteJoint_SetMotorSpeed,py::arg("joint_id"),py::arg("motor_speed"));
    m.def("revolute_joint_get_motor_speed", &b2RevoluteJoint_GetMotorSpeed,py::arg("joint_id"));
    m.def("revolute_joint_get_motor_torque", &b2RevoluteJoint_GetMotorTorque,py::arg("joint_id"));
    m.def("revolute_joint_set_max_motor_torque", &b2RevoluteJoint_SetMaxMotorTorque,py::arg("joint_id"),py::arg("torque"));
    m.def("revolute_joint_get_max_motor_torque", &b2RevoluteJoint_GetMaxMotorTorque,py::arg("joint_id"));
}

void export_weld_joint_functions(py::module_ & m){

    m.def("create_weld_joint", &b2CreateWeldJoint,py::arg("world_id"),py::arg("def"));
    m.def("weld_joint_get_reference_angle", &b2WeldJoint_GetReferenceAngle,py::arg("joint_id"));
    m.def("weld_joint_set_reference_angle", &b2WeldJoint_SetReferenceAngle,py::arg("joint_id"),py::arg("angle_in_radians"));
    m.def("weld_joint_set_linear_hertz", &b2WeldJoint_SetLinearHertz,py::arg("joint_id"),py::arg("hertz"));
    m.def("weld_joint_get_linear_hertz", &b2WeldJoint_GetLinearHertz,py::arg("joint_id"));
    m.def("weld_joint_set_linear_damping_ratio", &b2WeldJoint_SetLinearDampingRatio,py::arg("joint_id"),py::arg("damping_ratio"));
    m.def("weld_joint_get_linear_damping_ratio", &b2WeldJoint_GetLinearDampingRatio,py::arg("joint_id"));
    m.def("weld_joint_set_angular_hertz", &b2WeldJoint_SetAngularHertz,py::arg("joint_id"),py::arg("hertz"));
    m.def("weld_joint_get_angular_hertz", &b2WeldJoint_GetAngularHertz,py::arg("joint_id"));
    m.def("weld_joint_set_angular_damping_ratio", &b2WeldJoint_SetAngularDampingRatio,py::arg("joint_id"),py::arg("damping_ratio"));
    m.def("weld_joint_get_angular_damping_ratio", &b2WeldJoint_GetAngularDampingRatio,py::arg("joint_id"));
}

void export_wheel_joint_functions(py::module_ & m){

    m.def("create_wheel_joint", &b2CreateWheelJoint,py::arg("world_id"),py::arg("def"));
    m.def("wheel_joint_enable_spring", &b2WheelJoint_EnableSpring,py::arg("joint_id"),py::arg("enable_spring"));
    m.def("wheel_joint_is_spring_enabled", &b2WheelJoint_IsSpringEnabled,py::arg("joint_id"));
    m.def("wheel_joint_set_spring_hertz", &b2WheelJoint_SetSpringHertz,py::arg("joint_id"),py::arg("hertz"));
    m.def("wheel_joint_get_spring_hertz", &b2WheelJoint_GetSpringHertz,py::arg("joint_id"));
    m.def("wheel_joint_set_spring_damping_ratio", &b2WheelJoint_SetSpringDampingRatio,py::arg("joint_id"),py::arg("damping_ratio"));
    m.def("wheel_joint_get_spring_damping_ratio", &b2WheelJoint_GetSpringDampingRatio,py::arg("joint_id"));
    m.def("wheel_joint_enable_limit", &b2WheelJoint_EnableLimit,py::arg("joint_id"),py::arg("enable_limit"));
    m.def("wheel_joint_is_limit_enabled", &b2WheelJoint_IsLimitEnabled,py::arg("joint_id"));
    m.def("wheel_joint_get_lower_limit", &b2WheelJoint_GetLowerLimit,py::arg("joint_id"));
    m.def("wheel_joint_get_upper_limit", &b2WheelJoint_GetUpperLimit,py::arg("joint_id"));
    m.def("wheel_joint_set_limits", &b2WheelJoint_SetLimits,py::arg("joint_id"),py::arg("lower"),py::arg("upper"));
    m.def("wheel_joint_enable_motor", &b2WheelJoint_EnableMotor,py::arg("joint_id"),py::arg("enable_motor"));
    m.def("wheel_joint_is_motor_enabled", &b2WheelJoint_IsMotorEnabled,py::arg("joint_id"));
    m.def("wheel_joint_set_motor_speed", &b2WheelJoint_SetMotorSpeed,py::arg("joint_id"),py::arg("motor_speed"));
    m.def("wheel_joint_get_motor_speed", &b2WheelJoint_GetMotorSpeed,py::arg("joint_id"));
    m.def("wheel_joint_set_max_motor_torque", &b2WheelJoint_SetMaxMotorTorque,py::arg("joint_id"),py::arg("torque"));
    m.def("wheel_joint_get_max_motor_torque", &b2WheelJoint_GetMaxMotorTorque,py::arg("joint_id"));
    m.def("wheel_joint_get_motor_torque", &b2WheelJoint_GetMotorTorque,py::arg("joint_id"));
}

void export_joint_functions(py::module_ & m){
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

void export_box2d_functions(py::module_ & m){
    export_world_functions(m);
    export_body_functions(m);
    export_shape_functions(m);
    export_chain_functions(m);
    export_joint_functions(m);
}
