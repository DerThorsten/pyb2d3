#include <nanobind/nanobind.h>

namespace py = nanobind;

void export_box2d_types(py::module_ &m);
void export_box2d_functions(py::module_ &m);

NB_MODULE(pybb2d, m) {
    export_box2d_types(m);
    export_box2d_functions(m);
}