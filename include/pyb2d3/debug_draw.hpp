#pragma once

#include <vector>

#include <box2d/box2d.h>
#include <box2d/math_functions.h>
#include <box2d/types.h>

namespace pyb2d
{
    // CRTP adapter from box2d's b2DebugDraw callbacks to member functions of `Derived`.
    //
    // Everything is handed to `Derived` in world coordinates, which keeps the drawing
    // interface independent of box2d's internal changes (e.g. 3.2 passes polygons as
    // local vertices + transform and circles with a local center).
    //
    // Derived must implement:
    //   draw_polygon(const b2Vec2* world_vertices, int count, b2HexColor)
    //   draw_solid_polygon(b2Transform, const b2Vec2* local_vertices, int count, float radius, b2HexColor)
    //   draw_circle(b2Vec2 center, float radius, b2HexColor)
    //   draw_solid_circle(b2Transform center_transform, float radius, b2HexColor)
    //   draw_solid_capsule(b2Vec2 p1, b2Vec2 p2, float radius, b2HexColor)
    //   draw_segment(b2Vec2 p1, b2Vec2 p2, b2HexColor)
    //   draw_transform(b2Transform)
    //   draw_point(b2Vec2 p, float size, b2HexColor)
    //   draw_string(b2Vec2 p, const char* s, b2HexColor)
    //   draw_aabb(b2AABB, b2HexColor)
    template <class Derived>
    class DebugDraw : public b2DebugDraw
    {
    public:

        DebugDraw()
            : b2DebugDraw(b2DefaultDebugDraw())
        {
            DrawPolygonFcn = [](b2WorldTransform t, const b2Vec2* v, int n, b2HexColor c, void* ctx)
            {
                b2Vec2 stack[B2_MAX_POLYGON_VERTICES];
                std::vector<b2Vec2> heap;
                b2Vec2* world = stack;
                if (n > B2_MAX_POLYGON_VERTICES)
                {
                    heap.resize(n);
                    world = heap.data();
                }
                for (int i = 0; i < n; ++i)
                {
                    world[i] = b2TransformPoint(t, v[i]);
                }
                self(ctx)->draw_polygon(world, n, c);
            };
            DrawSolidPolygonFcn = [](b2WorldTransform t, const b2Vec2* v, int n, float r, b2HexColor c, void* ctx)
            {
                self(ctx)->draw_solid_polygon(t, v, n, r, c);
            };
            DrawCircleFcn = [](b2Pos center, float r, b2HexColor c, void* ctx)
            {
                self(ctx)->draw_circle(center, r, c);
            };
            DrawSolidCircleFcn = [](b2WorldTransform t, b2Vec2 center, float r, b2HexColor c, void* ctx)
            {
                self(ctx)->draw_solid_circle(b2Transform{b2TransformPoint(t, center), t.q}, r, c);
            };
            DrawSolidCapsuleFcn = [](b2Pos p1, b2Pos p2, float r, b2HexColor c, void* ctx)
            {
                self(ctx)->draw_solid_capsule(p1, p2, r, c);
            };
            DrawLineFcn = [](b2Pos p1, b2Pos p2, b2HexColor c, void* ctx)
            {
                self(ctx)->draw_segment(p1, p2, c);
            };
            DrawTransformFcn = [](b2WorldTransform t, void* ctx)
            {
                self(ctx)->draw_transform(t);
            };
            DrawPointFcn = [](b2Pos p, float size, b2HexColor c, void* ctx)
            {
                self(ctx)->draw_point(p, size, c);
            };
            DrawStringFcn = [](b2Pos p, const char* s, b2HexColor c, void* ctx)
            {
                self(ctx)->draw_string(p, s, c);
            };
            DrawBoundsFcn = [](b2AABB aabb, b2HexColor c, void* ctx)
            {
                self(ctx)->draw_aabb(aabb, c);
            };
            context = static_cast<void*>(this);
        }

    private:

        static Derived* self(void* ctx)
        {
            return static_cast<Derived*>(static_cast<DebugDraw*>(ctx));
        }
    };
}  // namespace pyb2d
