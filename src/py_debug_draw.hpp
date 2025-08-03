#pragma once

#include <iostream>

#include <nanobind/nanobind.h>
#include <pyb2d3/debug_draw.hpp>
#include <pyb2d3/py_converter.hpp>
#include <pyb2d3/world_to_canvas.hpp>
// // C
// extern "C"
// {
#include <box2d/box2d.h>
#include <box2d/math_functions.h>
#include <box2d/types.h>
// }

// nanobind namespace
namespace py = nanobind;

class PyDebugDraw : public pyb2d::DebugDraw<PyDebugDraw>
{
public:

    inline PyDebugDraw(py::handle py_class)
        : pyb2d::DebugDraw<PyDebugDraw>()
        , m_py_class(py_class)
    {
    }

    void draw_polygon(const b2Vec2* vertices, int vertexCount, b2HexColor color)
    {
        float* data = const_cast<float*>(reinterpret_cast<const float*>(vertices));
        ArrayVec2 points(data, {static_cast<std::size_t>(vertexCount), static_cast<std::size_t>(2)});
        m_py_class.attr("draw_polygon")(points, static_cast<int>(color));
    }

    void
    draw_solid_polygon(b2Transform transform, const b2Vec2* vertices, int vertexCount, float radius, b2HexColor color)
    {
        float* data = const_cast<float*>(reinterpret_cast<const float*>(vertices));
        ArrayVec2 points(data, {static_cast<std::size_t>(vertexCount), static_cast<std::size_t>(2)});
        m_py_class.attr("draw_solid_polygon")(transform, points, radius, static_cast<int>(color));
    }

    void draw_circle(b2Vec2 center, float radius, b2HexColor color)
    {
        m_py_class.attr("draw_circle")(center, radius, static_cast<int>(color));
    }

    void draw_solid_cirlce(b2Transform transform, float radius, b2HexColor color)
    {
        m_py_class.attr("draw_solid_circle")(transform, radius, static_cast<int>(color));
    }

    void draw_solid_capsule(b2Vec2 p1, b2Vec2 p2, float radius, b2HexColor color)
    {
        m_py_class.attr("draw_solid_capsule")(p1, p2, radius, static_cast<int>(color));
    }

    void draw_segment(b2Vec2 p1, b2Vec2 p2, b2HexColor color)
    {
        m_py_class.attr("draw_segment")(p1, p2, static_cast<int>(color));
    }

    void draw_transform(b2Transform transform)
    {
        m_py_class.attr("draw_transform")(transform);
    }

    void draw_point(b2Vec2 p, float size, b2HexColor color)
    {
        m_py_class.attr("draw_point")(p, size, static_cast<int>(color));
    }

    void draw_string(b2Vec2 p, const char* s, b2HexColor color)
    {
        m_py_class.attr("draw_string")(p, s, static_cast<int>(color));
    }

    py::handle m_py_class;
};
