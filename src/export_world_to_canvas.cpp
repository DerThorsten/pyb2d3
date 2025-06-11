

#include <array>

#include <nanobind/nanobind.h>

// nanobind array
#include <box2d/box2d.h>
#include <box2d/math_functions.h>
#include <nanobind/stl/array.h>
#include <pyb2d3/batch_api/ndarray_traits.hpp>
#include <pyb2d3/numpy_utils.hpp>
#include <pyb2d3/py_converter.hpp>
#include <pyb2d3/world_to_canvas.hpp>

// nanobind namespace
namespace nb = nanobind;

void export_world_to_canvas(nb::module_& m)
{
    nb::class_<CanvasWorldTransform>(m, "CanvasWorldTransform")
        .def(
            nb::init<std::array<std::size_t, 2>, float, std::array<float, 2>>(),
            nb::arg("canvas_shape"),
            nb::arg("ppm") = 100.0f,
            nb::arg("offset") = std::array<float, 2>{0.0f, 0.0f},
            "Initialize the CanvasWorldTransform with canvas shape, pixels per meter (ppm), and offset."
        )
        .def("world_to_canvas", &CanvasWorldTransform::world_to_canvas)
        .def("canvas_to_world", &CanvasWorldTransform::canvas_to_world)
        .def("scale_world_to_canvas", &CanvasWorldTransform::scale_world_to_canvas)
        .def("scale_canvas_to_world", &CanvasWorldTransform::scale_canvas_to_world)

        .def(
            "batch_world_to_canvas",
            [](CanvasWorldTransform& self, ConstArrayVec2 points, std::optional<ArrayVec2> output_array)
            {
                std::size_t n_points = points.shape(0);
                auto out_arr = output_array.has_value() ? output_array.value()
                                                        : alloc_for_batch<b2Vec2>(n_points);
                auto out_data_ptr = out_arr.data();
                auto input_data_ptr = points.data();
                for (std::size_t i = 0; i < n_points; ++i)
                {
                    b2Vec2 input_value = b2Vec2{input_data_ptr[i * 2], input_data_ptr[i * 2 + 1]};
                    auto value = self.world_to_canvas(input_value);
                    out_data_ptr[i * 2] = value.x;
                    out_data_ptr[i * 2 + 1] = value.y;
                }

                return out_arr;
            },
            nb::arg("points"),
            nb::arg("output") = nb::none(),
            "Convert a batch of points from world coordinates to canvas coordinates. "
            "If output is not provided, a new array will be allocated."
        )

        .def(
            "batch_canvas_to_world",
            [](CanvasWorldTransform& self, ConstArrayVec2 points, std::optional<ArrayVec2> output_array)
            {
                std::size_t n_points = points.shape(0);
                auto out_arr = output_array.has_value() ? output_array.value()
                                                        : alloc_for_batch<b2Vec2>(n_points);
                auto out_data_ptr = out_arr.data();
                auto input_data_ptr = points.data();
                for (std::size_t i = 0; i < n_points; ++i)
                {
                    b2Vec2 input_value = b2Vec2{input_data_ptr[i * 2], input_data_ptr[i * 2 + 1]};
                    auto value = self.canvas_to_world(input_value);
                    out_data_ptr[i * 2] = value.x;
                    out_data_ptr[i * 2 + 1] = value.y;
                }

                return out_arr;
            },
            nb::arg("points"),
            nb::arg("output") = nb::none(),
            "Convert a batch of points from canvas coordinates to world coordinates. "
            "If output is not provided, a new array will be allocated."
        )


        .def_rw("canvas_shape", &CanvasWorldTransform::canvas_shape, nb::arg("canvas_shape"))
        .def_rw("ppm", &CanvasWorldTransform::ppm, nb::arg("ppm"))
        .def_rw("offset", &CanvasWorldTransform::offset, nb::arg("offset"))

        ;
}
