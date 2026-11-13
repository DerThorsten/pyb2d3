#include <type_traits>
#include <utility>

#include <nanobind/nanobind.h>

#include "bind.hpp"
#include "defs_common.hpp"
#include "pyb2d3/py_converter.hpp"

namespace pyb2d3::bind
{
    namespace
    {
        // the fields of b2JointDef, listed once
        template <class F>
        void for_each_joint_base_field(F&& f)
        {
            f("body_a", &b2JointDef::bodyIdA);
            f("body_b", &b2JointDef::bodyIdB);
            f("local_frame_a", &b2JointDef::localFrameA);
            f("local_frame_b", &b2JointDef::localFrameB);
            f("force_threshold", &b2JointDef::forceThreshold);
            f("torque_threshold", &b2JointDef::torqueThreshold);
            f("constraint_hertz", &b2JointDef::constraintHertz);
            f("constraint_damping_ratio", &b2JointDef::constraintDampingRatio);
            f("draw_scale", &b2JointDef::drawScale);
            f("collide_connected", &b2JointDef::collideConnected);
        }

        // a concrete joint def: default init, copy, `base`, and all base fields forwarded
        template <class D, D (*Default)()>
        nb::class_<D> joint_def_class(nb::module_& m, const char* name)
        {
            auto cls = def_class<D, Default>(m, name);
            cls.def_rw("base", &D::base);

            for_each_joint_base_field(
                [&](const char* field, auto member)
                {
                    using V = std::decay_t<decltype(std::declval<b2JointDef&>().*member)>;
                    cls.def_prop_rw(
                        field,
                        [member](const D& d)
                        {
                            return d.base.*member;
                        },
                        [member](D& d, V value)
                        {
                            d.base.*member = value;
                        }
                    );
                }
            );

            // convenience: anchors are the origins of the local frames
            cls.def_prop_rw(
                   "local_anchor_a",
                   [](const D& d)
                   {
                       return d.base.localFrameA.p;
                   },
                   [](D& d, b2Vec2 p)
                   {
                       d.base.localFrameA.p = p;
                   }
            )
                .def_prop_rw(
                    "local_anchor_b",
                    [](const D& d)
                    {
                        return d.base.localFrameB.p;
                    },
                    [](D& d, b2Vec2 p)
                    {
                        d.base.localFrameB.p = p;
                    }
                )
                .def_prop_rw(
                    "user_data",
                    [](const D& d)
                    {
                        return reinterpret_cast<user_data_uint>(d.base.userData);
                    },
                    [](D& d, user_data_uint value)
                    {
                        d.base.userData = reinterpret_cast<void*>(value);
                    }
                );
            return cls;
        }
    }  // namespace

