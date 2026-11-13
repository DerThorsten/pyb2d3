#include <vector>

#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>

#include "bind.hpp"
#include "pyb2d3/core/binder.hpp"
#include "pyb2d3/py_converter.hpp"

namespace pyb2d3::bind
{
    namespace
    {
        // one python class per geometry type, differing only in the get / set function
        template <class T, auto Get, auto Set>
        nb::class_<T, Shape> bind_geometry_shape(nb::module_& m, const char* cls_name, const char* prop)
        {
            nb::class_<T, Shape> cls(m, cls_name);
            cls.def(nb::init<uint64_t>(), nb::arg("id"));
            Binder<T, Shape>(cls).template rw<Get, Set>(prop);
            return cls;
        }

        template <class V, int (*Capacity)(b2ShapeId), int (*Fill)(b2ShapeId, V*, int)>
        std::vector<V> collect(const Shape& self)
        {
            std::vector<V> data(Capacity(self.id));
            data.resize(Fill(self.id, data.data(), static_cast<int>(data.size())));
            return data;
        }
    }  // namespace

    void export_shape(nb::module_& m)
    {
        nb::enum_<b2ShapeType>(m, "ShapeType")
            .value("circle", b2_circleShape)
            .value("capsule", b2_capsuleShape)
            .value("segment", b2_segmentShape)
            .value("polygon", b2_polygonShape)
            .value("chain_segment", b2_chainSegmentShape)
            .export_values();

        nb::class_<Shape> cls(m, "Shape");
        nb::class_<Batch<Shape>> batch_cls(m, "Shapes");
        bind_handle(cls, batch_cls);

        Binder(cls, batch_cls)
            .ro<b2Shape_GetType>("type")
            .ro<b2Shape_GetBody>("body")
            .ro<b2Shape_GetWorld>("world")
            .ro<b2Shape_IsSensor>("is_sensor")

            // material
            .ro<b2Shape_GetDensity>("density")
            .def<b2Shape_SetDensity>("set_density", nb::arg("density"), nb::arg("update_body_mass") = true)
            .rw<b2Shape_GetFriction, b2Shape_SetFriction>("friction")
            .rw<b2Shape_GetRestitution, b2Shape_SetRestitution>("restitution")
            .rw<b2Shape_GetUserMaterial, b2Shape_SetUserMaterial>("user_material")
            .rw<b2Shape_GetSurfaceMaterial, b2Shape_SetSurfaceMaterial>("surface_material")
            .rw<b2Shape_GetFilter, b2Shape_SetFilter>("filter")

            // events
            .rw<b2Shape_AreSensorEventsEnabled, b2Shape_EnableSensorEvents>("sensor_events_enabled")
            .rw<b2Shape_AreContactEventsEnabled, b2Shape_EnableContactEvents>("contact_events_enabled")
            .rw<b2Shape_ArePreSolveEventsEnabled, b2Shape_EnablePreSolveEvents>("pre_solve_events_enabled")
            .rw<b2Shape_AreHitEventsEnabled, b2Shape_EnableHitEvents>("hit_events_enabled")

            // geometry queries
            .def<b2Shape_TestPoint>("test_point", nb::arg("point"))
            .def<b2Shape_CastRay>("cast_ray", nb::arg("origin"), nb::arg("translation"))
            .def<b2Shape_GetClosestPoint>("closest_point", nb::arg("target"))
            .ro<b2Shape_GetBounds>("bounds")
            .def<b2Shape_ComputeMassData>("compute_mass_data")
            .def<b2Shape_ApplyWind>(
                "apply_wind",
                nb::arg("wind"),
                nb::arg("drag"),
                nb::arg("lift"),
                nb::arg("wake") = true
            )

            // contacts / sensors
            .ro<b2Shape_GetContactCapacity>("contact_capacity")
            .ro<b2Shape_GetSensorCapacity>("sensor_capacity");

        cls.def("destroy", &Shape::Destroy, nb::arg("update_body_mass") = true)
            .def(
                "cast",
                [](const Shape& self)
                {
                    return GetCastedShape(self.id);
                }
            )
            .def_prop_ro("contact_data", &collect<b2ContactData, b2Shape_GetContactCapacity, b2Shape_GetContactData>)
            .def_prop_ro("sensor_overlaps", &collect<b2ShapeId, b2Shape_GetSensorCapacity, b2Shape_GetSensorData>);

        bind_geometry_shape<CircleShape, b2Shape_GetCircle, b2Shape_SetCircle>(m, "CircleShape", "circle");
        bind_geometry_shape<CapsuleShape, b2Shape_GetCapsule, b2Shape_SetCapsule>(m, "CapsuleShape", "capsule");
        bind_geometry_shape<SegmentShape, b2Shape_GetSegment, b2Shape_SetSegment>(m, "SegmentShape", "segment");
        bind_geometry_shape<PolygonShape, b2Shape_GetPolygon, b2Shape_SetPolygon>(m, "PolygonShape", "polygon");

        auto chain_segment_cls = bind_geometry_shape<
            ChainSegmentShape,
            b2Shape_GetChainSegment,
            b2Shape_SetChainSegment>(m, "ChainSegmentShape", "chain_segment");
        Binder<ChainSegmentShape, Shape>(chain_segment_cls).ro<b2Shape_GetParentChain>("parent_chain");
        chain_segment_cls.def_prop_ro(
            "segment",
            [](const ChainSegmentShape& self)
            {
                return b2Shape_GetChainSegment(self.id).segment;
            }
        );

        m.def(
            "get_casted_shape",
            [](b2ShapeId id)
            {
                return GetCastedShape(id);
            },
            nb::arg("shape_id")
        );
    }
}  // namespace pyb2d3::bind
