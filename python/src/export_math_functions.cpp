#include <nanobind/nanobind.h>

// stl conversion
// #include <nanobind/stl/arr

#include "converter.hpp"

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
        .def(py::init<>())
        .def_rw("c", &b2Rot::c)
        .def_rw("s", &b2Rot::s)
    ;
};
