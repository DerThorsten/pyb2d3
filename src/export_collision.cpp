#include <iostream>

#include <nanobind/make_iterator.h>
#include <nanobind/nanobind.h>

// stl conversion
// #include <nanobind/stl/arr

#include <pyb2d3/py_converter.hpp>

// C
// extern "C"
// {
#include <box2d/box2d.h>
#include <box2d/math_functions.h>
// }

// nanobind namespace
namespace py = nanobind;

void export_collision(py::module_& m)
{
    // b2ShapeProxy
    py::class_<b2ShapeProxy>(m, "ShapeProxy")
        .def(py::init<>())
        .def_prop_rw(
            "points",
            [](b2ShapeProxy* self)
            {
                return ArrayVec2(
                    reinterpret_cast<float*>(self->points),     // data
                    {std::size_t(self->count), std::size_t(2)}  // shape
                );
            },
            [](b2ShapeProxy* self, ArrayVec2 value)
            {
                self->count = value.size();
                for (int i = 0; i < value.size(); i++)
                {
                    self->points[i].x = value(i, 0);
                    self->points[i].y = value(i, 1);
                }
            }
        )
        .def_ro("count", &b2ShapeProxy::count)
        .def_rw("radius", &b2ShapeProxy::radius);


    py::class_<b2RayCastInput>(m, "RayCastInput")
        .def_rw("origin", &b2RayCastInput::origin)
        .def_rw("translation", &b2RayCastInput::translation)
        .def_rw("max_fraction", &b2RayCastInput::maxFraction);

    // b2CastOutput
    py::class_<b2CastOutput>(m, "CastOutput")
        .def(py::init<>())
        .def_rw("normal", &b2CastOutput::normal)
        .def_rw("point", &b2CastOutput::point)
        .def_rw("fraction", &b2CastOutput::fraction)
        .def_rw("iterations", &b2CastOutput::iterations)
        .def_rw("hit", &b2CastOutput::hit);

    // b2MassData
    py::class_<b2MassData>(m, "MassData")
        .def(py::init<>())
        .def_rw("mass", &b2MassData::mass)
        .def_rw("center", &b2MassData::center)
        .def_rw("rotational_inertia", &b2MassData::rotationalInertia);

    // b2Circle
    py::class_<b2Circle>(m, "Circle")
        .def(py::init<>())
        .def_rw("center", &b2Circle::center)
        .def_rw("radius", &b2Circle::radius);

    // b2Capsule
    py::class_<b2Capsule>(m, "Capsule")
        .def(py::init<>())
        .def_rw("center1", &b2Capsule::center1)
        .def_rw("center2", &b2Capsule::center2)
        .def_rw("radius", &b2Capsule::radius);

    // b2Polygon
    py::class_<b2Polygon>(m, "Polygon")
        .def(py::init<>())
        .def_prop_rw(
            "vertices",
            [](b2Polygon* self)
            {
                return ArrayVec2(
                    reinterpret_cast<float*>(self->vertices),   // data
                    {std::size_t(self->count), std::size_t(2)}  // shape
                );
            },
            [](b2Polygon* self, ArrayVec2 value)
            {
                self->count = value.size();
                for (int i = 0; i < value.size(); i++)
                {
                    self->vertices[i].x = value(i, 0);
                    self->vertices[i].y = value(i, 1);
                }
            }
        )
        .def_prop_rw(
            "normals",
            [](b2Polygon* self)
            {
                return ArrayVec2(
                    reinterpret_cast<float*>(self->normals),    // data
                    {std::size_t(self->count), std::size_t(2)}  // shape
                );
            },
            [](b2Polygon* self, ArrayVec2 value)
            {
                self->count = value.size();
                for (int i = 0; i < value.size(); i++)
                {
                    self->normals[i].x = value(i, 0);
                    self->normals[i].y = value(i, 1);
                }
            }
        )
        .def_rw("centroid", &b2Polygon::centroid)
        .def_rw("radius", &b2Polygon::radius)
        .def_ro("count", &b2Polygon::count);

    // b2Segment
    py::class_<b2Segment>(m, "Segment")
        .def(py::init<>())
        .def_rw("point1", &b2Segment::point1)
        .def_rw("point2", &b2Segment::point2);

    // b2ChainSegment
    py::class_<b2ChainSegment>(m, "ChainSegment")
        .def(py::init<>())
        .def_rw("ghost1", &b2ChainSegment::ghost1)
        .def_rw("segment", &b2ChainSegment::segment)
        .def_rw("ghost2", &b2ChainSegment::ghost2);

    m.def("is_valid_ray", &b2IsValidRay, py::arg("input"));
    m.def("_make_polygon", &b2MakePolygon, py::arg("hull"), py::arg("radius"));
    m.def("_make_offset_polygon", &b2MakeOffsetPolygon, py::arg("hull"), py::arg("position"), py::arg("rotation"));
    m.def(
        "_make_offset_rounded_polygon",
        &b2MakeOffsetRoundedPolygon,
        py::arg("hull"),
        py::arg("position"),
        py::arg("rotation"),
        py::arg("radius")
    );

    m.def("square", &b2MakeSquare, py::arg("h"));
    m.def("_make_box", &b2MakeBox, py::arg("hx"), py::arg("hy"));
    m.def("_make_rounded_box", &b2MakeRoundedBox, py::arg("hx"), py::arg("hy"), py::arg("radius"));
    m.def("_make_offset_box", &b2MakeOffsetBox, py::arg("hx"), py::arg("hy"), py::arg("center"), py::arg("rotation"));
    m.def(
        "make_offset_rounded_box",
        &b2MakeOffsetRoundedBox,
        py::arg("hx"),
        py::arg("hy"),
        py::arg("center"),
        py::arg("rotation"),
        py::arg("radius")
    );

#if 0
    // we dont need these in that form.
    // if we want to use them, wrap them in the respective classes
    m.def("transform_polygon", &b2TransformPolygon, py::arg("transform"), py::arg("polygon"));
    m.def("compute_circle_mass", &b2ComputeCircleMass, py::arg("shape"), py::arg("density"));
    m.def("compute_capsule_mass", &b2ComputeCapsuleMass, py::arg("shape"), py::arg("density"));
    m.def("compute_polygon_mass", &b2ComputePolygonMass, py::arg("shape"), py::arg("density"));
    m.def("compute_circle_aabb", &b2ComputeCircleAABB, py::arg("shape"), py::arg("transform"));
    m.def("compute_capsule_aabb", &b2ComputeCapsuleAABB, py::arg("shape"), py::arg("transform"));
    m.def("compute_polygon_aabb", &b2ComputePolygonAABB, py::arg("shape"), py::arg("transform"));
    m.def("compute_segment_aabb", &b2ComputeSegmentAABB, py::arg("shape"), py::arg("transform"));
    m.def("point_in_circle", &b2PointInCircle, py::arg("point"), py::arg("shape"));
    m.def("point_in_capsule", &b2PointInCapsule, py::arg("point"), py::arg("shape"));
    m.def("point_in_polygon", &b2PointInPolygon, py::arg("point"), py::arg("shape"));
    m.def("ray_cast_circle", &b2RayCastCircle, py::arg("input"), py::arg("shape"));
    m.def("ray_cast_capsule", &b2RayCastCapsule, py::arg("input"), py::arg("shape"));
    m.def("ray_cast_segment", &b2RayCastSegment, py::arg("input"), py::arg("shape"), py::arg("one_sided"));
    m.def("ray_cast_polygon", &b2RayCastPolygon, py::arg("input"), py::arg("shape"));
    m.def("shape_cast_circle", &b2ShapeCastCircle, py::arg("input"), py::arg("shape"));
    m.def("shape_cast_capsule", &b2ShapeCastCapsule, py::arg("input"), py::arg("shape"));
    m.def("shape_cast_segment", &b2ShapeCastSegment, py::arg("input"), py::arg("shape"));
    m.def("shape_cast_polygon", &b2ShapeCastPolygon, py::arg("input"), py::arg("shape"));
#endif

    // b2Hull
    py::class_<b2Hull>(m, "Hull")
        .def(py::init<>())
        .def_prop_rw(
            "points",
            [](b2Hull* self)
            {
                return ArrayVec2(
                    reinterpret_cast<float*>(self->points),
                    {std::size_t(self->count), std::size_t(2)}  // shape
                );
            },
            [](b2Hull* self, ArrayVec2 value)
            {
                self->count = value.size();
                for (int i = 0; i < value.size(); i++)
                {
                    self->points[i].x = value(i, 0);
                    self->points[i].y = value(i, 1);
                }
            }
        )
        .def(
            "validate",
            [](b2Hull* self)
            {
                return b2ValidateHull(self);
            }
        )
        .def_ro("count", &b2Hull::count);

    m.def(
        "compute_hull",
        [](ArrayVec2 points)
        {
            b2Hull hull = b2ComputeHull(reinterpret_cast<b2Vec2*>(points.data()), points.shape(0));
            return hull;
        },
        py::arg("points")
    );

    // m.def("validate_hull", &b2ValidateHull, py::arg("hull"));

#if 0
    // b2SegmentDistanceResult
    py::class_<b2SegmentDistanceResult>(m, "SegmentDistanceResult")
        .def(py::init<>())
        .def_rw("closest1", &b2SegmentDistanceResult::closest1)
        .def_rw("closest2", &b2SegmentDistanceResult::closest2)
        .def_rw("fraction1", &b2SegmentDistanceResult::fraction1)
        .def_rw("fraction2", &b2SegmentDistanceResult::fraction2)
        .def_rw("distanceSquared", &b2SegmentDistanceResult::distanceSquared);

    // b2SegmentDistance
    m.def("segment_distance", &b2SegmentDistance, py::arg("p1"), py::arg("q1"), py::arg("p2"), py::arg("q2"));

    // b2DistanceOutput
    py::class_<b2DistanceOutput>(m, "DistanceOutput")
        .def(py::init<>())
        .def_rw("pointA", &b2DistanceOutput::pointA)
        .def_rw("pointB", &b2DistanceOutput::pointB)
        .def_rw("distance", &b2DistanceOutput::distance)
        .def_rw("iterations", &b2DistanceOutput::iterations)
        .def_rw("simplexCount", &b2DistanceOutput::simplexCount);

    // b2SimplexVertex
    py::class_<b2SimplexVertex>(m, "SimplexVertex")
        .def(py::init<>())
        .def_rw("wA", &b2SimplexVertex::wA)
        .def_rw("wB", &b2SimplexVertex::wB)
        .def_rw("w", &b2SimplexVertex::w)
        .def_rw("a", &b2SimplexVertex::a)
        .def_rw("indexA", &b2SimplexVertex::indexA)
        .def_rw("indexB", &b2SimplexVertex::indexB);

    // b2Simplex
    py::class_<b2Simplex>(m, "Simplex")
        .def(py::init<>())
        .def_rw("v1", &b2Simplex::v1)
        .def_rw("v2", &b2Simplex::v2)
        .def_rw("v3", &b2Simplex::v3)
        .def_rw("count", &b2Simplex::count);

    // b2ShapeDistance
    m.def(
        "shape_distance",
        &b2ShapeDistance,
        py::arg("cache"),
        py::arg("input"),
        py::arg("simplexes"),
        py::arg("simplexCapacity")
    );

    // b2ShapeCastPairInput
    py::class_<b2ShapeCastPairInput>(m, "ShapeCastPairInput")
        .def(py::init<>())
        .def_rw("proxyA", &b2ShapeCastPairInput::proxyA)
        .def_rw("proxyB", &b2ShapeCastPairInput::proxyB)
        .def_rw("transformA", &b2ShapeCastPairInput::transformA)
        .def_rw("transformB", &b2ShapeCastPairInput::transformB)
        .def_rw("translationB", &b2ShapeCastPairInput::translationB)
        .def_rw("maxFraction", &b2ShapeCastPairInput::maxFraction);

    // b2ShapeCast
    m.def("shape_cast", &b2ShapeCast, py::arg("input"));
    m.def(
        "make_proxy",
        [](ArrayVec2 vertices, float radius)
        {
            return b2MakeProxy(reinterpret_cast<b2Vec2*>(vertices.data()), vertices.shape(0), radius);
        },
        py::arg("vertices"),
        py::arg("radius")
    );

    // b2Sweep
    py::class_<b2Sweep>(m, "Sweep")
        .def(py::init<>())
        .def_rw("local_center", &b2Sweep::localCenter)
        .def_rw("c1", &b2Sweep::c1)
        .def_rw("c2", &b2Sweep::c2)
        .def_rw("q1", &b2Sweep::q1)
        .def_rw("q2", &b2Sweep::q2);

    // b2GetSweepTransform
    m.def("get_sweep_transform", &b2GetSweepTransform, py::arg("sweep"), py::arg("time"));


    py::enum_<b2TOIState>(m, "TOIState")
        .value("UNKNOWN", b2TOIState::b2_toiStateUnknown)
        .value("FAILED", b2TOIState::b2_toiStateFailed)
        .value("OVERLAPPED", b2TOIState::b2_toiStateOverlapped)
        .value("HIT", b2TOIState::b2_toiStateHit)
        .value("SEPARATED", b2TOIState::b2_toiStateSeparated);

    // b2TOIOutput
    py::class_<b2TOIOutput>(m, "TOIOutput").def(py::init<>()).def_rw("state", &b2TOIOutput::state)
        //.def_rw("t", &b2TOIOutput::t)
        ;


    // b2TimeOfImpact
    m.def("time_of_impact", &b2TimeOfImpact, py::arg("input"));

#endif


    // b2ManifoldPoint
    py::class_<b2ManifoldPoint>(m, "ManifoldPoint")
        .def(py::init<>())
        .def_ro("point", &b2ManifoldPoint::point)
        .def_ro("anchor_a", &b2ManifoldPoint::anchorA)
        .def_ro("anchor_b", &b2ManifoldPoint::anchorB)
        .def_ro("separation", &b2ManifoldPoint::separation)
        .def_ro("normal_impulse", &b2ManifoldPoint::normalImpulse)
        .def_ro("tangent_impulse", &b2ManifoldPoint::tangentImpulse)
        .def_ro("total_normal_impulse", &b2ManifoldPoint::totalNormalImpulse)
        .def_ro("normal_velocity", &b2ManifoldPoint::normalVelocity)
        .def_ro("id", &b2ManifoldPoint::id)
        .def_ro("persisted", &b2ManifoldPoint::persisted);

    // b2Manifold
    py::class_<b2Manifold>(m, "Manifold")
        .def(py::init<>())
        // TODO MANIFOLD POINTS
        .def_ro("point_count", &b2Manifold::pointCount)
        .def_rw("normal", &b2Manifold::normal)
        .def(
            "__len__",
            [](const b2Manifold& self)
            {
                return self.pointCount;
            }
        )
        .def(
            "points",
            [](const b2Manifold& self)
            {
                return nb::make_iterator(
                    nb::type<b2Manifold>(),
                    "iterator",
                    self.points,
                    self.points + self.pointCount
                );
            },
            nb::keep_alive<0, 1>()
        );

    // b2TreeStats

    py::class_<b2TreeStats>(m, "TreeStats")
        .def(py::init<>())
        .def_rw("node_visits", &b2TreeStats::nodeVisits)
        .def_rw("leaf_visits", &b2TreeStats::leafVisits);
}
