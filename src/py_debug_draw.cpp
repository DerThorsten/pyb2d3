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


// c++ class enum for color formats
enum class DebugDrawColorFormat
{
    HexaColorFormat,
    RgbFloatFormat,
    RgbUInt8Format
};

void export_py_debug_draw(nb::module_& m)
{
    // b2DebugDraw itself
    nb::class_<b2DebugDraw>(m, "_DebugDrawRawBase")
        .def_rw("drawing_bounds", &PyDebugDraw::drawingBounds)
        .def_rw("draw_shapes", &PyDebugDraw::drawShapes)
        .def_rw("draw_joints", &PyDebugDraw::drawJoints)
        .def_rw("draw_joint_extras", &PyDebugDraw::drawJointExtras)
        .def_rw("draw_bounds", &PyDebugDraw::drawBounds)
        .def_rw("draw_mass", &PyDebugDraw::drawMass)
        .def_rw("draw_body_names", &PyDebugDraw::drawBodyNames)
        .def_rw("draw_contacts", &PyDebugDraw::drawContacts)
        .def_rw("draw_graph_colors", &PyDebugDraw::drawGraphColors)
        .def_rw("draw_contact_normals", &PyDebugDraw::drawContactNormals)
        .def_rw("draw_contact_impulses", &PyDebugDraw::drawContactImpulses)
        .def_rw("draw_contact_features", &PyDebugDraw::drawContactFeatures)
        .def_rw("draw_friction_impulses", &PyDebugDraw::drawFrictionImpulses)
        .def_rw("draw_islands", &PyDebugDraw::drawIslands);


    nb::class_<PyDebugDraw, b2DebugDraw>(m, "DebugDrawBase").def(nb::init<nb::object>());


    // enum for color formats
    nb::enum_<DebugDrawColorFormat>(m, "DebugDrawColorFormat")
        .value("HexaColorFormat", DebugDrawColorFormat::HexaColorFormat)
        .value("RgbFloatFormat", DebugDrawColorFormat::RgbFloatFormat)
        .value("RgbUInt8Format", DebugDrawColorFormat::RgbUInt8Format)
        .export_values();


    // PyTransformDebugDraw
    nb::class_<PyTransformDebugDraw<CanvasWorldTransform, HexaColorFormat>, b2DebugDraw>(
        m,
        "TransformDebugDrawBaseHexaColorFormat"
    )
        .def(
            nb::init<const CanvasWorldTransform&, nb::handle>(),
            nb::keep_alive<0, 1>(),
            nb::keep_alive<0, 2>(),
            nb::arg("transform"),
            nb::arg("py_object")
        )

        ;

    nb::class_<PyTransformDebugDraw<CanvasWorldTransform, RgbFloatFormat>, b2DebugDraw>(
        m,
        "TransformDebugDrawBaseRgbFloatFormat"
    )
        .def(
            nb::init<const CanvasWorldTransform&, nb::handle>(),
            nb::keep_alive<0, 1>(),
            nb::keep_alive<0, 2>(),
            nb::arg("transform"),
            nb::arg("py_object")
        );
    nb::class_<PyTransformDebugDraw<CanvasWorldTransform, RgbUInt8Format>, b2DebugDraw>(
        m,
        "TransformDebugDrawBaseRgbUInt8Format"
    )
        .def(
            nb::init<const CanvasWorldTransform&, nb::handle>(),
            nb::keep_alive<0, 1>(),
            nb::keep_alive<0, 2>(),
            nb::arg("transform"),
            nb::arg("py_object")
        );
}
