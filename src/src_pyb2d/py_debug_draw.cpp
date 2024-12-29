#include <nanobind/nanobind.h>
#include "py_debug_draw.hpp"
#include <pyb2d/py_converter.hpp>
#include <iostream>

// C
extern "C" {
#include <box2d/math_functions.h>
#include <box2d/box2d.h>
#include <box2d/types.h>
}

// nanobind namespace
namespace py = nanobind;

/// Draw a closed polygon provided in CCW order.
void PyDrawPolygon( const b2Vec2* vertices, int vertexCount, b2HexColor color, void* context )
{   
    PyDebugDraw* draw = reinterpret_cast<PyDebugDraw*>(context);
    float * data = const_cast<float *>(reinterpret_cast<const float*>(vertices));
    ArrayVec2 points(data, {static_cast<std::size_t>(vertexCount), static_cast<std::size_t>(2)});
    draw->m_py_class.attr("draw_polygon")(points, static_cast<int>(color));
}

/// Draw a solid closed polygon provided in CCW order.
void PyDrawSolidPolygon( b2Transform transform, const b2Vec2* vertices, int vertexCount, float radius, b2HexColor color,void* context )
{
    PyDebugDraw* draw = reinterpret_cast<PyDebugDraw*>(context);
    float * data = const_cast<float *>(reinterpret_cast<const float*>(vertices));
    ArrayVec2 points(data, {static_cast<std::size_t>(vertexCount), static_cast<std::size_t>(2)});
    draw->m_py_class.attr("draw_solid_polygon")(transform, points, radius, static_cast<int>(color));
}

/// Draw a circle.
void PyDrawCircle( b2Vec2 center, float radius, b2HexColor color, void* context )
{
    PyDebugDraw* draw = (PyDebugDraw*)context;
    draw->m_py_class.attr("draw_circle")(center.x, center.y, radius, static_cast<int>(color));
}

/// Draw a solid circle.
void PyDrawSolidCircle( b2Transform transform, float radius, b2HexColor color, void* context )
{
    PyDebugDraw* draw = (PyDebugDraw*)context;
    draw->m_py_class.attr("draw_solid_circle")(transform, radius, static_cast<int>(color));
}

/// Draw a solid capsule.
void PyDrawSolidCapsule( b2Vec2 p1, b2Vec2 p2, float radius, b2HexColor color, void* context )
{
    PyDebugDraw* draw = (PyDebugDraw*)context;
    draw->m_py_class.attr("draw_solid_capsule")(p1, p2, radius, static_cast<int>(color));
}

/// Draw a line segment.
void PyDrawSegment( b2Vec2 p1, b2Vec2 p2, b2HexColor color, void* context )
{
    PyDebugDraw* draw = (PyDebugDraw*)context;
    draw->m_py_class.attr("draw_segment")(p1, p2, static_cast<int>(color));
}

/// Draw a transform. Choose your own length scale.
void PyDrawTransform( b2Transform transform, void* context )
{
    PyDebugDraw* draw = (PyDebugDraw*)context;
    draw->m_py_class.attr("draw_transform")(transform);
}

/// Draw a point.
void PyDrawPoint( b2Vec2 p, float size, b2HexColor color, void* context )
{
    PyDebugDraw* draw = (PyDebugDraw*)context;
    draw->m_py_class.attr("draw_point")(p, size, static_cast<int>(color));
}

/// Draw a string.
void PyDrawString( b2Vec2 p, const char* s, void* context )
{
    PyDebugDraw* draw = (PyDebugDraw*)context;
    draw->m_py_class.attr("draw_string")(p, s);
}


PyDebugDraw::PyDebugDraw(py::handle py_class) 
:   b2DebugDraw(b2DefaultDebugDraw()),
    m_py_class(py_class)
{
    this->DrawPolygon = PyDrawPolygonGeneric<PyDebugDraw>;
    this->DrawSolidPolygon = PyDrawSolidPolygon;
    this->DrawCircle = PyDrawCircle;
    this->DrawSolidCircle = PyDrawSolidCircle;
    this->DrawSolidCapsule = PyDrawSolidCapsule;
    this->DrawSegment = PyDrawSegment;
    this->DrawTransform = PyDrawTransform;
    this->DrawPoint =  PyDrawPoint;
    this->DrawString = PyDrawString;
    this->context = reinterpret_cast<void*>(this);
}


void export_py_debug_draw(py::module_ &m)
{
    py::class_<PyDebugDraw>(m, "DebugDrawBase")
        .def(py::init<py::object>())

        .def_rw("drawing_bounds", &PyDebugDraw::drawingBounds)
        .def_rw("use_drawing_bounds", &PyDebugDraw::useDrawingBounds)
        .def_rw("draw_shapes", &PyDebugDraw::drawShapes)
        .def_rw("draw_joints", &PyDebugDraw::drawJoints)
        .def_rw("draw_joint_extras", &PyDebugDraw::drawJointExtras)
        .def_rw("draw_aabbs", &PyDebugDraw::drawAABBs)
        .def_rw("draw_mass", &PyDebugDraw::drawMass)
    ;
}