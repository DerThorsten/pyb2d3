#include <string>
#include <tuple>
#include <vector>

#include <box2d/collision.h>
#include <box2d/math_functions.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/vector.h>

#include "bind.hpp"
#include "pyb2d3/core/binder.hpp"
#include "pyb2d3/core/points.hpp"
#include "pyb2d3/py_converter.hpp"

namespace pyb2d3::bind
{
    namespace
    {
        using PointArray = b2Vec2[B2_MAX_POLYGON_VERTICES];

        // (n, 2) copy of the first `count` points
        nb::object points_to_array(const b2Vec2* points, int count)
        {
            float* data = nullptr;
            nb::object arr = detail::make_array<float>(count, 2, data);
            for (int i = 0; i < count; ++i)
            {
                batch_value<b2Vec2>::store(data + 2 * i, points[i]);
            }
            return arr;
        }

        // throw unless the points fit into box2d's fixed size point arrays
        void check_max_points(const Points& points)
        {
            if (points.size() > B2_MAX_POLYGON_VERTICES)
            {
                throw nb::value_error(
                    ("at most " + std::to_string(B2_MAX_POLYGON_VERTICES) + " points are supported").c_str()
                );
            }
        }

        // copy points into a fixed size point array, checking the box2d limit
        int array_to_points(const Points& value, b2Vec2* points)
        {
            check_max_points(value);
            std::copy(value.data(), value.data() + value.size(), points);
            return value.count();
        }

        // `name` property for a struct with a fixed point array + count (Hull, ShapeProxy, Polygon)
        template <class T, PointArray T::* Points, int T::* Count>
        void points_property(nb::class_<T>& cls, const char* name, bool writable)
        {
            auto getter = [](const T& self)
            {
                return points_to_array(self.*Points, self.*Count);
            };
            if (writable)
            {
                cls.def_prop_rw(
                    name,
                    getter,
                    [](T& self, const pyb2d3::Points& value)
                    {
                        self.*Count = array_to_points(value, self.*Points);
                    }
                );
            }
            else
            {
                cls.def_prop_ro(name, getter);
            }
        }

    }  // namespace

