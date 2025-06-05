#include <nanobind/nanobind.h>
#include <pyb2d3/threadpool.hpp>

// nanobind namespace
namespace nb = nanobind;

void export_threadpool(nb::module_& m)
{
    // // enum
    // nb::enum_<NumThreads>(m, "NumThreads")
    //     .value("Auto", NumThreads::Auto)
    //     .value("Nice", NumThreads::Nice)
    //     .value("NoThreads", NumThreads::NoThreads)
    //     .export_values();

    // // ParallelOptions
    // nb::class_<ParallelOptions>(m, "ParallelOptions")
    //     .def(nb::init<int>(), nb::arg("num_threads") = static_cast<int>(NumThreads::Auto))
    //     .def("get_num_threads", &ParallelOptions::getNumThreads)
    //     .def("get_actual_num_threads", &ParallelOptions::getActualNumThreads)
    //     .def("num_threads", &ParallelOptions::numThreads, nb::arg("n"));

    // ThreadPool
    nb::class_<ThreadPool>(m, "ThreadPool")
        // .def(nb::init<const ParallelOptions&>(), nb::arg("options"))
        .def(nb::init<int>(), nb::arg("n") = -1);
}
