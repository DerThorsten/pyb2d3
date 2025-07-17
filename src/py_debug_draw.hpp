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

struct HexaColorFormat
{
    using type = int;

    static type convert(const b2HexColor& color)
    {
        return static_cast<type>(color);
    }
};

struct RgbFloatFormat
{
    using type = std::array<float, 3>;

    static type convert(const b2HexColor& color)
    {
        return {
            static_cast<float>((color >> 16) & 0xFF) / 255.0f,
            static_cast<float>((color >> 8) & 0xFF) / 255.0f,
            static_cast<float>(color & 0xFF) / 255.0f
        };
    }
};

struct RgbUInt8Format
{
    using type = std::array<uint8_t, 3>;

    static type convert(const b2HexColor& color)
    {
        return {
            static_cast<uint8_t>((color >> 16) & 0xFF),
            static_cast<uint8_t>((color >> 8) & 0xFF),
            static_cast<uint8_t>(color & 0xFF)
        };
    }
};

// apply a transformation to each point before calling to
// the python class methods
template <class TRANSFORM, class COLOR_FORMAT>
class PyTransformDebugDraw : public pyb2d::DebugDraw<PyTransformDebugDraw<TRANSFORM, COLOR_FORMAT>>
{
public:

    inline PyTransformDebugDraw(const TRANSFORM& transform, py::handle py_class)
        : pyb2d::DebugDraw<PyTransformDebugDraw>()
        , m_transform(transform)
        , m_py_class(py_class)
        , m_points_buffer()
    {
    }

    void draw_polygon(const b2Vec2* vertices, int vertexCount, b2HexColor color)
    {
        m_points_buffer.clear();
        for (int i = 0; i < vertexCount; ++i)
        {
            m_points_buffer.push_back(m_transform.world_to_canvas(vertices[i]));
        }
        ArrayVec2 points(
            m_points_buffer.data(),
            {static_cast<std::size_t>(vertexCount), static_cast<std::size_t>(2)}
        );
        m_py_class.attr("draw_polygon")(points, COLOR_FORMAT::convert(color));
    }

    void
    draw_solid_polygon(b2Transform transform, const b2Vec2* vertices, int vertexCount, float radius, b2HexColor color)
    {
        m_points_buffer.clear();
        for (int i = 0; i < vertexCount; ++i)
        {
            m_points_buffer.push_back(m_transform.world_to_canvas(b2TransformPoint(transform, vertices[i])));
        }
        ArrayVec2 points(
            m_points_buffer.data(),
            {static_cast<std::size_t>(vertexCount), static_cast<std::size_t>(2)}
        );
        m_py_class.attr("draw_solid_polygon")(
            points,
            m_transform.scale_world_to_canvas(radius),
            COLOR_FORMAT::convert(color)
        );
    }

    void draw_circle(b2Vec2 center, float radius, b2HexColor color)
    {
        b2Vec2 canvas_center = m_transform.world_to_canvas(center);
        m_py_class.attr("draw_circle")(
            canvas_center,
            m_transform.scale_world_to_canvas(radius),
            COLOR_FORMAT::convert(color)
        );
    }

    void draw_solid_cirlce(b2Transform transform, float radius, b2HexColor color)
    {
        m_py_class.attr("draw_solid_circle")(
            m_transform.world_to_canvas(transform.p),
            m_transform.scale_world_to_canvas(radius),
            COLOR_FORMAT::convert(color)
        );
    }

    void draw_solid_capsule(b2Vec2 p1, b2Vec2 p2, float radius, b2HexColor color)
    {
        m_py_class.attr("draw_solid_capsule")(
            m_transform.world_to_canvas(p1),
            m_transform.world_to_canvas(p2),
            m_transform.scale_world_to_canvas(radius),
            COLOR_FORMAT::convert(color)
        );
    }

    void draw_segment(b2Vec2 p1, b2Vec2 p2, b2HexColor color)
    {
        m_py_class.attr("draw_segment")(
            m_transform.world_to_canvas(p1),
            m_transform.world_to_canvas(p2),
            COLOR_FORMAT::convert(color)
        );
    }

    void draw_transform(b2Transform transform)
    {
        b2Vec2 canvas_p = m_transform.world_to_canvas(transform.p);
        b2Transform canvas_transform;
        canvas_transform.p = canvas_p;
        canvas_transform.q.c = transform.q.c;
        canvas_transform.q.s = transform.q.s;
        m_py_class.attr("draw_transform")(canvas_p, canvas_transform);
    }

    void draw_point(b2Vec2 p, float size, b2HexColor color)
    {
        m_py_class.attr("draw_point")(
            m_transform.world_to_canvas(p),
            m_transform.scale_world_to_canvas(size),
            COLOR_FORMAT::convert(color)
        );
    }

    void draw_string(b2Vec2 p, const char* s, b2HexColor color)
    {
        m_py_class.attr("draw_string")(m_transform.world_to_canvas(p), s, COLOR_FORMAT::convert(color));
    }

private:

    const TRANSFORM& m_transform;
    py::handle m_py_class;
    std::vector<b2Vec2> m_points_buffer;
};
