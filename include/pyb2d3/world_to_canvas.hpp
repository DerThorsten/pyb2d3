#pragma once


// # transform points from world coordinates
// # to canvas coordinates  and vice versa
// class WorldTransform(object):
//     def __init__(self, canvas_shape, ppm=100, offset=[0, 0]):
//         self.canvas_shape = canvas_shape
//         self.ppm = ppm
//         self.offset = offset


//     def world_to_canvas(self, p):
//         x = (p[0] + self.offset[0]) * self.ppm
//         y = self.canvas_shape[1] - ((p[1] + self.offset[1]) * self.ppm)
//         return (x, y)

//     def canvas_to_world(self, p):
//         x = (p[0] / self.ppm) - self.offset[0]
//         y = -((p[1] - self.canvas_shape[1]) / self.ppm) - self.offset[1]
//         return (x, y)

//     def batch_world_to_canvas(self, points, output=None):
//         # points = points.copy()
//         if output is None:
//             output = np.zeros(points.shape, dtype=np.float32)
//         output[:] = points[:]


//         output[:, 0] = (output[:, 0] + self.offset[0]) * self.ppm
//         output[:, 1] = self.canvas_shape[1] - ((output[:, 1] + self.offset[1]) * self.ppm)


//         return output

//     def batch_canvas_to_world(self, points, output=None):
//         # convert a list of points to world coordinates
//         if output is None:
//             output = np.zeros((len(points), 2), dtype=np.float32)
//         output[:] = np.require(points, dtype=np.float32)

//         output[:, 0] = (output[:, 0] / self.ppm) - self.offset[0]
//         output[:, 1] = -((output[:, 1] - self.canvas_shape[1]) / self.ppm) - self.offset[1]
//         return output

//     def scale_world_to_canvas(self, s):
//         return s * self.ppm

//     def scale_canvas_to_world(self, s):
//         return s / self.ppm

#include <array>

#include <box2d/box2d.h>
#include <box2d/math_functions.h>
#include <nanobind/nanobind.h>
#include <pyb2d3/py_converter.hpp>

// nanobind namespace
namespace nb = nanobind;

// suitable for html-based rendering engines
struct CanvasWorldTransform
{
    std::array<std::size_t, 2> canvas_shape;
    float ppm;
    std::array<float, 2> offset;

    inline CanvasWorldTransform(std::array<std::size_t, 2> shape, float pixels_per_meter, std::array<float, 2> offset)
        : canvas_shape(shape)
        , ppm(pixels_per_meter)
        , offset(offset)
    {
    }

    inline b2Vec2 world_to_canvas(const b2Vec2& p) const
    {
        float x = (p.x + offset[0]) * ppm;
        float y = canvas_shape[1] - ((p.y + offset[1]) * ppm);
        return b2Vec2{x, y};
    }

    inline b2Vec2 canvas_to_world(const b2Vec2& p) const
    {
        float x = (p.x / ppm) - offset[0];
        float y = -((p.y - canvas_shape[1]) / ppm) - offset[1];
        return b2Vec2{x, y};
    }

    inline float scale_world_to_canvas(float s) const
    {
        return s * ppm;
    }

    inline float scale_canvas_to_world(float s) const
    {
        return s / ppm;
    }
};
