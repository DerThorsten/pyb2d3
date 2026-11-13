#include <nanobind/nanobind.h>
#include <pyb2d3/threadpool.hpp>

#include "bind.hpp"

namespace pyb2d3::bind
{
    void export_threadpool(nb::module_& m)
    {
        nb::class_<ThreadPool>(m, "ThreadPool")
            .def(nb::init<int>(), nb::arg("n") = -1, "Thread pool for box2d's task system; n=-1 uses all cores.")
            .def_prop_ro("num_threads", &ThreadPool::nThreads);
    }
}  // namespace pyb2d3::bind
