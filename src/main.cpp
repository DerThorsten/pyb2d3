#include <nanobind/nanobind.h>
// #include <pyb2d3/py_converter.hpp>

namespace py = nanobind;

void export_box2d_types(py::module_& m);
void export_box2d_functions(py::module_& m);
void export_collision(py::module_& m);
void export_py_debug_draw(py::module_& m);
void export_math_functions(py::module_& m);
void export_batch_api(py::module_& m);
void export_world_to_canvas(py::module_& m);
void export_extras(py::module_& m);

#ifndef PYB2D3_NO_THREADING
void export_threadpool(py::module_& m);
#endif


NB_MODULE(_pyb2d3, m)
{
    export_box2d_types(m);
    export_box2d_functions(m);
    export_collision(m);
    export_py_debug_draw(m);
    export_math_functions(m);
    export_batch_api(m);
    export_world_to_canvas(m);
    export_extras(m);

#ifndef PYB2D3_NO_THREADING
    export_threadpool(m);
#endif


    m.doc() = "Python bindings for Box2D, a 2D physics engine.";

#ifdef PYB2D3_NO_THREADING
    m.attr("WITH_THREADING") = false;
#else
    m.attr("WITH_THREADING") = true;
#endif
}
