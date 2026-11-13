#pragma once

// Entry points of the per-domain binding files (one function per file).
// They are called from module.cpp in dependency order.

#include <nanobind/nanobind.h>

namespace pyb2d3::bind
{
    namespace nb = nanobind;

    void export_base(nb::module_& m);           // base.cpp: version, timing, misc
    void export_vec2(nb::module_& m);           // vec2.cpp: Vec2
    void export_math(nb::module_& m);           // math.cpp: Rot, Transform, AABB, Plane, math functions
    void export_collision(nb::module_& m);      // collision.cpp: geometry, casts, distance, manifolds
    void export_dynamic_tree(nb::module_& m);   // dynamic_tree.cpp: DynamicTree
    void export_defs(nb::module_& m);           // defs.cpp: World/Body/Shape/Chain/Explosion defs, filters, materials
    void export_joint_defs(nb::module_& m);     // joint_defs.cpp: all joint defs
    void export_world(nb::module_& m);          // world.cpp: WorldView
    void export_body(nb::module_& m);           // body.cpp: Body, Bodies
    void export_shape(nb::module_& m);          // shape.cpp: Shape + subclasses, Shapes
    void export_chain(nb::module_& m);          // chain.cpp: Chain
    void export_joint(nb::module_& m);          // joint.cpp: Joint + subclasses
    void export_events(nb::module_& m);         // events.cpp: events, contacts
    void export_recording(nb::module_& m);      // recording.cpp: Recording, Replay, snapshots
    void export_debug_draw(nb::module_& m);     // debug_draw.cpp
    void export_world_to_canvas(nb::module_& m);
    void export_extras(nb::module_& m);
#ifndef PYB2D3_NO_THREADING
    void export_threadpool(nb::module_& m);
#endif
}  // namespace pyb2d3::bind
