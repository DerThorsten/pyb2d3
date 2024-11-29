#include <nanobind/nanobind.h>

#include "converter.hpp"

// C
extern "C" {
#include <box2d/math_functions.h>
#include <box2d/box2d.h>
}

// nanobind namespace
namespace py = nanobind;

void export_id_types(py::module_ & m)
{
    py::class_<b2BodyId>(m, "BodyId")
    ;
    py::class_<b2ShapeId>(m, "ShapeId")
    ;
    py::class_<b2WorldId>(m, "WorldId")
    ;
}

void export_b2Vec2(py::module_ &m) {
    // py::class_<b2Vec2>(m, "Vec2")
    //     .def(py::init<>())
    //     .def(py::init<float, float>())
    //     .def_rw("x", &b2Vec2::x)
    //     .def_rw("y", &b2Vec2::y)
    // ;
}

void export_ray_result(py::module_ &m) {
    py::class_<b2RayResult>(m, "RayResult")
        .def_rw("shape_id", &b2RayResult::shapeId)
        .def_rw("point", &b2RayResult::point)
        .def_rw("normal", &b2RayResult::normal)
        .def_rw("fraction", &b2RayResult::fraction)
        .def_rw("node_visits", &b2RayResult::nodeVisits)
        .def_rw("leaf_visits", &b2RayResult::leafVisits)
    ;
}

void export_mixing_rule(py::module_ &m) {
    py::enum_<b2MixingRule>(m, "MixingRule")
        .value("average", b2_mixAverage)
        .value("geometric_mean", b2_mixGeometricMean)
        .value("multiply", b2_mixMultiply)
        .value("minimum", b2_mixMinimum)
        .value("maximum", b2_mixMaximum)
    ;
}


void export_world_def(py::module_ &m) {

    // b2WorldDef
    py::class_<b2WorldDef>(m, "WorldDef")

        .def("__init__", [](b2WorldDef *t) { new (t) b2WorldDef(b2DefaultWorldDef()); })
        .def_rw("gravity", &b2WorldDef::gravity)
        .def_rw("restitution_threshold", &b2WorldDef::restitutionThreshold)
        .def_rw("contact_pushout_velocity", &b2WorldDef::contactPushoutVelocity)
        .def_rw("hit_event_threshold", &b2WorldDef::hitEventThreshold)
        .def_rw("contact_hertz", &b2WorldDef::contactHertz)
        .def_rw("contact_damping_ratio", &b2WorldDef::contactDampingRatio)
        .def_rw("joint_hertz", &b2WorldDef::jointHertz)
        .def_rw("joint_damping_ratio", &b2WorldDef::jointDampingRatio)
        .def_rw("maximum_linear_velocity", &b2WorldDef::maximumLinearVelocity)
        .def_rw("friction_mixing_rule", &b2WorldDef::frictionMixingRule)
        .def_rw("restitution_mixing_rule", &b2WorldDef::restitutionMixingRule)
        // .def_rw("enqueue_task", &b2WorldDef::enqueueTask)
        // .def_rw("finish_task", &b2WorldDef::finishTask)
        // .def_rw("user_task_context", &b2WorldDef::userTaskContext)
        // .def_rw("user_data", &b2WorldDef::userData)
        .def_rw("internal_value", &b2WorldDef::internalValue)
    ;
}

void export_body_def(py::module_ &m) {

    py::enum_<b2BodyType>(m, "BodyType")
        .value("STATIC", b2_staticBody)
        .value("KINEMATIC", b2_kinematicBody)
        .value("DYNAMIC", b2_dynamicBody)
    ;


    // body def 
    py::class_<b2BodyDef>(m, "BodyDef")
        .def("__init__", [](b2BodyDef *t) { new (t) b2BodyDef(b2DefaultBodyDef()); })
        .def_rw("type", &b2BodyDef::type)
        .def_rw("position", &b2BodyDef::position)
        .def_rw("rotation", &b2BodyDef::rotation)
        .def_rw("linear_velocity", &b2BodyDef::linearVelocity)
        .def_rw("angular_velocity", &b2BodyDef::angularVelocity)
        .def_rw("linear_damping", &b2BodyDef::linearDamping)
        .def_rw("angular_damping", &b2BodyDef::angularDamping)
        .def_rw("gravity_scale", &b2BodyDef::gravityScale)
        .def_rw("sleep_threshold", &b2BodyDef::sleepThreshold)
        // .def_rw("user_data", &b2BodyDef::userData)
        .def_rw("enable_sleep", &b2BodyDef::enableSleep)
        .def_rw("is_awake", &b2BodyDef::isAwake)
        .def_rw("fixed_rotation", &b2BodyDef::fixedRotation)
        .def_rw("is_bullet", &b2BodyDef::isBullet)
        .def_rw("is_enabled", &b2BodyDef::isEnabled)
        .def_rw("internal_value", &b2BodyDef::internalValue)
    ; 
    
}

