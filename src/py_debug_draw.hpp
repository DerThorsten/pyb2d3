#pragma once

#include <nanobind/nanobind.h>
#include <pyb2d/py_converter.hpp>

// C
// extern "C"
// {
#include <box2d/box2d.h>
#include <box2d/math_functions.h>
#include <box2d/types.h>
// }

// nanobind namespace
namespace py = nanobind;

/// Draw a closed polygon provided in CCW order.
void PyDrawPolygon(const b2Vec2* vertices, int vertexCount, b2HexColor color, void* context);

/// Draw a solid closed polygon provided in CCW order.
void PyDrawSolidPolygon(
    b2Transform transform,
    const b2Vec2* vertices,
    int vertexCount,
    float radius,
    b2HexColor color,
    void* context
);

/// Draw a circle.
void PyDrawCircle(b2Vec2 center, float radius, b2HexColor color, void* context);

/// Draw a solid circle.
void PyDrawSolidCircle(b2Transform transform, float radius, b2HexColor color, void* context);

/// Draw a solid capsule.
void PyDrawSolidCapsule(b2Vec2 p1, b2Vec2 p2, float radius, b2HexColor color, void* context);

/// Draw a line segment.
void PyDrawSegment(b2Vec2 p1, b2Vec2 p2, b2HexColor color, void* context);

/// Draw a transform. Choose your own length scale.
void PyDrawTransform(b2Transform transform, void* context);

/// Draw a point.
void PyDrawPoint(b2Vec2 p, float size, b2HexColor color, void* context);

/// Draw a string.
void PyDrawString(b2Vec2 p, const char* s, void* context);

template <class CLS>
void PyDrawPolygonGeneric(const b2Vec2* vertices, int vertexCount, b2HexColor color, void* context)
{
    CLS* draw = reinterpret_cast<CLS*>(context);
    float* data = const_cast<float*>(reinterpret_cast<const float*>(vertices));
    ArrayVec2 points(data, {static_cast<std::size_t>(vertexCount), static_cast<std::size_t>(2)});
    draw->m_py_class.attr("draw_polygon")(points, static_cast<int>(color));
}

class PyDebugDraw : public b2DebugDraw
{
public:

    // delete copy constructor
    PyDebugDraw(const PyDebugDraw&) = delete;
    // delete move constructor
    PyDebugDraw(PyDebugDraw&&) = delete;
    // delete copy assignment
    PyDebugDraw& operator=(const PyDebugDraw&) = delete;

    PyDebugDraw(py::handle py_class);

    py::handle m_py_class;
};
