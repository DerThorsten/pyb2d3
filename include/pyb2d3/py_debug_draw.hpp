#pragma once

#include <box2d/box2d.h>
#include <nanobind/nanobind.h>

#include "pyb2d3/core/binder.hpp"
#include "pyb2d3/debug_draw.hpp"
#include "pyb2d3/py_converter.hpp"

namespace nb = nanobind;

// Debug draw that forwards every primitive to methods of a python object
// (see `pyb2d3.DebugDraw` for the python side of the interface).
class PyDebugDraw : public pyb2d::DebugDraw<PyDebugDraw>
{
public:

    explicit PyDebugDraw(nb::handle py_object)
        : m_py(py_object)
    {
    }

    void draw_polygon(const b2Vec2* vertices, int count, b2HexColor color)
    {
        m_py.attr("draw_polygon")(points(vertices, count), int(color));
    }

    void draw_solid_polygon(b2Transform transform, const b2Vec2* vertices, int count, float radius, b2HexColor color)
    {
        m_py.attr("draw_solid_polygon")(transform, points(vertices, count), radius, int(color));
    }

    void draw_circle(b2Vec2 center, float radius, b2HexColor color)
    {
        m_py.attr("draw_circle")(center, radius, int(color));
    }

    void draw_solid_circle(b2Transform transform, float radius, b2HexColor color)
    {
        m_py.attr("draw_solid_circle")(transform, radius, int(color));
    }

    void draw_solid_capsule(b2Vec2 p1, b2Vec2 p2, float radius, b2HexColor color)
    {
        m_py.attr("draw_solid_capsule")(p1, p2, radius, int(color));
    }

    void draw_segment(b2Vec2 p1, b2Vec2 p2, b2HexColor color)
    {
        m_py.attr("draw_segment")(p1, p2, int(color));
    }

    void draw_transform(b2Transform transform)
    {
        m_py.attr("draw_transform")(transform);
    }

    void draw_point(b2Vec2 p, float size, b2HexColor color)
    {
        m_py.attr("draw_point")(p, size, int(color));
    }

    void draw_string(b2Vec2 p, const char* s, b2HexColor color)
    {
        m_py.attr("draw_string")(p, s, int(color));
    }

    void draw_aabb(b2AABB aabb, b2HexColor color)
    {
        m_py.attr("draw_aabb")(aabb, int(color));
    }

private:

    // (n, 2) float32 array, copied (box2d's buffer is only valid during the callback)
    static nb::object points(const b2Vec2* vertices, int count)
    {
        float* data = nullptr;
        nb::object arr = pyb2d3::detail::make_array<float>(count, 2, data);
        for (int i = 0; i < count; ++i)
        {
            data[2 * i] = vertices[i].x;
            data[2 * i + 1] = vertices[i].y;
        }
        return arr;
    }

    nb::handle m_py;
};
