#include <vector>

#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>

#include "bind.hpp"
#include "pyb2d3/core/binder.hpp"
#include "pyb2d3/py_converter.hpp"

namespace pyb2d3::bind
{
    void export_chain(nb::module_& m)
    {
        nb::class_<Chain> cls(m, "Chain");
        bind_handle(cls);

        Binder<Chain>(cls)
            .ro<b2Chain_GetWorld>("world")
            .ro<b2Chain_GetSegmentCount>("segment_count")
            .def<b2Chain_GetSurfaceMaterial>("get_surface_material", nb::arg("segment_index"))
            .def<b2Chain_SetSurfaceMaterial>("set_surface_material", nb::arg("material"), nb::arg("segment_index"))
            .def<b2Chain_SetAllSurfaceMaterials>("set_all_surface_materials", nb::arg("material"));

        cls.def("destroy", &Chain::Destroy)
            .def_prop_ro(
                "segments",
                [](const Chain& self)
                {
                    std::vector<b2ShapeId> ids(b2Chain_GetSegmentCount(self.id));
                    ids.resize(b2Chain_GetSegments(self.id, ids.data(), static_cast<int>(ids.size())));
                    return ids;
                }
            );
    }
}  // namespace pyb2d3::bind
