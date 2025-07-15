#include "py_debug_draw.hpp"

#include <iostream>

#include <nanobind/nanobind.h>
#include <pyb2d3/debug_draw.hpp>
#include <pyb2d3/py_converter.hpp>
// // C
// extern "C"
// {
#include <box2d/box2d.h>
#include <box2d/math_functions.h>
#include <box2d/types.h>
// }

// nanobind namespace
namespace nb = nanobind;

void export_py_debug_draw(nb::module_& m)
{
    nb::class_<PyDebugDraw>(m, "DebugDrawBase")
        .def(nb::init<nb::object>())

        .def_rw("drawing_bounds", &PyDebugDraw::drawingBounds)
        .def_rw("use_drawing_bounds", &PyDebugDraw::useDrawingBounds)
        .def_rw("draw_shapes", &PyDebugDraw::drawShapes)
        .def_rw("draw_joints", &PyDebugDraw::drawJoints)
        .def_rw("draw_joint_extras", &PyDebugDraw::drawJointExtras)
        // .def_rw("draw_aabbs", &PyDebugDraw::drawAABBs)
        .def_rw("draw_mass", &PyDebugDraw::drawMass);


    // PyTransformDebugDraw
    nb::class_<PyTransformDebugDraw>(m, "TransformDebugDrawBase")
        .def(
            "__init__",
            [](PyTransformDebugDraw* t, const CanvasWorldTransform& arg0, nb::handle arg1)
            {
                new (t) PyTransformDebugDraw(arg0, arg1);
            },
            nb::arg("transform"),
            nb::arg("py_class")

        )
        .def("draw_polygon", &PyTransformDebugDraw::draw_polygon)
        .def("draw_solid_polygon", &PyTransformDebugDraw::draw_solid_polygon)
        .def("draw_circle", &PyTransformDebugDraw::draw_circle)
        .def("draw_solid_cirlce", &PyTransformDebugDraw::draw_solid_cirlce)
        .def("draw_solid_capsule", &PyTransformDebugDraw::draw_solid_capsule)
        .def("draw_segment", &PyTransformDebugDraw::draw_segment)
        .def("draw_transform", &PyTransformDebugDraw::draw_transform)
        .def("draw_point", &PyTransformDebugDraw::draw_point)
        .def("draw_string", &PyTransformDebugDraw::draw_string);
}