    void export_joint_defs(nb::module_& m)
    {
        nb::class_<b2JointDef> base(m, "JointDef");
        base.def(nb::init<>());
        for_each_joint_base_field(
            [&](const char* field, auto member)
            {
                base.def_rw(field, member);
            }
        );
        def_user_data(base);

        joint_def_class<b2DistanceJointDef, b2DefaultDistanceJointDef>(m, "DistanceJointDef")
            .def_rw("length", &b2DistanceJointDef::length)
            .def_rw("enable_spring", &b2DistanceJointDef::enableSpring)
            .def_rw("lower_spring_force", &b2DistanceJointDef::lowerSpringForce)
            .def_rw("upper_spring_force", &b2DistanceJointDef::upperSpringForce)
            .def_rw("hertz", &b2DistanceJointDef::hertz)
            .def_rw("damping_ratio", &b2DistanceJointDef::dampingRatio)
            .def_rw("enable_limit", &b2DistanceJointDef::enableLimit)
            .def_rw("min_length", &b2DistanceJointDef::minLength)
            .def_rw("max_length", &b2DistanceJointDef::maxLength)
            .def_rw("enable_motor", &b2DistanceJointDef::enableMotor)
            .def_rw("max_motor_force", &b2DistanceJointDef::maxMotorForce)
            .def_rw("motor_speed", &b2DistanceJointDef::motorSpeed);

        joint_def_class<b2FilterJointDef, b2DefaultFilterJointDef>(m, "FilterJointDef");

        joint_def_class<b2MotorJointDef, b2DefaultMotorJointDef>(m, "MotorJointDef")
            .def_rw("linear_velocity", &b2MotorJointDef::linearVelocity)
            .def_rw("max_velocity_force", &b2MotorJointDef::maxVelocityForce)
            .def_rw("angular_velocity", &b2MotorJointDef::angularVelocity)
            .def_rw("max_velocity_torque", &b2MotorJointDef::maxVelocityTorque)
            .def_rw("linear_hertz", &b2MotorJointDef::linearHertz)
            .def_rw("linear_damping_ratio", &b2MotorJointDef::linearDampingRatio)
            .def_rw("max_spring_force", &b2MotorJointDef::maxSpringForce)
            .def_rw("angular_hertz", &b2MotorJointDef::angularHertz)
            .def_rw("angular_damping_ratio", &b2MotorJointDef::angularDampingRatio)
            .def_rw("max_spring_torque", &b2MotorJointDef::maxSpringTorque);

        joint_def_class<b2MoverJointDef, b2DefaultMoverJointDef>(m, "MoverJointDef")
            .def_rw("linear_velocity", &b2MoverJointDef::linearVelocity)
            .def_rw("max_velocity_force", &b2MoverJointDef::maxVelocityForce);

        joint_def_class<b2PogoJointDef, b2DefaultPogoJointDef>(m, "PogoJointDef")
            .def_rw("normal", &b2PogoJointDef::normal)
            .def_rw("hertz", &b2PogoJointDef::hertz)
            .def_rw("damping_ratio", &b2PogoJointDef::dampingRatio)
            .def_rw("rest_length", &b2PogoJointDef::restLength)
            .def_rw("max_tension_force", &b2PogoJointDef::maxTensionForce)
            .def_rw("max_compression_force", &b2PogoJointDef::maxCompressionForce)
            .def_rw("impulse", &b2PogoJointDef::impulse)
            .def_rw("velocity", &b2PogoJointDef::velocity);

        joint_def_class<b2PrismaticJointDef, b2DefaultPrismaticJointDef>(m, "PrismaticJointDef")
            .def_rw("enable_spring", &b2PrismaticJointDef::enableSpring)
            .def_rw("hertz", &b2PrismaticJointDef::hertz)
            .def_rw("damping_ratio", &b2PrismaticJointDef::dampingRatio)
            .def_rw("target_translation", &b2PrismaticJointDef::targetTranslation)
            .def_rw("enable_limit", &b2PrismaticJointDef::enableLimit)
            .def_rw("lower_translation", &b2PrismaticJointDef::lowerTranslation)
            .def_rw("upper_translation", &b2PrismaticJointDef::upperTranslation)
            .def_rw("enable_motor", &b2PrismaticJointDef::enableMotor)
            .def_rw("max_motor_force", &b2PrismaticJointDef::maxMotorForce)
            .def_rw("motor_speed", &b2PrismaticJointDef::motorSpeed);

        joint_def_class<b2RevoluteJointDef, b2DefaultRevoluteJointDef>(m, "RevoluteJointDef")
            .def_rw("target_angle", &b2RevoluteJointDef::targetAngle)
            .def_rw("enable_spring", &b2RevoluteJointDef::enableSpring)
            .def_rw("hertz", &b2RevoluteJointDef::hertz)
            .def_rw("damping_ratio", &b2RevoluteJointDef::dampingRatio)
            .def_rw("enable_limit", &b2RevoluteJointDef::enableLimit)
            .def_rw("lower_angle", &b2RevoluteJointDef::lowerAngle)
            .def_rw("upper_angle", &b2RevoluteJointDef::upperAngle)
            .def_rw("enable_motor", &b2RevoluteJointDef::enableMotor)
            .def_rw("max_motor_torque", &b2RevoluteJointDef::maxMotorTorque)
            .def_rw("motor_speed", &b2RevoluteJointDef::motorSpeed);

        joint_def_class<b2WeldJointDef, b2DefaultWeldJointDef>(m, "WeldJointDef")
            .def_rw("linear_hertz", &b2WeldJointDef::linearHertz)
            .def_rw("angular_hertz", &b2WeldJointDef::angularHertz)
            .def_rw("linear_damping_ratio", &b2WeldJointDef::linearDampingRatio)
            .def_rw("angular_damping_ratio", &b2WeldJointDef::angularDampingRatio);

        joint_def_class<b2WheelJointDef, b2DefaultWheelJointDef>(m, "WheelJointDef")
            .def_rw("enable_spring", &b2WheelJointDef::enableSpring)
            .def_rw("hertz", &b2WheelJointDef::hertz)
            .def_rw("damping_ratio", &b2WheelJointDef::dampingRatio)
            .def_rw("enable_limit", &b2WheelJointDef::enableLimit)
            .def_rw("lower_translation", &b2WheelJointDef::lowerTranslation)
            .def_rw("upper_translation", &b2WheelJointDef::upperTranslation)
            .def_rw("enable_motor", &b2WheelJointDef::enableMotor)
            .def_rw("max_motor_torque", &b2WheelJointDef::maxMotorTorque)
            .def_rw("motor_speed", &b2WheelJointDef::motorSpeed);
    }
}  // namespace pyb2d3::bind
