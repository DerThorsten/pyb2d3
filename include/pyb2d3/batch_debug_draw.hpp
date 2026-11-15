#pragma once

#include <cmath>
#include <cstdint>
#include <cstring>
#include <vector>

#include <box2d/box2d.h>
#include <nanobind/nanobind.h>

#include "pyb2d3/debug_draw.hpp"

namespace nb = nanobind;

// Debug draw that collects the primitives of `b2World_Draw` in flat float arrays, one
// per primitive type, with no python call per shape (the per-shape python callbacks of
// `PyDebugDraw` dominate the frame time with thousands of bodies, especially in wasm).
//
// Every record has the memory layout of one GPU instance of the sandbox's OpenGL draw
// code (`pyb2d3_sandbox_opengl/draw.py`); colors are packed RGBA8 (r in the lowest
// byte, alpha 255) stored bit for bit in a float:
//   circles        x, y, radius, rgba                                     (4)
//   solid_circles  x, y, cos, sin, radius, rgba                           (6)
//   capsules       center x, y, axis x, y, radius, length, rgba           (7)
//   polygons       transform (x, y, cos, sin), 8 local points (16, zero padded),
//                  count (int32 bits), radius, rgba                       (23)
//   points         x, y, size, rgba                                       (4)
//   lines          two vertices per line: x, y, rgba                      (3 each)
// Polygon outlines, bounds and transforms become lines; strings are rare and go to a
// python callable `on_string(position, text, color)`.
class BatchDebugDraw : public pyb2d::DebugDraw<BatchDebugDraw>
{
public:

    static constexpr std::size_t circle_width = 4;
    static constexpr std::size_t solid_circle_width = 6;
    static constexpr std::size_t capsule_width = 7;
    static constexpr std::size_t polygon_width = 23;
    static constexpr std::size_t point_width = 4;
    static constexpr std::size_t line_vertex_width = 3;

    explicit BatchDebugDraw(nb::object on_string)
        : m_on_string(std::move(on_string))
    {
    }

    std::vector<float> circles;
    std::vector<float> solid_circles;
    std::vector<float> capsules;
    std::vector<float> polygons;
    std::vector<float> points;
    std::vector<float> lines;

    // empty all arrays (keeps the allocations for the next frame)
    void clear()
    {
        circles.clear();
        solid_circles.clear();
        capsules.clear();
        polygons.clear();
        points.clear();
        lines.clear();
    }

    // the drawing options (what to draw, scales, bounds) of another debug draw
    void copy_options(const b2DebugDraw& other)
    {
        drawingBounds = other.drawingBounds;
        forceScale = other.forceScale;
        jointScale = other.jointScale;
        drawShapes = other.drawShapes;
        drawJoints = other.drawJoints;
        drawJointExtras = other.drawJointExtras;
        drawAnchorA = other.drawAnchorA;
        drawChainNormals = other.drawChainNormals;
        drawBounds = other.drawBounds;
        drawMass = other.drawMass;
        drawBodyNames = other.drawBodyNames;
        drawContacts = other.drawContacts;
        drawGraphColors = other.drawGraphColors;
        drawContactFeatures = other.drawContactFeatures;
        drawContactNormals = other.drawContactNormals;
        drawContactForces = other.drawContactForces;
        drawFrictionForces = other.drawFrictionForces;
        drawIslands = other.drawIslands;
    }

    // -- pyb2d::DebugDraw interface (world coordinates) --------------------------------

    void draw_polygon(const b2Vec2* vertices, int count, b2HexColor color)
    {
        for (int i = 0; i < count; ++i)
        {
            line(vertices[i], vertices[(i + 1) % count], color);
        }
    }

    void
    draw_solid_polygon(b2Transform transform, const b2Vec2* vertices, int count, float radius, b2HexColor color)
    {
        const int n = count < B2_MAX_POLYGON_VERTICES ? count : B2_MAX_POLYGON_VERTICES;
        push(polygons, {transform.p.x, transform.p.y, transform.q.c, transform.q.s});
        for (int i = 0; i < 8; ++i)
        {
            const bool used = i < n;
            push(polygons, {used ? vertices[i].x : 0.0f, used ? vertices[i].y : 0.0f});
        }
        polygons.push_back(bits(static_cast<std::uint32_t>(n)));
        push(polygons, {radius, rgba(color)});
    }

    void draw_circle(b2Vec2 center, float radius, b2HexColor color)
    {
        push(circles, {center.x, center.y, radius, rgba(color)});
    }

    void draw_solid_circle(b2Transform transform, float radius, b2HexColor color)
    {
        push(solid_circles, {transform.p.x, transform.p.y, transform.q.c, transform.q.s, radius, rgba(color)});
    }

    void draw_solid_capsule(b2Vec2 p1, b2Vec2 p2, float radius, b2HexColor color)
    {
        const float dx = p2.x - p1.x;
        const float dy = p2.y - p1.y;
        const float length = std::sqrt(dx * dx + dy * dy);
        if (length < 0.001f)
        {
            draw_solid_circle(b2Transform{p1, b2Rot_identity}, radius, color);
            return;
        }
        push(
            capsules,
            {0.5f * (p1.x + p2.x), 0.5f * (p1.y + p2.y), dx / length, dy / length, radius, length, rgba(color)}
        );
    }

    void draw_segment(b2Vec2 p1, b2Vec2 p2, b2HexColor color)
    {
        line(p1, p2, color);
    }

    void draw_transform(b2Transform transform)
    {
        const float scale = 0.5f;
        line(transform.p, b2TransformPoint(transform, {scale, 0.0f}), b2_colorRed);
        line(transform.p, b2TransformPoint(transform, {0.0f, scale}), b2_colorGreen);
    }

    void draw_point(b2Vec2 p, float size, b2HexColor color)
    {
        push(points, {p.x, p.y, size, rgba(color)});
    }

    void draw_string(b2Vec2 p, const char* s, b2HexColor color)
    {
        if (m_on_string.is_valid() && !m_on_string.is_none())
        {
            m_on_string(p, s, int(color));
        }
    }

    void draw_aabb(b2AABB aabb, b2HexColor color)
    {
        const b2Vec2 lo = aabb.lowerBound;
        const b2Vec2 hi = aabb.upperBound;
        const b2Vec2 corners[4] = {lo, {hi.x, lo.y}, hi, {lo.x, hi.y}};
        draw_polygon(corners, 4, color);
    }

private:

    // the bits of a uint32 as a float (the arrays are uploaded as raw bytes)
    static float bits(std::uint32_t value)
    {
        float f;
        std::memcpy(&f, &value, sizeof(f));
        return f;
    }

    // 0xRRGGBB -> RGBA8 with r in the lowest byte, alpha 255, as float bits
    static float rgba(b2HexColor color)
    {
        const std::uint32_t c = static_cast<std::uint32_t>(color);
        const std::uint32_t r = (c >> 16) & 0xFF;
        const std::uint32_t g = (c >> 8) & 0xFF;
        const std::uint32_t b = c & 0xFF;
        return bits((255u << 24) | (b << 16) | (g << 8) | r);
    }

    static void push(std::vector<float>& out, std::initializer_list<float> values)
    {
        out.insert(out.end(), values);
    }

    void line(b2Vec2 p1, b2Vec2 p2, b2HexColor color)
    {
        const float c = rgba(color);
        push(lines, {p1.x, p1.y, c, p2.x, p2.y, c});
    }

    nb::object m_on_string;
};
