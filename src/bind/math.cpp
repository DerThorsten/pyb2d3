#include <cmath>
#include <tuple>

#include <box2d/math_functions.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/tuple.h>

#include "bind.hpp"
#include "pyb2d3/core/points.hpp"
#include "pyb2d3/py_converter.hpp"

namespace pyb2d3::bind
{
    void export_math(nb::module_& m)
    {
        // ---- types ------------------------------------------------------------------------
        nb::class_<b2Rot>(m, "Rot")
            .def(
                "__init__",
                [](b2Rot* t, float radians)
                {
                    new (t) b2Rot(b2MakeRot(radians));
                },
                nb::arg("radians") = 0.0f
            )
            .def_rw("c", &b2Rot::c)
            .def_rw("s", &b2Rot::s)
            .def_prop_ro("angle", &b2Rot_GetAngle)
            .def_prop_ro("x_axis", &b2Rot_GetXAxis)
            .def_prop_ro("y_axis", &b2Rot_GetYAxis)
            .def("inverse", &b2InvertRot)
            .def(
                "__repr__",
                [](const b2Rot& q)
                {
                    return nb::str("Rot(angle={})").format(b2Rot_GetAngle(q));
                }
            );
        // a float (radians) is accepted wherever a Rot is expected
        nb::implicitly_convertible<float, b2Rot>();

        nb::class_<b2Transform>(m, "Transform")
            .def(
                "__init__",
                [](b2Transform* t, b2Vec2 p, b2Rot q)
                {
                    new (t) b2Transform{p, q};
                },
                nb::arg("p") = b2Vec2{0.0f, 0.0f},
                nb::arg("q") = b2Rot_identity
            )
            .def_rw("p", &b2Transform::p)
            .def_rw("q", &b2Transform::q)
            .def("transform_point", &b2TransformPoint, nb::arg("point"))
            .def("inv_transform_point", &b2InvTransformPoint, nb::arg("point"))
            .def(
                "__repr__",
                [](const b2Transform& t)
                {
                    return nb::str("Transform(p=({}, {}), angle={})").format(t.p.x, t.p.y, b2Rot_GetAngle(t.q));
                }
            );

        nb::class_<b2Mat22>(m, "Mat22")
            .def(
                "__init__",
                [](b2Mat22* t, b2Vec2 cx, b2Vec2 cy)
                {
                    new (t) b2Mat22{cx, cy};
                },
                nb::arg("cx") = b2Vec2{1.0f, 0.0f},
                nb::arg("cy") = b2Vec2{0.0f, 1.0f}
            )
            .def_rw("cx", &b2Mat22::cx)
            .def_rw("cy", &b2Mat22::cy);

        nb::class_<b2AABB>(m, "AABB")
            .def(
                "__init__",
                [](b2AABB* t, b2Vec2 lower, b2Vec2 upper)
                {
                    new (t) b2AABB{lower, upper};
                },
                nb::arg("lower_bound") = b2Vec2{0.0f, 0.0f},
                nb::arg("upper_bound") = b2Vec2{0.0f, 0.0f}
            )
            .def_rw("lower_bound", &b2AABB::lowerBound)
            .def_rw("upper_bound", &b2AABB::upperBound)
            .def("center", &b2AABB_Center)
            .def("extents", &b2AABB_Extents)
            .def("contains", &b2AABB_Contains, nb::arg("other"))
            .def("overlaps", &b2AABB_Overlaps, nb::arg("other"))
            .def("union", &b2AABB_Union, nb::arg("other"))
            .def("is_valid", &b2IsValidAABB);

        nb::class_<b2Plane>(m, "Plane")
            .def(nb::init<>())
            .def_rw("normal", &b2Plane::normal)
            .def_rw("offset", &b2Plane::offset);

        nb::class_<b2CosSin>(m, "CosSin").def_ro("cosine", &b2CosSin::cosine).def_ro("sine", &b2CosSin::sine);

        // ---- scalar --------------------------------------------------------------------------
        m.def("atan2", &b2Atan2, nb::arg("y"), nb::arg("x"));
        m.def("compute_cos_sin", &b2ComputeCosSin, nb::arg("radians"));
        m.def("unwind_angle", &b2UnwindAngle, nb::arg("radians"));
        m.def(
            "spring_damper",
            &b2SpringDamper,
            nb::arg("hertz"),
            nb::arg("damping_ratio"),
            nb::arg("position"),
            nb::arg("velocity"),
            nb::arg("time_step")
        );

        // ---- vectors -------------------------------------------------------------------------
        m.def("add", &b2Add, nb::arg("a"), nb::arg("b"));
        m.def("sub", &b2Sub, nb::arg("a"), nb::arg("b"));
        m.def("neg", &b2Neg, nb::arg("a"));
        m.def("dot", &b2Dot, nb::arg("a"), nb::arg("b"));
        m.def("cross", &b2Cross, nb::arg("a"), nb::arg("b"));
        m.def("cross_vs", &b2CrossVS, nb::arg("v"), nb::arg("s"));
        m.def("cross_sv", &b2CrossSV, nb::arg("s"), nb::arg("v"));
        m.def("left_perp", &b2LeftPerp, nb::arg("v"));
        m.def("right_perp", &b2RightPerp, nb::arg("v"));
        m.def("lerp", &b2Lerp, nb::arg("a"), nb::arg("b"), nb::arg("t"));
        m.def("mul", &b2Mul, nb::arg("a"), nb::arg("b"));
        m.def("mul_sv", &b2MulSV, nb::arg("s"), nb::arg("v"));
        m.def("mul_add", &b2MulAdd, nb::arg("a"), nb::arg("s"), nb::arg("b"));
        m.def("mul_sub", &b2MulSub, nb::arg("a"), nb::arg("s"), nb::arg("b"));
        m.def("abs", &b2Abs, nb::arg("a"));
        m.def("min", &b2Min, nb::arg("a"), nb::arg("b"));
        m.def("max", &b2Max, nb::arg("a"), nb::arg("b"));
        m.def("clamp", &b2Clamp, nb::arg("v"), nb::arg("a"), nb::arg("b"));
        m.def("length", &b2Length, nb::arg("v"));
        m.def("length_squared", &b2LengthSquared, nb::arg("v"));
        m.def("distance", &b2Distance, nb::arg("a"), nb::arg("b"));
        m.def("distance_squared", &b2DistanceSquared, nb::arg("a"), nb::arg("b"));
        m.def("normalize", &b2Normalize, nb::arg("v"));
        m.def("is_normalized", &b2IsNormalized, nb::arg("v"));
        m.def(
            "get_length_and_normalize",
            [](b2Vec2 v)
            {
                float length = 0.0f;
                b2Vec2 n = b2GetLengthAndNormalize(&length, v);
                return std::make_tuple(length, n);
            },
            nb::arg("v")
        );
        m.def(
            "mid_point",
            [](b2Vec2 a, b2Vec2 b)
            {
                return b2Lerp(a, b, 0.5f);
            },
            nb::arg("a"),
            nb::arg("b")
        );

        // ---- rotations -----------------------------------------------------------------------
        m.def("make_rot", &b2MakeRot, nb::arg("radians"));
        m.def("make_rot_from_unit_vector", &b2MakeRotFromUnitVector, nb::arg("unit_vector"));
        m.def("compute_rotation_between_unit_vectors", &b2ComputeRotationBetweenUnitVectors, nb::arg("v1"), nb::arg("v2"));
        m.def("normalize_rot", &b2NormalizeRot, nb::arg("q"));
        m.def("is_normalized_rot", &b2IsNormalizedRot, nb::arg("q"));
        m.def("invert_rot", &b2InvertRot, nb::arg("q"));
        m.def("integrate_rotation", &b2IntegrateRotation, nb::arg("q"), nb::arg("delta_angle"));
        m.def("nlerp", &b2NLerp, nb::arg("q1"), nb::arg("q2"), nb::arg("t"));
        m.def("compute_angular_velocity", &b2ComputeAngularVelocity, nb::arg("q1"), nb::arg("q2"), nb::arg("inv_h"));
        m.def("rot_get_angle", &b2Rot_GetAngle, nb::arg("q"));
        m.def("mul_rot", &b2MulRot, nb::arg("q"), nb::arg("r"));
        m.def("inv_mul_rot", &b2InvMulRot, nb::arg("q"), nb::arg("r"));
        m.def("relative_angle", &b2RelativeAngle, nb::arg("a"), nb::arg("b"));
        m.def("rotate_vector", &b2RotateVector, nb::arg("q"), nb::arg("v"));
        m.def("inv_rotate_vector", &b2InvRotateVector, nb::arg("q"), nb::arg("v"));

        // ---- transforms / matrices -----------------------------------------------------------
        m.def("transform_point", &b2TransformPoint, nb::arg("t"), nb::arg("p"));
        m.def("inv_transform_point", &b2InvTransformPoint, nb::arg("t"), nb::arg("p"));
        m.def("mul_transforms", &b2MulTransforms, nb::arg("a"), nb::arg("b"));
        m.def("inv_mul_transforms", &b2InvMulTransforms, nb::arg("a"), nb::arg("b"));
        m.def("mul_mv", &b2MulMV, nb::arg("a"), nb::arg("v"));
        m.def("get_inverse22", &b2GetInverse22, nb::arg("a"));
        m.def("solve22", &b2Solve22, nb::arg("a"), nb::arg("b"));

        // ---- bounds / planes -----------------------------------------------------------------
        m.def(
            "make_aabb",
            [](const Points& points, float radius)
            {
                if (points.size() == 0)
                {
                    throw nb::value_error("make_aabb needs at least one point");
                }
                return b2MakeAABB(points.data(), points.count(), radius);
            },
            nb::arg("points"),
            nb::arg("radius") = 0.0f
        );
        m.def("plane_separation", &b2PlaneSeparation, nb::arg("plane"), nb::arg("point"));

        // ---- validation ----------------------------------------------------------------------
        m.def("is_valid_float", &b2IsValidFloat, nb::arg("a"));
        m.def("is_valid_vec2", &b2IsValidVec2, nb::arg("v"));
        m.def("is_valid_rot", &b2IsValidRot, nb::arg("q"));
        m.def("is_valid_transform", &b2IsValidTransform, nb::arg("t"));
        m.def("is_valid_aabb", &b2IsValidAABB, nb::arg("aabb"));
        m.def("is_valid_plane", &b2IsValidPlane, nb::arg("plane"));
    }
}  // namespace pyb2d3::bind