void export_filter(py::module_ &m) {
    py::class_<b2Filter>(m, "Filter")
        .def("__init__", [](b2Filter *t) { new (t) b2Filter(b2DefaultFilter()); })
        .def_rw("category_bits", &b2Filter::categoryBits)
        .def_rw("mask_bits", &b2Filter::maskBits)
        .def_rw("group_index", &b2Filter::groupIndex)
    ;
} 

void export_query_filter(py::module_ &m) {
    py::class_<b2QueryFilter>(m, "QueryFilter")
        .def("__init__", [](b2QueryFilter *t) { new (t) b2QueryFilter(b2DefaultQueryFilter()); })
        .def_rw("category_bits", &b2QueryFilter::categoryBits)
        .def_rw("mask_bits", &b2QueryFilter::maskBits)
    ;
}

void export_shape_def(py::module_ &m) {
    py::class_<b2ShapeDef>(m, "ShapeDef")
        .def("__init__", [](b2ShapeDef *t) { new (t) b2ShapeDef(b2DefaultShapeDef()); })
        .def_rw("friction", &b2ShapeDef::friction)
        .def_rw("restitution", &b2ShapeDef::restitution)
        .def_rw("density", &b2ShapeDef::density)
        .def_rw("filter", &b2ShapeDef::filter)
        .def_rw("custom_color", &b2ShapeDef::customColor)
        .def_rw("is_sensor", &b2ShapeDef::isSensor)
        .def_rw("enable_sensor_events", &b2ShapeDef::enableSensorEvents)
        .def_rw("enable_contact_events", &b2ShapeDef::enableContactEvents)
        .def_rw("enable_hit_events", &b2ShapeDef::enableHitEvents)
        .def_rw("enable_pre_solve_events", &b2ShapeDef::enablePreSolveEvents)
        .def_rw("invoke_contact_creation", &b2ShapeDef::invokeContactCreation)
        .def_rw("update_body_mass", &b2ShapeDef::updateBodyMass)
        .def_rw("internal_value", &b2ShapeDef::internalValue)
    ;
}

void export_chain_def(py::module_ &m) {
    py::class_<b2ChainDef>(m, "ChainDef")
        .def("__init__", [](b2ChainDef *t) { new (t) b2ChainDef(b2DefaultChainDef()); })
        //.def_rw("points", &b2ChainDef::points) //TODO
        .def_rw("count", &b2ChainDef::count)
        .def_rw("friction", &b2ChainDef::friction)
        .def_rw("restitution", &b2ChainDef::restitution)
        .def_rw("filter", &b2ChainDef::filter)
        .def_rw("custom_color", &b2ChainDef::customColor)
        .def_rw("is_loop", &b2ChainDef::isLoop)
        .def_rw("internal_value", &b2ChainDef::internalValue)
    ;
}

void export_profile(py::module_ &m) {

    py::class_<b2Profile>(m, "Profile")
        .def_rw("step", &b2Profile::step)
        .def_rw("pairs", &b2Profile::pairs)
        .def_rw("collide", &b2Profile::collide)
        .def_rw("solve", &b2Profile::solve)
        .def_rw("build_islands", &b2Profile::buildIslands)
        .def_rw("solve_constraints", &b2Profile::solveConstraints)
        .def_rw("prepare_tasks", &b2Profile::prepareTasks)
        .def_rw("solver_tasks", &b2Profile::solverTasks)
        .def_rw("prepare_constraints", &b2Profile::prepareConstraints)
        .def_rw("integrate_velocities", &b2Profile::integrateVelocities)
        .def_rw("warm_start", &b2Profile::warmStart)
        .def_rw("solve_velocities", &b2Profile::solveVelocities)
        .def_rw("integrate_positions", &b2Profile::integratePositions)
        .def_rw("relax_velocities", &b2Profile::relaxVelocities)
        .def_rw("apply_restitution", &b2Profile::applyRestitution)
        .def_rw("store_impulses", &b2Profile::storeImpulses)
        .def_rw("finalize_bodies", &b2Profile::finalizeBodies)
        .def_rw("split_islands", &b2Profile::splitIslands)
        .def_rw("sleep_islands", &b2Profile::sleepIslands)
        .def_rw("hit_events", &b2Profile::hitEvents)
        .def_rw("broadphase", &b2Profile::broadphase)
        .def_rw("continuous", &b2Profile::continuous)
    ;
}

