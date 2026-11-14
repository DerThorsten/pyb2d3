#include <string>

#include <box2d/base.h>
#include <box2d/box2d.h>
#include <box2d/constants.h>
#include <box2d/math_functions.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

#include "bind.hpp"
#include "pyb2d3/generated/docstrings.hpp"

namespace pyb2d3::bind
{
    namespace
    {
        nb::object*& log_callback()
        {
            static nb::object* fn = nullptr;
            return fn;
        }

        void log_trampoline(const char* message)
        {
            nb::gil_scoped_acquire gil;
            try
            {
                (*log_callback())(message);
            }
            catch (nb::python_error& e)
            {
                e.discard_as_unraisable("box2d log callback");
            }
        }

        void default_log(const char* message)
        {
            PySys_WriteStdout("%s\n", message);
        }
    }  // namespace

    void export_base(nb::module_& m)
    {
        nb::class_<b2Version>(m, "Version")
            .def_ro("major", &b2Version::major)
            .def_ro("minor", &b2Version::minor)
            .def_ro("revision", &b2Version::revision)
            .def(
                "__repr__",
                [](const b2Version& v)
                {
                    return std::to_string(v.major) + "." + std::to_string(v.minor) + "." + std::to_string(v.revision);
                }
            );

        // compile time constants of the box2d build
        m.attr("NAME_LENGTH") = B2_NAME_LENGTH;
        m.attr("MAX_POLYGON_VERTICES") = B2_MAX_POLYGON_VERTICES;
        m.attr("MAX_WORKERS") = B2_MAX_WORKERS;
        m.attr("MAX_WORLDS") = B2_MAX_WORLDS;
        m.attr("GRAPH_COLOR_COUNT") = B2_GRAPH_COLOR_COUNT;
        m.attr("MAX_RESTITUTION_ITERATIONS") = B2_MAX_RESTITUTION_ITERATIONS;
        m.attr("DEFAULT_CATEGORY_BITS") = uint64_t(B2_DEFAULT_CATEGORY_BITS);
        m.attr("DEFAULT_MASK_BITS") = uint64_t(B2_DEFAULT_MASK_BITS);
        m.attr("TIME_TO_SLEEP") = B2_TIME_TO_SLEEP;

        m.def("get_version", &b2GetVersion, "Version of the box2d C library pyb2d3 was built against.");
        m.def("is_double_precision", &b2IsDoublePrecision, docs::doc<&b2IsDoublePrecision>);
        m.def("is_avx2_available", &b2IsAVX2Available, docs::doc<&b2IsAVX2Available>);
        m.def("get_byte_count", &b2GetByteCount, "Bytes currently allocated by box2d.");

        m.def("get_ticks", &b2GetTicks, docs::doc<&b2GetTicks>);
        m.def("get_milliseconds", &b2GetMilliseconds, nb::arg("ticks"), docs::doc<&b2GetMilliseconds>);
        m.def("yield_thread", &b2Yield, docs::doc<&b2Yield>);

        m.def(
            "set_length_units_per_meter",
            &b2SetLengthUnitsPerMeter,
            nb::arg("length_units"),
            docs::doc<&b2SetLengthUnitsPerMeter>
        );
        m.def("get_length_units_per_meter", &b2GetLengthUnitsPerMeter, docs::doc<&b2GetLengthUnitsPerMeter>);
        // colors are plain 0xRRGGBB ints everywhere in the python api
        m.def(
            "get_graph_color",
            [](int index)
            {
                return static_cast<uint32_t>(b2GetGraphColor(index));
            },
            nb::arg("index")
        );

        m.def(
            "set_log_callback",
            [](nb::object fn)
            {
                delete log_callback();
                log_callback() = fn.is_none() ? nullptr : new nb::object(std::move(fn));
                b2SetLogCallback(log_callback() ? log_trampoline : default_log);
            },
            nb::arg("callback").none(),
            "Route box2d's log messages to ``callback(message)``; None restores printing to stdout."
        );
    }
}  // namespace pyb2d3::bind
