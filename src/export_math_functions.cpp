#include <nanobind/nanobind.h>

// stl conversion
// #include <nanobind/stl/arr
#include <iostream>

#include <pyb2d3/py_converter.hpp>
// C
// extern "C"
// {
#include <box2d/box2d.h>
// #include <box2d/math_functions.h>
// }

// nanobind namespace
namespace py = nanobind;

void export_math_functions(py::module_& m)
{
    py::class_<b2Transform>(m, "Transform")
        //.def(py::init<>())
        .def(
            "__init__",
            [](b2Transform* t)
            {
                new (t) b2Transform();
                *t = b2Transform_identity;
            }
        )
        // .def("__init__", [](b2Transform* t, b2Vec2 p)
        //     {
        //         new (t) b2Transform();
        //         t->p = p;
        //         t->q = q;
        //     }
        //     ,
        //     // py::arg("p") = b2Vec2{0.0f, 0.0f}//,
        //     // py::arg("q") = b2Rot{1.0f, 0.0f}
        // )

        .def_rw("p", &b2Transform::p)
        .def_rw("q", &b2Transform::q)
        .def(
            "transform_point",
            [](b2Transform& t, b2Vec2 p)
            {
                return b2TransformPoint(t, p);
            }
        )
        .def(
            "inv_transform_point",
            [](b2Transform& t, b2Vec2 p)
            {
                return b2InvTransformPoint(t, p);
            }
        );


    py::class_<b2Rot>(m, "Rot")
        .def(
            "__init__",
            [](b2Rot* t, double rad)
            {
                new (t) b2Rot();
                t->s = sin(rad);
                t->c = cos(rad);
            }
        )
        .def(
            "__init__",
            [](b2Rot* t)
            {
                new (t) b2Rot();
                t->s = 0.0;
                t->c = 1.0;
            }
        )
        .def_rw("c", &b2Rot::c)
        .def_rw("s", &b2Rot::s);

    py::class_<b2AABB>(m, "AABB")
        .def(py::init<>())
        .def_rw("lower_bound", &b2AABB::lowerBound)
        .def_rw("upper_bound", &b2AABB::upperBound)
        .def(
            "center",
            [](b2AABB& a)
            {
                return b2AABB_Center(a);
            }
        )
        .def(
            "contains",
            [](b2AABB& a, b2AABB& b)
            {
                return b2AABB_Contains(a, b);
            }
        )
        .def(
            "is_valid",
            [](b2AABB& a)
            {
                return b2IsValidAABB(a);
            }
        )

        ;

    py::class_<b2Plane>(m, "Plane")
        .def(py::init<>())
        .def_rw("normal", &b2Plane::normal)
        .def_rw("offset", &b2Plane::offset);

    m.def(
        "add",
        [](b2Vec2 a, b2Vec2 b)
        {
            return a + b;
        }
    );

    m.def(
        "dot",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Dot(a, b);
        }
    );

    m.def(
        "cross",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Cross(a, b);
        }
    );

    m.def(
        "cross_vs",
        [](b2Vec2 v, float s)
        {
            return b2CrossVS(v, s);
        }
    );

    m.def(
        "cross_sv",
        [](float s, b2Vec2 v)
        {
            return b2CrossSV(s, v);
        }
    );

    m.def(
        "left_perp",
        [](b2Vec2 v)
        {
            return b2LeftPerp(v);
        }
    );

    m.def(
        "right_perp",
        [](b2Vec2 v)
        {
            return b2RightPerp(v);
        }
    );

    m.def(
        "add",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Add(a, b);
        }
    );

    m.def(
        "sub",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Sub(a, b);
        }
    );

    m.def(
        "neg",
        [](b2Vec2 a)
        {
            return b2Neg(a);
        }
    );

    m.def(
        "lerp",
        [](b2Vec2 a, b2Vec2 b, float t)
        {
            return b2Lerp(a, b, t);
        }
    );

    m.def(
        "mul",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Mul(a, b);
        }
    );

    m.def(
        "mul_sv",
        [](float s, b2Vec2 v)
        {
            return b2MulSV(s, v);
        }
    );

    m.def(
        "mul_add",
        [](b2Vec2 a, float s, b2Vec2 b)
        {
            return b2MulAdd(a, s, b);
        }
    );

    m.def(
        "mul_sub",
        [](b2Vec2 a, float s, b2Vec2 b)
        {
            return b2MulSub(a, s, b);
        }
    );

    m.def(
        "abs",
        [](b2Vec2 a)
        {
            return b2Abs(a);
        }
    );

    m.def(
        "min",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Min(a, b);
        }
    );

    m.def(
        "max",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Max(a, b);
        }
    );

    m.def(
        "clamp",
        [](b2Vec2 v, b2Vec2 a, b2Vec2 b)
        {
            return b2Clamp(v, a, b);
        }
    );

    m.def(
        "length",
        [](b2Vec2 v)
        {
            return b2Length(v);
        }
    );

    m.def(
        "distance",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Distance(a, b);
        }
    );

    m.def(
        "normalize",
        [](b2Vec2 v)
        {
            return b2Normalize(v);
        }
    );

    m.def(
        "get_length_and_normalize",
        [](float* length, b2Vec2 v)
        {
            return b2GetLengthAndNormalize(length, v);
        }
    );

    m.def(
        "normalize_rot",
        [](b2Rot q)
        {
            return b2NormalizeRot(q);
        }
    );

    m.def(
        "integrate_rotation",
        [](b2Rot q1, float deltaAngle)
        {
            return b2IntegrateRotation(q1, deltaAngle);
        }
    );

    m.def(
        "mul_sv",
        [](float s, b2Vec2 v)
        {
            return b2MulSV(s, v);
        }
    );

    m.def(
        "mul_add",
        [](b2Vec2 a, float s, b2Vec2 b)
        {
            return b2MulAdd(a, s, b);
        }
    );

    m.def(
        "mul_sub",
        [](b2Vec2 a, float s, b2Vec2 b)
        {
            return b2MulSub(a, s, b);
        }
    );

    m.def(
        "abs",
        [](b2Vec2 a)
        {
            return b2Abs(a);
        }
    );

    m.def(
        "min",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Min(a, b);
        }
    );

    m.def(
        "max",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Max(a, b);
        }
    );

    m.def(
        "clamp",
        [](b2Vec2 v, b2Vec2 a, b2Vec2 b)
        {
            return b2Clamp(v, a, b);
        }
    );

    m.def(
        "length",
        [](b2Vec2 v)
        {
            return b2Length(v);
        }
    );

    m.def(
        "distance",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Distance(a, b);
        }
    );

    m.def(
        "normalize",
        [](b2Vec2 v)
        {
            return b2Normalize(v);
        }
    );

    m.def(
        "get_length_and_normalize",
        [](float* length, b2Vec2 v)
        {
            return b2GetLengthAndNormalize(length, v);
        }
    );

    m.def(
        "normalize_rot",
        [](b2Rot q)
        {
            return b2NormalizeRot(q);
        }
    );

    m.def(
        "integrate_rotation",
        [](b2Rot q1, float deltaAngle)
        {
            return b2IntegrateRotation(q1, deltaAngle);
        }
    );

    m.def(
        "mul",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Mul(a, b);
        }
    );

    m.def(
        "mul_sv",
        [](float s, b2Vec2 v)
        {
            return b2MulSV(s, v);
        }
    );

    m.def(
        "mul_add",
        [](b2Vec2 a, float s, b2Vec2 b)
        {
            return b2MulAdd(a, s, b);
        }
    );

    m.def(
        "mul_sub",
        [](b2Vec2 a, float s, b2Vec2 b)
        {
            return b2MulSub(a, s, b);
        }
    );

    m.def(
        "abs",
        [](b2Vec2 a)
        {
            return b2Abs(a);
        }
    );

    m.def(
        "min",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Min(a, b);
        }
    );

    m.def(
        "max",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Max(a, b);
        }
    );

    m.def(
        "clamp",
        [](b2Vec2 v, b2Vec2 a, b2Vec2 b)
        {
            return b2Clamp(v, a, b);
        }
    );

    m.def(
        "length",
        [](b2Vec2 v)
        {
            return b2Length(v);
        }
    );

    m.def(
        "distance",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2Distance(a, b);
        }
    );

    m.def(
        "normalize",
        [](b2Vec2 v)
        {
            return b2Normalize(v);
        }
    );

    m.def(
        "get_length_and_normalize",
        [](float* length, b2Vec2 v)
        {
            return b2GetLengthAndNormalize(length, v);
        }
    );

    m.def(
        "normalize_rot",
        [](b2Rot q)
        {
            return b2NormalizeRot(q);
        }
    );

    m.def(
        "integrate_rotation",
        [](b2Rot q1, float deltaAngle)
        {
            return b2IntegrateRotation(q1, deltaAngle);
        }
    );

    m.def(
        "length_squared",
        [](b2Vec2 v)
        {
            return b2LengthSquared(v);
        }
    );

    m.def(
        "distance_squared",
        [](b2Vec2 a, b2Vec2 b)
        {
            return b2DistanceSquared(a, b);
        }
    );

    m.def(
        "make_rot",
        [](float angle)
        {
            return b2MakeRot(angle);
        }
    );

    m.def(
        "compute_rotation_between_unit_vectors",
        [](b2Vec2 v1, b2Vec2 v2)
        {
            return b2ComputeRotationBetweenUnitVectors(v1, v2);
        }
    );

    m.def(
        "is_normalized",
        [](b2Vec2 v)
        {
            return b2IsNormalized(v);
        }
    );

    m.def(
        "is_normalized_rot",
        [](b2Rot q)
        {
            return b2IsNormalizedRot(q);
        }
    );

    m.def(
        "nlerp",
        [](b2Rot q1, b2Rot q2, float t)
        {
            return b2NLerp(q1, q2, t);
        }
    );

    m.def(
        "compute_angular_velocity",
        [](b2Rot q1, b2Rot q2, float inv_h)
        {
            return b2ComputeAngularVelocity(q1, q2, inv_h);
        }
    );

    m.def(
        "get_angle",
        [](b2Rot q)
        {
            return b2Rot_GetAngle(q);
        }
    );

    m.def(
        "get_x_axis",
        [](b2Rot q)
        {
            return b2Rot_GetXAxis(q);
        }
    );

    m.def(
        "get_y_axis",
        [](b2Rot q)
        {
            return b2Rot_GetYAxis(q);
        }
    );

    m.def(
        "mul_rot",
        [](b2Rot q, b2Rot r)
        {
            return b2MulRot(q, r);
        }
    );

    m.def(
        "inv_mul_rot",
        [](b2Rot q, b2Rot r)
        {
            return b2InvMulRot(q, r);
        }
    );

    m.def(
        "relative_angle",
        [](b2Rot b, b2Rot a)
        {
            return b2RelativeAngle(b, a);
        }
    );

    m.def(
        "unwind_angle",
        [](float angle)
        {
            return b2UnwindAngle(angle);
        }
    );

    m.def(
        "rotate_vector",
        [](b2Rot q, b2Vec2 v)
        {
            return b2RotateVector(q, v);
        }
    );

    m.def(
        "inv_rotate_vector",
        [](b2Rot q, b2Vec2 v)
        {
            return b2InvRotateVector(q, v);
        }
    );

    m.def(
        "transform_point",
        [](b2Transform t, b2Vec2 p)
        {
            return b2TransformPoint(t, p);
        }
    );

    m.def(
        "inv_transform_point",
        [](b2Transform t, b2Vec2 p)
        {
            return b2InvTransformPoint(t, p);
        }
    );

    m.def(
        "mul_transforms",
        [](b2Transform A, b2Transform B)
        {
            return b2MulTransforms(A, B);
        }
    );

    m.def(
        "inv_mul_transforms",
        [](b2Transform A, b2Transform B)
        {
            return b2InvMulTransforms(A, B);
        }
    );

    m.def(
        "mul_mv",
        [](b2Mat22 A, b2Vec2 v)
        {
            return b2MulMV(A, v);
        }
    );

    m.def(
        "get_inverse22",
        [](b2Mat22 A)
        {
            return b2GetInverse22(A);
        }
    );

    m.def(
        "solve22",
        [](b2Mat22 A, b2Vec2 b)
        {
            return b2Solve22(A, b);
        }
    );

    m.def(
        "contains",
        [](b2AABB a, b2AABB b)
        {
            return b2AABB_Contains(a, b);
        }
    );

    m.def(
        "center",
        [](b2AABB a)
        {
            return b2AABB_Center(a);
        }
    );

    m.def(
        "extents",
        [](b2AABB a)
        {
            return b2AABB_Extents(a);
        }
    );

    m.def(
        "union",
        [](b2AABB a, b2AABB b)
        {
            return b2AABB_Union(a, b);
        }
    );

    m.def(
        "set_length_units_per_meter",
        [](float lengthUnits)
        {
            return b2SetLengthUnitsPerMeter(lengthUnits);
        }
    );

    nb::implicitly_convertible<double, b2Rot>();


    m.def(
        "mid_point",
        [](b2Vec2 p1, b2Vec2 p2)
        {
            return (p1 + p2) * 0.5f;
        }
    );


    // some additional functions that are not in the original Box2D
    m.def(
        "mid_point_squared_distance",
        [](b2Vec2 p1, b2Vec2 p2, b2Vec2 p3)
        {
            // compute the squared distance between the mid point of p1 and p2 and p3
            b2Vec2 mid = (p1 + p2) * 0.5f;
            return b2DistanceSquared(mid, p3);
        }
    );

    m.def(
        "mid_point_distance",
        [](b2Vec2 p1, b2Vec2 p2, b2Vec2 p3)
        {
            // compute the squared distance between the mid point of p1 and p2 and p3
            b2Vec2 mid = (p1 + p2) * 0.5f;
            return b2Distance(mid, p3);
        }
    );
};
