#include <tuple>

#include <nanobind/nanobind.h>
#include <nanobind/stl/tuple.h>

#include "bind.hpp"
#include "pyb2d3/core/binder.hpp"
#include "pyb2d3/py_converter.hpp"

namespace pyb2d3::bind
{
    namespace
    {
        template <class T>
        using JointBinder = Binder<T, Joint>;

        // ---- features shared by several joint types --------------------------------

        // spring_enabled, spring_hertz, spring_damping_ratio
        template <auto IsEnabled, auto Enable, auto GetHertz, auto SetHertz, auto GetDamping, auto SetDamping, class B>
        void bind_spring(B& b)
        {
            b.template rw<IsEnabled, Enable>("spring_enabled")
                .template rw<GetHertz, SetHertz>("spring_hertz")
                .template rw<GetDamping, SetDamping>("spring_damping_ratio");
        }

        // limit_enabled, set_limits(lower, upper), lower_limit, upper_limit
        template <auto IsEnabled, auto Enable, auto SetLimits, auto GetLower, auto GetUpper, class B>
        void bind_limit(B& b)
        {
            b.template rw<IsEnabled, Enable>("limit_enabled")
                .template def<SetLimits>("set_limits", nb::arg("lower"), nb::arg("upper"))
                .template ro<GetLower>("lower_limit")
                .template ro<GetUpper>("upper_limit");
        }

        // motor_enabled, target_motor_speed, max_motor_{force|torque}, current_motor_{force|torque}
        template <
            auto IsEnabled,
            auto Enable,
            auto GetSpeed,
            auto SetSpeed,
            auto GetMax,
            auto SetMax,
            auto GetCurrent,
            class B>
        void bind_motor(B& b, const char* max_name, const char* current_name)
        {
            b.template rw<IsEnabled, Enable>("motor_enabled")
                .template rw<GetSpeed, SetSpeed>("target_motor_speed")
                .template rw<GetMax, SetMax>(max_name)
                .template ro<GetCurrent>(current_name);
        }

        template <class T>
        nb::class_<T, Joint> joint_class(nb::module_& m, const char* name)
        {
            nb::class_<T, Joint> cls(m, name);
            cls.def(nb::init<uint64_t>(), nb::arg("id"));
            return cls;
        }

        // ---- extras that are not a plain getter --------------------------------------

        std::tuple<float, float> get_constraint_tuning(const Joint& self)
        {
            float hertz = 0.0f, damping_ratio = 0.0f;
            b2Joint_GetConstraintTuning(self.id, &hertz, &damping_ratio);
            return {hertz, damping_ratio};
        }

        std::tuple<float, float> get_spring_force_range(const DistanceJoint& self)
        {
            float lower = 0.0f, upper = 0.0f;
            b2DistanceJoint_GetSpringForceRange(self.id, &lower, &upper);
            return {lower, upper};
        }
    }  // namespace

