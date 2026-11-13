#include <nanobind/nanobind.h>

#include "bind.hpp"

NB_MODULE(_pyb2d3, m)
{
    namespace bind = pyb2d3::bind;

    m.doc() = "Python bindings for Box2D, a 2D physics engine.";

    // order matters: types used as default arguments must be registered first
    bind::export_base(m);
    bind::export_vec2(m);
    bind::export_math(m);
    bind::export_collision(m);
    bind::export_dynamic_tree(m);
    bind::export_defs(m);
    bind::export_joint_defs(m);
    bind::export_body(m);
    bind::export_shape(m);
    bind::export_chain(m);
    bind::export_joint(m);
    bind::export_events(m);
    bind::export_debug_draw(m);
    bind::export_recording(m);
    bind::export_world(m);
    bind::export_world_to_canvas(m);
    bind::export_extras(m);

#ifdef PYB2D3_NO_THREADING
    m.attr("WITH_THREADING") = false;
#else
    bind::export_threadpool(m);
    m.attr("WITH_THREADING") = true;
#endif

#ifdef PYB2D3_NO_BATCH_API
    m.attr("WITH_BATCH_API") = false;
#else
    m.attr("WITH_BATCH_API") = true;
#endif
}
