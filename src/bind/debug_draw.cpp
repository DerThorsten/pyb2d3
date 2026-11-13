#include <nanobind/nanobind.h>

#include "bind.hpp"
#include "pyb2d3/py_debug_draw.hpp"

namespace pyb2d3::bind
{
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
    }
}  // namespace pyb2d3::bind