void export_counters(py::module_ &m) {
    py::class_<b2Counters>
        (m, "Counters")
        .def_rw("body_count", &b2Counters::bodyCount)
        .def_rw("shape_count", &b2Counters::shapeCount)
        .def_rw("contact_count", &b2Counters::contactCount)
        .def_rw("joint_count", &b2Counters::jointCount)
        .def_rw("island_count", &b2Counters::islandCount)
        .def_rw("stack_used", &b2Counters::stackUsed)
        .def_rw("static_tree_height", &b2Counters::staticTreeHeight)
        .def_rw("tree_height", &b2Counters::treeHeight)
        .def_rw("byte_count", &b2Counters::byteCount)
        .def_rw("task_count", &b2Counters::taskCount)
       // .def_rw("color_counts", &b2Counters::colorCounts) //TODO
    ;
}

void export_joint_defs(py::module_ &m) {

    py::enum_<b2JointType>(m, "JointType")
        .value("distance_joint", b2_distanceJoint)
        .value("motor_joint", b2_motorJoint)
        .value("mouse_joint", b2_mouseJoint)
        .value("null_joint", b2_nullJoint)
        .value("prismatic_joint", b2_prismaticJoint)
        .value("revolute_joint", b2_revoluteJoint)
        .value("weld_joint", b2_weldJoint)
        .value("wheel_joint", b2_wheelJoint)
    ;

    py::class_<b2DistanceJointDef>(m, "DistanceJointDef")
        .def("__init__", [](b2DistanceJointDef *t) { new (t) b2DistanceJointDef(b2DefaultDistanceJointDef()); })
        .def_rw("body_id_a", &b2DistanceJointDef::bodyIdA)
        .def_rw("body_id_b", &b2DistanceJointDef::bodyIdB)
        .def_rw("local_anchor_a", &b2DistanceJointDef::localAnchorA)
        .def_rw("local_anchor_b", &b2DistanceJointDef::localAnchorB)
        .def_rw("length", &b2DistanceJointDef::length)
        .def_rw("enable_spring", &b2DistanceJointDef::enableSpring)
        .def_rw("hertz", &b2DistanceJointDef::hertz)
        .def_rw("damping_ratio", &b2DistanceJointDef::dampingRatio)
        .def_rw("enable_limit", &b2DistanceJointDef::enableLimit)
        .def_rw("min_length", &b2DistanceJointDef::minLength)
        .def_rw("max_length", &b2DistanceJointDef::maxLength)
        .def_rw("enable_motor", &b2DistanceJointDef::enableMotor)
        .def_rw("max_motor_force", &b2DistanceJointDef::maxMotorForce)
        .def_rw("motor_speed", &b2DistanceJointDef::motorSpeed)
        .def_rw("collide_connected", &b2DistanceJointDef::collideConnected)
        //.def_rw("user_data", &b2DistanceJointDef::userData) TODO
        .def_rw("internal_value", &b2DistanceJointDef::internalValue)
    ;

    // motor joint def
    py::class_<b2MotorJointDef>(m, "MotorJointDef")
        .def("__init__", [](b2MotorJointDef *t) { new (t) b2MotorJointDef(b2DefaultMotorJointDef()); })
        .def_rw("body_id_a", &b2MotorJointDef::bodyIdA)
        .def_rw("body_id_b", &b2MotorJointDef::bodyIdB)
        .def_rw("linear_offset", &b2MotorJointDef::linearOffset)
        .def_rw("angular_offset", &b2MotorJointDef::angularOffset)
        .def_rw("max_force", &b2MotorJointDef::maxForce)
        .def_rw("max_torque", &b2MotorJointDef::maxTorque)
        .def_rw("correction_factor", &b2MotorJointDef::correctionFactor)
        .def_rw("collide_connected", &b2MotorJointDef::collideConnected)
        //.def_rw("user_data", &b2MotorJointDef::userData) TODO
        .def_rw("internal_value", &b2MotorJointDef::internalValue)
    ;

    py::class_<b2MouseJointDef>(m, "MouseJointDef")
        .def("__init__", [](b2MouseJointDef *t) { new (t) b2MouseJointDef(b2DefaultMouseJointDef()); })
        .def_rw("body_id_a", &b2MouseJointDef::bodyIdA)
        .def_rw("body_id_b", &b2MouseJointDef::bodyIdB)
        .def_rw("target", &b2MouseJointDef::target)
        .def_rw("max_force", &b2MouseJointDef::maxForce)
        .def_rw("hertz", &b2MouseJointDef::hertz)
        .def_rw("damping_ratio", &b2MouseJointDef::dampingRatio)
        .def_rw("collide_connected", &b2MouseJointDef::collideConnected)
        //.def_rw("user_data", &b2MouseJointDef::userData) TODO
        .def_rw("internal_value", &b2MouseJointDef::internalValue)
    ;

    py::class_<b2NullJointDef>(m, "NullJointDef")
        .def("__init__", [](b2NullJointDef *t) { new (t) b2NullJointDef(b2DefaultNullJointDef()); })
        .def_rw("body_id_a", &b2NullJointDef::bodyIdA)
        .def_rw("body_id_b", &b2NullJointDef::bodyIdB)
        //.def_rw("user_data", &b2NullJointDef::userData) TODO
        .def_rw("internal_value", &b2NullJointDef::internalValue)
    ;
    
    py::class_<b2PrismaticJointDef>(m, "PrismaticJointDef")
        .def("__init__", [](b2PrismaticJointDef *t) { new (t) b2PrismaticJointDef(b2DefaultPrismaticJointDef()); })
        .def_rw("body_id_a", &b2PrismaticJointDef::bodyIdA)
        .def_rw("body_id_b", &b2PrismaticJointDef::bodyIdB)
        .def_rw("local_anchor_a", &b2PrismaticJointDef::localAnchorA)
        .def_rw("local_anchor_b", &b2PrismaticJointDef::localAnchorB)
        .def_rw("local_axis_a", &b2PrismaticJointDef::localAxisA)
        .def_rw("reference_angle", &b2PrismaticJointDef::referenceAngle)
        .def_rw("enable_spring", &b2PrismaticJointDef::enableSpring)
        .def_rw("hertz", &b2PrismaticJointDef::hertz)
        .def_rw("damping_ratio", &b2PrismaticJointDef::dampingRatio)
        .def_rw("enable_limit", &b2PrismaticJointDef::enableLimit)
        .def_rw("lower_translation", &b2PrismaticJointDef::lowerTranslation)
        .def_rw("upper_translation", &b2PrismaticJointDef::upperTranslation)
        .def_rw("enable_motor", &b2PrismaticJointDef::enableMotor)
        .def_rw("max_motor_force", &b2PrismaticJointDef::maxMotorForce)
        .def_rw("motor_speed", &b2PrismaticJointDef::motorSpeed)
        .def_rw("collide_connected", &b2PrismaticJointDef::collideConnected)
        //.def_rw("user_data", &b2PrismaticJointDef::userData) TODO
        .def_rw("internal_value", &b2PrismaticJointDef::internalValue)
    ;

    py::class_<b2RevoluteJointDef>(m, "RevoluteJointDef")
        .def("__init__", [](b2RevoluteJointDef *t) { new (t) b2RevoluteJointDef(b2DefaultRevoluteJointDef()); })
        .def_rw("body_id_a", &b2RevoluteJointDef::bodyIdA)
        .def_rw("body_id_b", &b2RevoluteJointDef::bodyIdB)
        .def_rw("local_anchor_a", &b2RevoluteJointDef::localAnchorA)
        .def_rw("local_anchor_b", &b2RevoluteJointDef::localAnchorB)
        .def_rw("reference_angle", &b2RevoluteJointDef::referenceAngle)
        .def_rw("enable_spring", &b2RevoluteJointDef::enableSpring)
        .def_rw("hertz", &b2RevoluteJointDef::hertz)
        .def_rw("damping_ratio", &b2RevoluteJointDef::dampingRatio)
        .def_rw("enable_limit", &b2RevoluteJointDef::enableLimit)
        .def_rw("lower_angle", &b2RevoluteJointDef::lowerAngle)
        .def_rw("upper_angle", &b2RevoluteJointDef::upperAngle)
        .def_rw("enable_motor", &b2RevoluteJointDef::enableMotor)
        .def_rw("max_motor_torque", &b2RevoluteJointDef::maxMotorTorque)
        .def_rw("motor_speed", &b2RevoluteJointDef::motorSpeed)
        .def_rw("draw_size", &b2RevoluteJointDef::drawSize)
        .def_rw("collide_connected", &b2RevoluteJointDef::collideConnected)
        //.def_rw("user_data", &b2RevoluteJointDef::userData) TODO
        .def_rw("internal_value", &b2RevoluteJointDef::internalValue)
    ;

    py::class_<b2WeldJointDef>(m, "WeldJointDef")
        .def("__init__", [](b2WeldJointDef *t) { new (t) b2WeldJointDef(b2DefaultWeldJointDef()); })
        .def_rw("body_id_a", &b2WeldJointDef::bodyIdA)
        .def_rw("body_id_b", &b2WeldJointDef::bodyIdB)
        .def_rw("local_anchor_a", &b2WeldJointDef::localAnchorA)
        .def_rw("local_anchor_b", &b2WeldJointDef::localAnchorB)
        .def_rw("reference_angle", &b2WeldJointDef::referenceAngle)
        .def_rw("linear_hertz", &b2WeldJointDef::linearHertz)
        .def_rw("angular_hertz", &b2WeldJointDef::angularHertz)
        .def_rw("linear_damping_ratio", &b2WeldJointDef::linearDampingRatio)
        .def_rw("angular_damping_ratio", &b2WeldJointDef::angularDampingRatio)
        .def_rw("collide_connected", &b2WeldJointDef::collideConnected)
        //.def_rw("user_data", &b2WeldJointDef::userData) TODO
        .def_rw("internal_value", &b2WeldJointDef::internalValue)
    ;

    py::class_<b2WheelJointDef>(m, "WheelJointDef")
        .def("__init__", [](b2WheelJointDef *t) { new (t) b2WheelJointDef(b2DefaultWheelJointDef()); })
        .def_rw("body_id_a", &b2WheelJointDef::bodyIdA)
        .def_rw("body_id_b", &b2WheelJointDef::bodyIdB)
        .def_rw("local_anchor_a", &b2WheelJointDef::localAnchorA)
        .def_rw("local_anchor_b", &b2WheelJointDef::localAnchorB)
        .def_rw("local_axis_a", &b2WheelJointDef::localAxisA)
        .def_rw("enable_spring", &b2WheelJointDef::enableSpring)
        .def_rw("hertz", &b2WheelJointDef::hertz)
        .def_rw("damping_ratio", &b2WheelJointDef::dampingRatio)
        .def_rw("enable_limit", &b2WheelJointDef::enableLimit)
        .def_rw("lower_translation", &b2WheelJointDef::lowerTranslation)
        .def_rw("upper_translation", &b2WheelJointDef::upperTranslation)
        .def_rw("enable_motor", &b2WheelJointDef::enableMotor)
        .def_rw("max_motor_torque", &b2WheelJointDef::maxMotorTorque)
        .def_rw("motor_speed", &b2WheelJointDef::motorSpeed)
        .def_rw("collide_connected", &b2WheelJointDef::collideConnected)
        //.def_rw("user_data", &b2WheelJointDef::userData) TODO
        .def_rw("internal_value", &b2WheelJointDef::internalValue)
    ;
}