    void export_collision(nb::module_& m)
    {
        // ---- geometry ---------------------------------------------------------------------
        nb::class_<b2Circle>(m, "Circle")
            .def(
                "__init__",
                [](b2Circle* t, b2Vec2 center, float radius)
                {
                    new (t) b2Circle{center, radius};
                },
                nb::arg("center") = b2Vec2{0.0f, 0.0f},
                nb::arg("radius") = 1.0f
            )
            .def_rw("center", &b2Circle::center)
            .def_rw("radius", &b2Circle::radius);

        nb::class_<b2Capsule>(m, "Capsule")
            .def(
                "__init__",
                [](b2Capsule* t, b2Vec2 c1, b2Vec2 c2, float radius)
                {
                    new (t) b2Capsule{c1, c2, radius};
                },
                nb::arg("center1") = b2Vec2{0.0f, 0.0f},
                nb::arg("center2") = b2Vec2{0.0f, 0.0f},
                nb::arg("radius") = 0.0f
            )
            .def_rw("center1", &b2Capsule::center1)
            .def_rw("center2", &b2Capsule::center2)
            .def_rw("radius", &b2Capsule::radius);

        nb::class_<b2Segment>(m, "Segment")
            .def(
                "__init__",
                [](b2Segment* t, b2Vec2 p1, b2Vec2 p2)
                {
                    new (t) b2Segment{p1, p2};
                },
                nb::arg("point1") = b2Vec2{0.0f, 0.0f},
                nb::arg("point2") = b2Vec2{0.0f, 0.0f}
            )
            .def_rw("point1", &b2Segment::point1)
            .def_rw("point2", &b2Segment::point2);

        nb::class_<b2ChainSegment>(m, "ChainSegment")
            .def(nb::init<>())
            .def_rw("ghost1", &b2ChainSegment::ghost1)
            .def_rw("segment", &b2ChainSegment::segment)
            .def_rw("ghost2", &b2ChainSegment::ghost2)
            .def_rw("chain_id", &b2ChainSegment::chainId);

        // polygons are built with the make_* functions, so their points are read only
        nb::class_<b2Polygon> polygon(m, "Polygon");
        polygon.def(nb::init<>())
            .def_rw("centroid", &b2Polygon::centroid)
            .def_rw("radius", &b2Polygon::radius)
            .def_ro("count", &b2Polygon::count);
        // writable like in C (e.g. to scale a polygon in place), but the count must not change:
        // normals and centroid are not recomputed
        polygon.def_prop_rw(
            "vertices",
            [](const b2Polygon& self)
            {
                return points_to_array(self.vertices, self.count);
            },
            [](b2Polygon& self, const Points& value)
            {
                if (value.count() != self.count)
                {
                    throw nb::value_error(
                        "Polygon.vertices: the vertex count must not change (normals are not recomputed), "
                        "use make_polygon(compute_hull(points)) for a new polygon"
                    );
                }
                array_to_points(value, self.vertices);
            }
        );
        points_property<b2Polygon, &b2Polygon::normals, &b2Polygon::count>(polygon, "normals", false);

        nb::class_<b2Hull> hull(m, "Hull");
        hull.def(nb::init<>())
            .def_ro("count", &b2Hull::count)
            .def("validate", &b2ValidateHull, docs::doc<&b2ValidateHull>);
        points_property<b2Hull, &b2Hull::points, &b2Hull::count>(hull, "points", true);

        nb::class_<b2MassData>(m, "MassData")
            .def(nb::init<>())
            .def_rw("mass", &b2MassData::mass)
            .def_rw("center", &b2MassData::center)
            .def_rw("rotational_inertia", &b2MassData::rotationalInertia);

        m.def(
            "compute_hull",
            [](const Points& points)
            {
                return b2ComputeHull(points.data(), points.count());
            },
            nb::arg("points"),
            "Convex hull of up to 8 points (an empty hull for fewer than 3 or more than 8 points)."
        );
        m.def("validate_hull", &b2ValidateHull, nb::arg("hull"), docs::doc<&b2ValidateHull>);

        m.def(
            "make_polygon",
            &b2MakePolygon,
            nb::arg("hull"),
            nb::arg("radius") = 0.0f,
            docs::doc<&b2MakePolygon>
        );
        m.def(
            "make_offset_polygon",
            &b2MakeOffsetPolygon,
            nb::arg("hull"),
            nb::arg("position"),
            nb::arg("rotation"),
            docs::doc<&b2MakeOffsetPolygon>
        );
        m.def(
            "make_offset_rounded_polygon",
            &b2MakeOffsetRoundedPolygon,
            nb::arg("hull"),
            nb::arg("position"),
            nb::arg("rotation"),
            nb::arg("radius"),
            docs::doc<&b2MakeOffsetRoundedPolygon>
        );
        m.def("make_square", &b2MakeSquare, nb::arg("half_width"), docs::doc<&b2MakeSquare>);
        m.def("make_box", &b2MakeBox, nb::arg("half_width"), nb::arg("half_height"), docs::doc<&b2MakeBox>);
        m.def(
            "make_rounded_box",
            &b2MakeRoundedBox,
            nb::arg("half_width"),
            nb::arg("half_height"),
            nb::arg("radius"),
            docs::doc<&b2MakeRoundedBox>
        );
        m.def(
            "make_offset_box",
            &b2MakeOffsetBox,
            nb::arg("half_width"),
            nb::arg("half_height"),
            nb::arg("center"),
            nb::arg("rotation"),
            docs::doc<&b2MakeOffsetBox>
        );
        m.def(
            "make_offset_rounded_box",
            &b2MakeOffsetRoundedBox,
            nb::arg("half_width"),
            nb::arg("half_height"),
            nb::arg("center"),
            nb::arg("rotation"),
            nb::arg("radius"),
            docs::doc<&b2MakeOffsetRoundedBox>
        );
        m.def(
            "transform_polygon",
            &b2TransformPolygon,
            nb::arg("transform"),
            nb::arg("polygon"),
            docs::doc<&b2TransformPolygon>
        );

        m.def(
            "compute_circle_mass",
            &b2ComputeCircleMass,
            nb::arg("shape"),
            nb::arg("density"),
            docs::doc<&b2ComputeCircleMass>
        );
        m.def(
            "compute_capsule_mass",
            &b2ComputeCapsuleMass,
            nb::arg("shape"),
            nb::arg("density"),
            docs::doc<&b2ComputeCapsuleMass>
        );
        m.def(
            "compute_polygon_mass",
            &b2ComputePolygonMass,
            nb::arg("shape"),
            nb::arg("density"),
            docs::doc<&b2ComputePolygonMass>
        );
        m.def(
            "compute_circle_bounds",
            &b2ComputeCircleBounds,
            nb::arg("shape"),
            nb::arg("transform"),
            docs::doc<&b2ComputeCircleBounds>
        );
        m.def(
            "compute_capsule_bounds",
            &b2ComputeCapsuleBounds,
            nb::arg("shape"),
            nb::arg("transform"),
            docs::doc<&b2ComputeCapsuleBounds>
        );
        m.def(
            "compute_polygon_bounds",
            &b2ComputePolygonBounds,
            nb::arg("shape"),
            nb::arg("transform"),
            docs::doc<&b2ComputePolygonBounds>
        );
        m.def(
            "compute_segment_bounds",
            &b2ComputeSegmentBounds,
            nb::arg("shape"),
            nb::arg("transform"),
            docs::doc<&b2ComputeSegmentBounds>
        );
        m.def(
            "point_in_circle",
            &b2PointInCircle,
            nb::arg("shape"),
            nb::arg("point"),
            docs::doc<&b2PointInCircle>
        );
        m.def(
            "point_in_capsule",
            &b2PointInCapsule,
            nb::arg("shape"),
            nb::arg("point"),
            docs::doc<&b2PointInCapsule>
        );
        m.def(
            "point_in_polygon",
            &b2PointInPolygon,
            nb::arg("shape"),
            nb::arg("point"),
            docs::doc<&b2PointInPolygon>
        );

        // ---- ray / shape casts --------------------------------------------------------------
        nb::class_<b2RayCastInput>(m, "RayCastInput")
            .def(
                "__init__",
                [](b2RayCastInput* t, b2Vec2 origin, b2Vec2 translation, float max_fraction)
                {
                    new (t) b2RayCastInput{origin, translation, max_fraction};
                },
                nb::arg("origin") = b2Vec2{0.0f, 0.0f},
                nb::arg("translation") = b2Vec2{0.0f, 0.0f},
                nb::arg("max_fraction") = 1.0f
            )
            .def_rw("origin", &b2RayCastInput::origin)
            .def_rw("translation", &b2RayCastInput::translation)
            .def_rw("max_fraction", &b2RayCastInput::maxFraction);
        m.def("is_valid_ray", &b2IsValidRay, nb::arg("input"), docs::doc<&b2IsValidRay>);

        nb::class_<b2ShapeProxy> proxy(m, "ShapeProxy");
        proxy.def(nb::init<>()).def_ro("count", &b2ShapeProxy::count).def_rw("radius", &b2ShapeProxy::radius);
        points_property<b2ShapeProxy, &b2ShapeProxy::points, &b2ShapeProxy::count>(proxy, "points", true);
        m.def(
            "make_proxy",
            [](const Points& points, float radius)
            {
                check_max_points(points);
                return b2MakeProxy(points.data(), points.count(), radius);
            },
            nb::arg("points"),
            nb::arg("radius") = 0.0f
        );
        m.def(
            "make_offset_proxy",
            [](const Points& points, float radius, b2Vec2 position, b2Rot rotation)
            {
                check_max_points(points);
                return b2MakeOffsetProxy(points.data(), points.count(), radius, position, rotation);
            },
            nb::arg("points"),
            nb::arg("radius"),
            nb::arg("position"),
            nb::arg("rotation")
        );

        nb::class_<b2ShapeCastInput>(m, "ShapeCastInput")
            .def(nb::init<>())
            .def_rw("proxy", &b2ShapeCastInput::proxy)
            .def_rw("translation", &b2ShapeCastInput::translation)
            .def_rw("max_fraction", &b2ShapeCastInput::maxFraction)
            .def_rw("can_encroach", &b2ShapeCastInput::canEncroach);

        nb::class_<b2CastOutput>(m, "CastOutput")
            .def(nb::init<>())
            .def_rw("normal", &b2CastOutput::normal)
            .def_rw("point", &b2CastOutput::point)
            .def_rw("fraction", &b2CastOutput::fraction)
            .def_rw("iterations", &b2CastOutput::iterations)
            .def_rw("hit", &b2CastOutput::hit);

        m.def(
            "cast_ray_circle",
            &b2CastRayCircle,
            nb::arg("shape"),
            nb::arg("input"),
            docs::doc<&b2CastRayCircle>
        );
        m.def(
            "cast_ray_capsule",
            &b2CastRayCapsule,
            nb::arg("shape"),
            nb::arg("input"),
            docs::doc<&b2CastRayCapsule>
        );
        m.def(
            "cast_ray_segment",
            &b2CastRaySegment,
            nb::arg("shape"),
            nb::arg("input"),
            nb::arg("one_sided") = false,
            docs::doc<&b2CastRaySegment>
        );
        m.def(
            "cast_ray_polygon",
            &b2CastRayPolygon,
            nb::arg("shape"),
            nb::arg("input"),
            docs::doc<&b2CastRayPolygon>
        );
        m.def(
            "cast_shape_circle",
            &b2CastShapeCircle,
            nb::arg("shape"),
            nb::arg("input"),
            docs::doc<&b2CastShapeCircle>
        );
        m.def(
            "cast_shape_capsule",
            &b2CastShapeCapsule,
            nb::arg("shape"),
            nb::arg("input"),
            docs::doc<&b2CastShapeCapsule>
        );
        m.def(
            "cast_shape_segment",
            &b2CastShapeSegment,
            nb::arg("shape"),
            nb::arg("input"),
            docs::doc<&b2CastShapeSegment>
        );
        m.def(
            "cast_shape_polygon",
            &b2CastShapePolygon,
            nb::arg("shape"),
            nb::arg("input"),
            docs::doc<&b2CastShapePolygon>
        );

        nb::class_<b2ShapeCastPairInput>(m, "ShapeCastPairInput")
            .def(nb::init<>())
            .def_rw("proxy_a", &b2ShapeCastPairInput::proxyA)
            .def_rw("proxy_b", &b2ShapeCastPairInput::proxyB)
            .def_rw("transform", &b2ShapeCastPairInput::transform)
            .def_rw("translation_b", &b2ShapeCastPairInput::translationB)
            .def_rw("max_fraction", &b2ShapeCastPairInput::maxFraction)
            .def_rw("can_encroach", &b2ShapeCastPairInput::canEncroach);
        m.def("cast_shape", &b2CastShape, nb::arg("input"), docs::doc<&b2CastShape>);

        // ---- distance -------------------------------------------------------------------------
        nb::class_<b2SegmentDistanceResult>(m, "SegmentDistanceResult")
            .def_ro("closest1", &b2SegmentDistanceResult::closest1)
            .def_ro("closest2", &b2SegmentDistanceResult::closest2)
            .def_ro("fraction1", &b2SegmentDistanceResult::fraction1)
            .def_ro("fraction2", &b2SegmentDistanceResult::fraction2)
            .def_ro("distance_squared", &b2SegmentDistanceResult::distanceSquared);
        m.def(
            "compute_segment_distance",
            &b2ComputeSegmentDistance,
            nb::arg("p1"),
            nb::arg("q1"),
            nb::arg("p2"),
            nb::arg("q2"),
            docs::doc<&b2ComputeSegmentDistance>
        );

        nb::class_<b2SimplexCache>(m, "SimplexCache")
            .def(
                "__init__",
                [](b2SimplexCache* t)
                {
                    new (t) b2SimplexCache(b2_emptySimplexCache);
                }
            )
            .def_ro("count", &b2SimplexCache::count);

        nb::class_<b2DistanceInput>(m, "DistanceInput")
            .def(nb::init<>())
            .def_rw("proxy_a", &b2DistanceInput::proxyA)
            .def_rw("proxy_b", &b2DistanceInput::proxyB)
            .def_rw("transform", &b2DistanceInput::transform)
            .def_rw("use_radii", &b2DistanceInput::useRadii);

        nb::class_<b2DistanceOutput>(m, "DistanceOutput")
            .def_ro("point_a", &b2DistanceOutput::pointA)
            .def_ro("point_b", &b2DistanceOutput::pointB)
            .def_ro("normal", &b2DistanceOutput::normal)
            .def_ro("distance", &b2DistanceOutput::distance)
            .def_ro("iterations", &b2DistanceOutput::iterations)
            .def_ro("simplex_count", &b2DistanceOutput::simplexCount);

        nb::class_<b2SimplexVertex>(m, "SimplexVertex")
            .def_ro("w_a", &b2SimplexVertex::wA)
            .def_ro("w_b", &b2SimplexVertex::wB)
            .def_ro("w", &b2SimplexVertex::w)
            .def_ro("a", &b2SimplexVertex::a)
            .def_ro("index_a", &b2SimplexVertex::indexA)
            .def_ro("index_b", &b2SimplexVertex::indexB);

        nb::class_<b2Simplex>(m, "Simplex")
            .def_ro("v1", &b2Simplex::v1)
            .def_ro("v2", &b2Simplex::v2)
            .def_ro("v3", &b2Simplex::v3)
            .def_ro("count", &b2Simplex::count);

        m.def(
            "compute_shape_distance",
            [](const b2DistanceInput& input, b2SimplexCache* cache, int simplex_capacity)
            {
                b2SimplexCache local = b2_emptySimplexCache;
                std::vector<b2Simplex> simplexes(simplex_capacity);
                b2DistanceOutput out = b2ComputeShapeDistance(
                    &input,
                    cache ? cache : &local,
                    simplexes.data(),
                    simplex_capacity
                );
                simplexes.resize(std::min(out.simplexCount, simplex_capacity));
                return std::make_tuple(out, simplexes);
            },
            nb::arg("input"),
            nb::arg("cache").none() = nb::none(),
            nb::arg("simplex_capacity") = 0,
            "Returns (DistanceOutput, [Simplex]). Pass a SimplexCache to warm start repeated queries."
        );

        // ---- time of impact ---------------------------------------------------------------------
        nb::class_<b2Sweep>(m, "Sweep")
            .def(nb::init<>())
            .def_rw("local_center", &b2Sweep::localCenter)
            .def_rw("c1", &b2Sweep::c1)
            .def_rw("c2", &b2Sweep::c2)
            .def_rw("q1", &b2Sweep::q1)
            .def_rw("q2", &b2Sweep::q2);
        m.def(
            "get_sweep_transform",
            &b2GetSweepTransform,
            nb::arg("sweep"),
            nb::arg("time"),
            docs::doc<&b2GetSweepTransform>
        );

        nb::class_<b2TOIInput>(m, "TOIInput")
            .def(nb::init<>())
            .def_rw("proxy_a", &b2TOIInput::proxyA)
            .def_rw("proxy_b", &b2TOIInput::proxyB)
            .def_rw("sweep_a", &b2TOIInput::sweepA)
            .def_rw("sweep_b", &b2TOIInput::sweepB)
            .def_rw("max_fraction", &b2TOIInput::maxFraction);

        nb::enum_<b2TOIState>(m, "TOIState")
            .value("UNKNOWN", b2_toiStateUnknown)
            .value("FAILED", b2_toiStateFailed)
            .value("OVERLAPPED", b2_toiStateOverlapped)
            .value("HIT", b2_toiStateHit)
            .value("SEPARATED", b2_toiStateSeparated);

        nb::class_<b2TOIOutput>(m, "TOIOutput")
            .def_ro("state", &b2TOIOutput::state)
            .def_ro("point", &b2TOIOutput::point)
            .def_ro("normal", &b2TOIOutput::normal)
            .def_ro("fraction", &b2TOIOutput::fraction);
        m.def(
            "compute_time_of_impact",
            &b2ComputeTimeOfImpact,
            nb::arg("input"),
            docs::doc<&b2ComputeTimeOfImpact>
        );

        // ---- manifolds --------------------------------------------------------------------------
        nb::class_<b2ManifoldPoint>(m, "ManifoldPoint")
            .def_ro("anchor_a", &b2ManifoldPoint::anchorA)
            .def_ro("anchor_b", &b2ManifoldPoint::anchorB)
            .def_ro("separation", &b2ManifoldPoint::separation)
            .def_ro("normal_impulse", &b2ManifoldPoint::normalImpulse)
            .def_ro("tangent_impulse", &b2ManifoldPoint::tangentImpulse)
            .def_ro("total_normal_impulse", &b2ManifoldPoint::totalNormalImpulse)
            .def_ro("normal_velocity", &b2ManifoldPoint::normalVelocity)
            .def_ro("base_separation", &b2ManifoldPoint::baseSeparation)
            .def_ro("id", &b2ManifoldPoint::id)
            .def_ro("persisted", &b2ManifoldPoint::persisted);

        nb::class_<b2Manifold>(m, "Manifold")
            .def(nb::init<>())
            .def_rw("normal", &b2Manifold::normal)
            .def_ro("rolling_impulse", &b2Manifold::rollingImpulse)
            .def_ro("point_count", &b2Manifold::pointCount)
            .def(
                "__len__",
                [](const b2Manifold& self)
                {
                    return self.pointCount;
                }
            )
            .def_prop_ro(
                "points",
                [](const b2Manifold& self)
                {
                    return std::vector<b2ManifoldPoint>(self.points, self.points + self.pointCount);
                }
            );

        nb::class_<b2LocalManifoldPoint>(m, "LocalManifoldPoint")
            .def_ro("point", &b2LocalManifoldPoint::point)
            .def_ro("separation", &b2LocalManifoldPoint::separation)
            .def_ro("id", &b2LocalManifoldPoint::id);

        nb::class_<b2LocalManifold>(m, "LocalManifold")
            .def_ro("normal", &b2LocalManifold::normal)
            .def_ro("point_count", &b2LocalManifold::pointCount)
            .def_prop_ro(
                "points",
                [](const b2LocalManifold& self)
                {
                    return std::vector<b2LocalManifoldPoint>(self.points, self.points + self.pointCount);
                }
            );

        // shape A is in the reference frame, `transform` is the pose of shape B relative to A
        const auto a = nb::arg("shape_a");
        const auto b = nb::arg("shape_b");
        const auto xf = nb::arg("transform");
        m.def("collide_circles", &b2CollideCircles, a, b, xf, docs::doc<&b2CollideCircles>);
        m.def(
            "collide_capsule_and_circle",
            &b2CollideCapsuleAndCircle,
            a,
            b,
            xf,
            docs::doc<&b2CollideCapsuleAndCircle>
        );
        m.def(
            "collide_segment_and_circle",
            &b2CollideSegmentAndCircle,
            a,
            b,
            xf,
            docs::doc<&b2CollideSegmentAndCircle>
        );
        m.def(
            "collide_polygon_and_circle",
            &b2CollidePolygonAndCircle,
            a,
            b,
            xf,
            docs::doc<&b2CollidePolygonAndCircle>
        );
        m.def("collide_capsules", &b2CollideCapsules, a, b, xf, docs::doc<&b2CollideCapsules>);
        m.def(
            "collide_segment_and_capsule",
            &b2CollideSegmentAndCapsule,
            a,
            b,
            xf,
            docs::doc<&b2CollideSegmentAndCapsule>
        );
        m.def(
            "collide_polygon_and_capsule",
            &b2CollidePolygonAndCapsule,
            a,
            b,
            xf,
            docs::doc<&b2CollidePolygonAndCapsule>
        );
        m.def("collide_polygons", &b2CollidePolygons, a, b, xf, docs::doc<&b2CollidePolygons>);
        m.def(
            "collide_segment_and_polygon",
            &b2CollideSegmentAndPolygon,
            a,
            b,
            xf,
            docs::doc<&b2CollideSegmentAndPolygon>
        );
        m.def(
            "collide_chain_segment_and_circle",
            &b2CollideChainSegmentAndCircle,
            a,
            b,
            xf,
            docs::doc<&b2CollideChainSegmentAndCircle>
        );
        m.def(
            "collide_chain_segment_and_capsule",
            [](const b2ChainSegment& sa, const b2Capsule& sb, b2Transform t, b2SimplexCache* cache)
            {
                b2SimplexCache local = b2_emptySimplexCache;
                return b2CollideChainSegmentAndCapsule(&sa, &sb, t, cache ? cache : &local);
            },
            a,
            b,
            xf,
            nb::arg("cache").none() = nb::none()
        );
        m.def(
            "collide_chain_segment_and_polygon",
            [](const b2ChainSegment& sa, const b2Polygon& sb, b2Transform t, b2SimplexCache* cache)
            {
                b2SimplexCache local = b2_emptySimplexCache;
                return b2CollideChainSegmentAndPolygon(&sa, &sb, t, cache ? cache : &local);
            },
            a,
            b,
            xf,
            nb::arg("cache").none() = nb::none()
        );

        // ---- trees / movers ---------------------------------------------------------------------
        nb::class_<b2TreeStats>(m, "TreeStats")
            .def(nb::init<>())
            .def_ro("node_visits", &b2TreeStats::nodeVisits)
            .def_ro("leaf_visits", &b2TreeStats::leafVisits);

        nb::class_<b2PlaneResult>(m, "PlaneResult")
            .def_ro("plane", &b2PlaneResult::plane)
            .def_ro("point", &b2PlaneResult::point)
            .def_ro("hit", &b2PlaneResult::hit);

        nb::class_<b2CollisionPlane>(m, "CollisionPlane")
            .def(
                "__init__",
                [](b2CollisionPlane* t, b2Plane plane, float push_limit, float push, bool clip_velocity)
                {
                    new (t) b2CollisionPlane{plane, push_limit, push, clip_velocity};
                },
                nb::arg("plane"),
                nb::arg("push_limit") = 3.4e38f,
                nb::arg("push") = 0.0f,
                nb::arg("clip_velocity") = true
            )
            .def_rw("plane", &b2CollisionPlane::plane)
            .def_rw("push_limit", &b2CollisionPlane::pushLimit)
            .def_rw("push", &b2CollisionPlane::push)
            .def_rw("clip_velocity", &b2CollisionPlane::clipVelocity);

        nb::class_<b2PlaneSolverResult>(m, "PlaneSolverResult")
            .def_ro("delta", &b2PlaneSolverResult::delta)
            .def_ro("iteration_count", &b2PlaneSolverResult::iterationCount);

        m.def(
            "solve_planes",
            [](b2Vec2 target_delta, std::vector<b2CollisionPlane> planes)
            {
                b2PlaneSolverResult r = b2SolvePlanes(target_delta, planes.data(), static_cast<int>(planes.size()));
                return std::make_tuple(r, planes);
            },
            nb::arg("target_delta"),
            nb::arg("planes"),
            "Returns (PlaneSolverResult, planes) where `planes` carry the updated push values."
        );
        m.def(
            "clip_vector",
            [](b2Vec2 vector, const std::vector<b2CollisionPlane>& planes)
            {
                return b2ClipVector(vector, planes.data(), static_cast<int>(planes.size()));
            },
            nb::arg("vector"),
            nb::arg("planes")
        );
    }
}  // namespace pyb2d3::bind
