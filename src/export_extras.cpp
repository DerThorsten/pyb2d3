#include <cmath>
#include <vector>

#include <box2d/box2d.h>
#include <box2d/math_functions.h>
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <pyb2d3/world_to_canvas.hpp>

// nanobind namespace
namespace nb = nanobind;


using ArrayVec2 = nb::ndarray<float, nb::numpy, nb::shape<-1, 2>, nb::c_contig>;
using ArrayVec2Int = nb::ndarray<int, nb::numpy, nb::shape<-1, 2>, nb::c_contig>;

// drawing capsules is expensive when not done with a shader.
// This creates the vertices for a capsule, transforms them
// to cavnas coordinates and rounds them to integers.
// this is particular usefull to draw capsules in pygame
struct CapsuleBuilderWithTransform
{
    CapsuleBuilderWithTransform(const CanvasWorldTransform& transform, std::size_t max_circle_segments = 2)

        : max_circle_segments(max_circle_segments)
        , transform(transform)
    {
        std::size_t max_points = 4 + 2 * max_circle_segments;
        vertices.reserve(max_points * 2);
    }

    std::size_t build(const b2Vec2& center1, const b2Vec2& center2, float radius)
    {
        const auto canvas_radius = transform.scale_world_to_canvas(radius);

        // auto pick the number of segments based on the radius
        // but at least 2 and most max_circle_segments
        std::size_t n = std::max(std::size_t(3), std::size_t(canvas_radius / 3.0f));
        n = std::min(n, max_circle_segments);

        vertices.clear();

        b2Vec2 direction = b2Normalize(center2 - center1) * radius;
        b2Vec2 perp = b2Vec2{-direction.y, direction.x};

        // angle of "perp" in radians
        float angle = atan2(perp.y, perp.x);

        // draw **HALF** of the circle segments
        // circle segments starting at the angle "angle" and going counter-clockwise
        const auto nseg = n + 2;
        for (std::size_t i = 0; i < nseg; ++i)
        {
            float theta = angle + (B2_PI * i) / nseg;
            b2Vec2 point = center1 + b2Vec2{radius * std::cosf(theta), radius * std::sinf(theta)};
            // transform the point to canvas coordinates
            const auto cpoint = transform.world_to_canvas(point);

            // round to int
            vertices.push_back(static_cast<int>(cpoint.x + 0.5f));
            vertices.push_back(static_cast<int>(cpoint.y + 0.5f));
        }

        // add the second half of the circle segments
        for (std::size_t i = 0; i < nseg; ++i)
        {
            float theta = angle + (B2_PI * i) / nseg + B2_PI;
            b2Vec2 point = center2 + b2Vec2{radius * std::cosf(theta), radius * std::sinf(theta)};
            // transform the point to canvas coordinates
            const auto cpoint = transform.world_to_canvas(point);

            // round to int
            vertices.push_back(static_cast<int>(cpoint.x + 0.5f));
            vertices.push_back(static_cast<int>(cpoint.y + 0.5f));
        }
        // return the number of vertices
        return vertices.size() / 2;  // each vertex has 2 components (x, y)
    }

    std::size_t max_circle_segments;
    std::vector<int> vertices;  // use int to avoid float precision issues
    const CanvasWorldTransform& transform;
};

void export_extras(nb::module_& m)
{
    nb::class_<CapsuleBuilderWithTransform>(m, "CapsuleBuilderWithTransform")
        .def(
            nb::init<const CanvasWorldTransform&, std::size_t>(),
            nb::keep_alive<0, 1>(),  // keep the transform alive
            nb::arg("transform"),
            nb::arg("max_circle_segments")
        )
        .def(
            "get_vertices_buffer",
            [](CapsuleBuilderWithTransform& self)
            {
                // convert the vector of int to a numpy array
                return ArrayVec2Int(
                    reinterpret_cast<int*>(self.vertices.data()),
                    {std::size_t(self.max_circle_segments * 2 + 4), std::size_t(2)}  // shape
                );
            },
            nb::rv_policy::reference_internal
        )
        .def("build", &CapsuleBuilderWithTransform::build);
}