    void export_joint(nb::module_& m)
    {
        nb::enum_<b2JointType>(m, "JointType")
            .value("DISTANCE", b2_distanceJoint)
            .value("FILTER", b2_filterJoint)
            .value("MOTOR", b2_motorJoint)
            .value("MOVER", b2_moverJoint)
            .value("POGO", b2_pogoJoint)
            .value("PRISMATIC", b2_prismaticJoint)
            .value("REVOLUTE", b2_revoluteJoint)
            .value("WELD", b2_weldJoint)
            .value("WHEEL", b2_wheelJoint);

        // ---- base class ----------------------------------------------------------------
        nb::class_<Joint> cls(m, "Joint");
        nb::class_<Batch<Joint>> batch_cls(m, "Joints");
        bind_handle(cls, batch_cls);

        Binder(cls, batch_cls)
            .ro<b2Joint_GetType>("type")
            .ro<b2Joint_GetBodyA>("body_a")
            .ro<b2Joint_GetBodyB>("body_b")
            .ro<b2Joint_GetWorld>("world")
            .rw<b2Joint_GetLocalFrameA, b2Joint_SetLocalFrameA>("local_frame_a")
            .rw<b2Joint_GetLocalFrameB, b2Joint_SetLocalFrameB>("local_frame_b")
            .rw<b2Joint_GetCollideConnected, b2Joint_SetCollideConnected>("collide_connected")
            .def<b2Joint_WakeBodies>("wake_bodies")
            .ro<b2Joint_GetConstraintForce>("constraint_force")
            .ro<b2Joint_GetConstraintTorque>("constraint_torque")
            .ro<b2Joint_GetLinearSeparation>("linear_separation")
            .ro<b2Joint_GetAngularSeparation>("angular_separation")
            .def<b2Joint_SetConstraintTuning>("set_constraint_tuning", nb::arg("hertz"), nb::arg("damping_ratio"))
            .rw<b2Joint_GetForceThreshold, b2Joint_SetForceThreshold>("force_threshold")
            .rw<b2Joint_GetTorqueThreshold, b2Joint_SetTorqueThreshold>("torque_threshold");

        cls.def("destroy", &Joint::Destroy)
            .def(
                "cast",
                [](const Joint& self)
                {
                    return GetCastedJoint(self.id);
                }
            )
            .def_prop_ro("constraint_tuning", &get_constraint_tuning);

        // ---- distance --------------------------------------------------------------------
        {
            auto c = joint_class<DistanceJoint>(m, "DistanceJoint");
            JointBinder<DistanceJoint> b(c);
            b.rw<b2DistanceJoint_GetRestLength, b2DistanceJoint_SetRestLength>("rest_length")
                .ro<b2DistanceJoint_GetCurrentLength>("current_length")
                .ro<b2DistanceJoint_GetSpringForce>("spring_force")
                .def<b2DistanceJoint_SetSpringForceRange>(
                    "set_spring_force_range",
                    nb::arg("lower_force"),
                    nb::arg("upper_force")
                );
            bind_spring<
                b2DistanceJoint_IsSpringEnabled,
                b2DistanceJoint_EnableSpring,
                b2DistanceJoint_GetSpringHertz,
                b2DistanceJoint_SetSpringHertz,
                b2DistanceJoint_GetSpringDampingRatio,
                b2DistanceJoint_SetSpringDampingRatio>(b);
            bind_limit<
                b2DistanceJoint_IsLimitEnabled,
                b2DistanceJoint_EnableLimit,
                b2DistanceJoint_SetLimits,
                b2DistanceJoint_GetLowerLimit,
                b2DistanceJoint_GetUpperLimit>(b);
            bind_motor<
                b2DistanceJoint_IsMotorEnabled,
                b2DistanceJoint_EnableMotor,
                b2DistanceJoint_GetTargetMotorSpeed,
                b2DistanceJoint_SetTargetMotorSpeed,
                b2DistanceJoint_GetMaxMotorForce,
                b2DistanceJoint_SetMaxMotorForce,
                b2DistanceJoint_GetCurrentMotorForce>(b, "max_motor_force", "current_motor_force");
            c.def_prop_ro("spring_force_range", &get_spring_force_range);
        }

        // ---- filter (no extra api) ---------------------------------------------------------
        joint_class<FilterJoint>(m, "FilterJoint");

        // ---- motor -------------------------------------------------------------------------
        {
            auto c = joint_class<MotorJoint>(m, "MotorJoint");
            JointBinder<MotorJoint>(c)
                .rw<b2MotorJoint_GetLinearVelocity, b2MotorJoint_SetLinearVelocity>("linear_velocity")
                .rw<b2MotorJoint_GetAngularVelocity, b2MotorJoint_SetAngularVelocity>("angular_velocity")
                .rw<b2MotorJoint_GetMaxVelocityForce, b2MotorJoint_SetMaxVelocityForce>("max_velocity_force")
                .rw<b2MotorJoint_GetMaxVelocityTorque, b2MotorJoint_SetMaxVelocityTorque>("max_velocity_torque")
                .rw<b2MotorJoint_GetLinearHertz, b2MotorJoint_SetLinearHertz>("linear_hertz")
                .rw<b2MotorJoint_GetLinearDampingRatio, b2MotorJoint_SetLinearDampingRatio>("linear_damping_ratio")
                .rw<b2MotorJoint_GetAngularHertz, b2MotorJoint_SetAngularHertz>("angular_hertz")
                .rw<b2MotorJoint_GetAngularDampingRatio, b2MotorJoint_SetAngularDampingRatio>("angular_damping_ratio")
                .rw<b2MotorJoint_GetMaxSpringForce, b2MotorJoint_SetMaxSpringForce>("max_spring_force")
                .rw<b2MotorJoint_GetMaxSpringTorque, b2MotorJoint_SetMaxSpringTorque>("max_spring_torque");
        }

        // ---- mover -------------------------------------------------------------------------
        {
            auto c = joint_class<MoverJoint>(m, "MoverJoint");
            JointBinder<MoverJoint>(c)
                .rw<b2MoverJoint_GetLinearVelocity, b2MoverJoint_SetLinearVelocity>("linear_velocity")
                .rw<b2MoverJoint_GetMaxVelocityForce, b2MoverJoint_SetMaxVelocityForce>("max_velocity_force");
        }

        // ---- pogo --------------------------------------------------------------------------
        {
            auto c = joint_class<PogoJoint>(m, "PogoJoint");
            JointBinder<PogoJoint>(c)
                .rw<b2PogoJoint_GetRestLength, b2PogoJoint_SetRestLength>("rest_length")
                .rw<b2PogoJoint_GetSpringHertz, b2PogoJoint_SetSpringHertz>("spring_hertz")
                .rw<b2PogoJoint_GetSpringDampingRatio, b2PogoJoint_SetSpringDampingRatio>("spring_damping_ratio")
                .ro<b2PogoJoint_GetCurrentLength>("current_length")
                .ro<b2PogoJoint_GetCurrentSpeed>("current_speed")
                .ro<b2PogoJoint_GetImpulse>("impulse");
        }

        // ---- prismatic ---------------------------------------------------------------------
        {
            auto c = joint_class<PrismaticJoint>(m, "PrismaticJoint");
            JointBinder<PrismaticJoint> b(c);
            b.rw<b2PrismaticJoint_GetTargetTranslation, b2PrismaticJoint_SetTargetTranslation>("target_translation")
                .ro<b2PrismaticJoint_GetCurrentTranslation>("current_translation")
                .ro<b2PrismaticJoint_GetCurrentSpeed>("current_speed");
            bind_spring<
                b2PrismaticJoint_IsSpringEnabled,
                b2PrismaticJoint_EnableSpring,
                b2PrismaticJoint_GetSpringHertz,
                b2PrismaticJoint_SetSpringHertz,
                b2PrismaticJoint_GetSpringDampingRatio,
                b2PrismaticJoint_SetSpringDampingRatio>(b);
            bind_limit<
                b2PrismaticJoint_IsLimitEnabled,
                b2PrismaticJoint_EnableLimit,
                b2PrismaticJoint_SetLimits,
                b2PrismaticJoint_GetLowerLimit,
                b2PrismaticJoint_GetUpperLimit>(b);
            bind_motor<
                b2PrismaticJoint_IsMotorEnabled,
                b2PrismaticJoint_EnableMotor,
                b2PrismaticJoint_GetTargetMotorSpeed,
                b2PrismaticJoint_SetTargetMotorSpeed,
                b2PrismaticJoint_GetMaxMotorForce,
                b2PrismaticJoint_SetMaxMotorForce,
                b2PrismaticJoint_GetCurrentMotorForce>(b, "max_motor_force", "current_motor_force");
        }

        // ---- revolute ----------------------------------------------------------------------
        {
            auto c = joint_class<RevoluteJoint>(m, "RevoluteJoint");
            JointBinder<RevoluteJoint> b(c);
            b.rw<b2RevoluteJoint_GetTargetAngle, b2RevoluteJoint_SetTargetAngle>("target_angle")
                .ro<b2RevoluteJoint_GetCurrentAngle>("current_angle")
                .ro<b2RevoluteJoint_GetCurrentSpeed>("current_speed");
            bind_spring<
                b2RevoluteJoint_IsSpringEnabled,
                b2RevoluteJoint_EnableSpring,
                b2RevoluteJoint_GetSpringHertz,
                b2RevoluteJoint_SetSpringHertz,
                b2RevoluteJoint_GetSpringDampingRatio,
                b2RevoluteJoint_SetSpringDampingRatio>(b);
            bind_limit<
                b2RevoluteJoint_IsLimitEnabled,
                b2RevoluteJoint_EnableLimit,
                b2RevoluteJoint_SetLimits,
                b2RevoluteJoint_GetLowerLimit,
                b2RevoluteJoint_GetUpperLimit>(b);
            bind_motor<
                b2RevoluteJoint_IsMotorEnabled,
                b2RevoluteJoint_EnableMotor,
                b2RevoluteJoint_GetTargetMotorSpeed,
                b2RevoluteJoint_SetTargetMotorSpeed,
                b2RevoluteJoint_GetMaxMotorTorque,
                b2RevoluteJoint_SetMaxMotorTorque,
                b2RevoluteJoint_GetCurrentMotorTorque>(b, "max_motor_torque", "current_motor_torque");
        }

        // ---- weld --------------------------------------------------------------------------
        {
            auto c = joint_class<WeldJoint>(m, "WeldJoint");
            JointBinder<WeldJoint>(c)
                .rw<b2WeldJoint_GetLinearHertz, b2WeldJoint_SetLinearHertz>("linear_hertz")
                .rw<b2WeldJoint_GetLinearDampingRatio, b2WeldJoint_SetLinearDampingRatio>("linear_damping_ratio")
                .rw<b2WeldJoint_GetAngularHertz, b2WeldJoint_SetAngularHertz>("angular_hertz")
                .rw<b2WeldJoint_GetAngularDampingRatio, b2WeldJoint_SetAngularDampingRatio>("angular_damping_ratio");
        }

        // ---- wheel -------------------------------------------------------------------------
        {
            auto c = joint_class<WheelJoint>(m, "WheelJoint");
            JointBinder<WheelJoint> b(c);
            bind_spring<
                b2WheelJoint_IsSpringEnabled,
                b2WheelJoint_EnableSpring,
                b2WheelJoint_GetSpringHertz,
                b2WheelJoint_SetSpringHertz,
                b2WheelJoint_GetSpringDampingRatio,
                b2WheelJoint_SetSpringDampingRatio>(b);
            bind_limit<
                b2WheelJoint_IsLimitEnabled,
                b2WheelJoint_EnableLimit,
                b2WheelJoint_SetLimits,
                b2WheelJoint_GetLowerLimit,
                b2WheelJoint_GetUpperLimit>(b);
            bind_motor<
                b2WheelJoint_IsMotorEnabled,
                b2WheelJoint_EnableMotor,
                b2WheelJoint_GetTargetMotorSpeed,
                b2WheelJoint_SetTargetMotorSpeed,
                b2WheelJoint_GetMaxMotorTorque,
                b2WheelJoint_SetMaxMotorTorque,
                b2WheelJoint_GetCurrentMotorTorque>(b, "max_motor_torque", "current_motor_torque");
        }
    }
}  // namespace pyb2d3::bind
