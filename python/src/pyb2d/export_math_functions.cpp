#include <nanobind/nanobind.h>

// stl conversion
// #include <nanobind/stl/arr

#include <pyb2d/py_converter.hpp>

// C
extern "C" {
#include <box2d/math_functions.h>
#include <box2d/box2d.h>
}

// nanobind namespace
namespace py = nanobind;








void export_math_functions(py::module_ & m)
{
    
    py::class_<b2Transform>(m, "Transform")
        .def(py::init<>())
        .def_rw("p", &b2Transform::p)
        .def_rw("q", &b2Transform::q)
    ;

    py::class_<b2Rot>(m, "Rot")
        .def("__init__", [](b2Rot *t, double rad) {
            new (t) b2Rot();
            t->s = sin(rad);
            t->c = cos(rad);
        })
        .def("__init__", [](b2Rot *t) {
            new (t) b2Rot();
            t->s = 1.0;
            t->c = 0.0;
        })
        .def_rw("c", &b2Rot::c)
        .def_rw("s", &b2Rot::s)
    ;


    nb::implicitly_convertible<double, b2Rot>();
};
