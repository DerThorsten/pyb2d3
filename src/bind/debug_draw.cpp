#include <algorithm>

#include <nanobind/nanobind.h>

#include "bind.hpp"
#include "pyb2d3/batch_debug_draw.hpp"
#include "pyb2d3/py_debug_draw.hpp"

namespace pyb2d3::bind
{
    namespace
    {
        // a copy of one of the BatchDebugDraw buffers as an (n, width) float32 array
        nb::object as_array(const std::vector<float>& values, std::size_t width)
        {
            float* data = nullptr;
            nb::object array = pyb2d3::detail::make_array<float>(values.size() / width, width, data);
            std::copy(values.begin(), values.end(), data);
            return array;
        }

        // a read-only property returning the copy of buffer `Member`
        template <std::vector<float> BatchDebugDraw::* Member, std::size_t Width>
        nb::object buffer(const BatchDebugDraw& self)
        {
            return as_array(self.*Member, Width);
        }
    }  // namespace

    void export_debug_draw(nb::module_& m)
    {
        // the flags / settings of b2DebugDraw
        nb::class_<b2DebugDraw>(m, "_DebugDrawRawBase")
            .def_rw("drawing_bounds", &b2DebugDraw::drawingBounds)
            .def_rw("force_scale", &b2DebugDraw::forceScale)
            .def_rw("joint_scale", &b2DebugDraw::jointScale)
            .def_rw("draw_shapes", &b2DebugDraw::drawShapes)
            .def_rw("draw_joints", &b2DebugDraw::drawJoints)
            .def_rw("draw_joint_extras", &b2DebugDraw::drawJointExtras)
            .def_rw("draw_anchor_a", &b2DebugDraw::drawAnchorA)
            .def_rw("draw_chain_normals", &b2DebugDraw::drawChainNormals)
            .def_rw("draw_bounds", &b2DebugDraw::drawBounds)
            .def_rw("draw_mass", &b2DebugDraw::drawMass)
            .def_rw("draw_body_names", &b2DebugDraw::drawBodyNames)
            .def_rw("draw_contacts", &b2DebugDraw::drawContacts)
            .def_rw("draw_graph_colors", &b2DebugDraw::drawGraphColors)
            .def_rw("draw_contact_features", &b2DebugDraw::drawContactFeatures)
            .def_rw("draw_contact_normals", &b2DebugDraw::drawContactNormals)
            .def_rw("draw_contact_forces", &b2DebugDraw::drawContactForces)
            .def_rw("draw_friction_forces", &b2DebugDraw::drawFrictionForces)
            .def_rw("draw_islands", &b2DebugDraw::drawIslands);

        nb::class_<PyDebugDraw, b2DebugDraw>(m, "DebugDrawBase").def(nb::init<nb::handle>(), nb::arg("py_object"));

        // world.draw(batch) collects everything in C++ (no python call per shape); the
        // buffers are float32 arrays in the GPU instance layouts documented in
        // include/pyb2d3/batch_debug_draw.hpp
        using B = BatchDebugDraw;
        nb::class_<B, b2DebugDraw>(
            m,
            "BatchDebugDraw",
            "Debug draw that collects ``world.draw(batch)`` in C++: one float32 array per primitive\n"
            "(circles, solid_circles, capsules, polygons, points, lines; layouts in\n"
            "include/pyb2d3/batch_debug_draw.hpp). Draws append, ``clear()`` empties the buffers.\n\n"
            "Each buffer property returns a new array that owns its copy of the data: it stays valid\n"
            "after ``clear()`` and later draws (e.g. several worlds into one frame), and every access\n"
            "copies (read each property once per frame)."
        )
            .def(nb::init<nb::object>(), nb::arg("on_string") = nb::none())
            .def("clear", &B::clear)
            .def("copy_options", &B::copy_options, nb::arg("other"))
            .def_prop_ro("circles", &buffer<&B::circles, B::circle_width>)
            .def_prop_ro("solid_circles", &buffer<&B::solid_circles, B::solid_circle_width>)
            .def_prop_ro("capsules", &buffer<&B::capsules, B::capsule_width>)
            .def_prop_ro("polygons", &buffer<&B::polygons, B::polygon_width>)
            .def_prop_ro("points", &buffer<&B::points, B::point_width>)
            .def_prop_ro("lines", &buffer<&B::lines, B::line_vertex_width>);
    }
}  // namespace pyb2d3::bind