void export_explosion_def(py::module_ &m) {

    py::class_<b2ExplosionDef>(m, "ExplosionDef")
        .def("__init__", [](b2ExplosionDef *t) { new (t) b2ExplosionDef(b2DefaultExplosionDef()); })
        .def_rw("mask_bits", &b2ExplosionDef::maskBits)
        .def_rw("position", &b2ExplosionDef::position)
        .def_rw("radius", &b2ExplosionDef::radius)
        .def_rw("falloff", &b2ExplosionDef::falloff)
        .def_rw("impulse_per_length", &b2ExplosionDef::impulsePerLength)
    ;
}   

void export_events(py::module_ &m) {

    py::class_<b2SensorBeginTouchEvent>(m, "SensorBeginTouchEvent")
        .def_rw("sensor_shape_id", &b2SensorBeginTouchEvent::sensorShapeId)
        .def_rw("visitor_shape_id", &b2SensorBeginTouchEvent::visitorShapeId)
    ;

    py::class_<b2SensorEndTouchEvent>(m, "SensorEndTouchEvent")
        .def_rw("sensor_shape_id", &b2SensorEndTouchEvent::sensorShapeId)
        .def_rw("visitor_shape_id", &b2SensorEndTouchEvent::visitorShapeId)
    ;

    py::class_<b2SensorEvents>(m, "SensorEvents")
        //.def_rw("begin_events", &b2SensorEvents::beginEvents)
        // .def_rw("end_events", &b2SensorEvents::endEvents)
        .def_rw("begin_count", &b2SensorEvents::beginCount)
        .def_rw("end_count", &b2SensorEvents::endCount)
    ;

    py::class_<b2ContactBeginTouchEvent>(m, "ContactBeginTouchEvent")
        .def_rw("shape_id_a", &b2ContactBeginTouchEvent::shapeIdA)
        .def_rw("shape_id_b", &b2ContactBeginTouchEvent::shapeIdB)
        .def_rw("manifold", &b2ContactBeginTouchEvent::manifold)
    ;

    py::class_<b2ContactEndTouchEvent>(m, "ContactEndTouchEvent")
        .def_rw("shape_id_a", &b2ContactEndTouchEvent::shapeIdA)
        .def_rw("shape_id_b", &b2ContactEndTouchEvent::shapeIdB)
    ;

    py::class_<b2ContactHitEvent>(m, "ContactHitEvent")
        .def_rw("shape_id_a", &b2ContactHitEvent::shapeIdA)
        .def_rw("shape_id_b", &b2ContactHitEvent::shapeIdB)
        .def_rw("point", &b2ContactHitEvent::point)
        .def_rw("normal", &b2ContactHitEvent::normal)
        .def_rw("approach_speed", &b2ContactHitEvent::approachSpeed)
    ;

    py::class_<b2ContactEvents>(m, "ContactEvents")
        //.def_rw("begin_events", &b2ContactEvents::beginEvents)
        //.def_rw("end_events", &b2ContactEvents::endEvents)
        .def_rw("hit_events", &b2ContactEvents::hitEvents)
        .def_rw("begin_count", &b2ContactEvents::beginCount)
        .def_rw("end_count", &b2ContactEvents::endCount)
        .def_rw("hit_count", &b2ContactEvents::hitCount)
    ;
    
    py::class_<b2BodyMoveEvent>(m, "BodyMoveEvent")
        .def_rw("transform", &b2BodyMoveEvent::transform)
        .def_rw("body_id", &b2BodyMoveEvent::bodyId)
        //.def_rw("user_data", &b2BodyMoveEvent::userData)
        .def_rw("fell_asleep", &b2BodyMoveEvent::fellAsleep)
    ;

    py::class_<b2BodyEvents>(m, "BodyEvents")
        //.def_rw("move_events", &b2BodyEvents::moveEvents)
        .def_rw("move_count", &b2BodyEvents::moveCount)
    ;
}

void export_contact_data(py::module_ &m) {
    py::class_<b2ContactData>(m, "ContactData")
        .def_rw("shape_id_a", &b2ContactData::shapeIdA)
        .def_rw("shape_id_b", &b2ContactData::shapeIdB)
        .def_rw("manifold", &b2ContactData::manifold)
    ;
}

void export_box2d_types(py::module_ &m) {
    export_b2Vec2(m);
    export_world_def(m);
    export_body_def(m);
    export_id_types(m);
    export_ray_result(m);
    export_mixing_rule(m);
    export_filter(m);
    export_query_filter(m);
    export_shape_def(m);
    export_chain_def(m);
    export_profile(m);
    export_counters(m);
    export_joint_defs(m);
    export_explosion_def(m);
    export_events(m);
    export_contact_data(m);
}