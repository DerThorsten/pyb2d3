#pragma once

// extern "C"
// {
#include <box2d/box2d.h>
#include <box2d/math_functions.h>
#include <box2d/types.h>

// }

namespace pyb2d
{
    namespace detail
    {
        template <class CLS>
        void GenericDrawPolygon(const b2Vec2* vertices, int vertexCount, b2HexColor color, void* context)
        {
            reinterpret_cast<CLS*>(context)->draw_polygon(vertices, vertexCount, color);
        }

        template <class CLS>
        void GenericDrawSolidPolygon(
            b2Transform transform,
            const b2Vec2* vertices,
            int vertexCount,
            float radius,
            b2HexColor color,
            void* context
        )
        {
            reinterpret_cast<CLS*>(context)->draw_solid_polygon(transform, vertices, vertexCount, radius, color);
        }

        template <class CLS>
        void GenericDrawCircle(b2Vec2 center, float radius, b2HexColor color, void* context)
        {
            reinterpret_cast<CLS*>(context)->draw_circle(center, radius, color);
        }

        template <class CLS>
        void GenericDrawSolidCircle(b2Transform transform, float radius, b2HexColor color, void* context)
        {
            reinterpret_cast<CLS*>(context)->draw_solid_cirlce(transform, radius, color);
        }

        template <class CLS>
        void GenericDrawSolidCapsule(b2Vec2 p1, b2Vec2 p2, float radius, b2HexColor color, void* context)
        {
            reinterpret_cast<CLS*>(context)->draw_solid_capsule(p1, p2, radius, color);
        }

        template <class CLS>
        void GenericDrawSegment(b2Vec2 p1, b2Vec2 p2, b2HexColor color, void* context)
        {
            reinterpret_cast<CLS*>(context)->draw_segment(p1, p2, color);
        }

        template <class CLS>
        void GenericDrawTransform(b2Transform transform, void* context)
        {
            reinterpret_cast<CLS*>(context)->draw_transform(transform);
        }

        template <class CLS>
        void GenericDrawPoint(b2Vec2 p, float size, b2HexColor color, void* context)
        {
            reinterpret_cast<CLS*>(context)->draw_point(p, size, color);
        }

        template <class CLS>
        void GenericDrawString(b2Vec2 p, const char* s, b2HexColor color, void* context)
        {
            reinterpret_cast<CLS*>(context)->draw_string(p, s, color);
        }
    }  // namespace detail

    template <class Derived>
    class DebugDraw : public b2DebugDraw
    {
    public:

        DebugDraw()
        {
            this->DrawPolygonFcn = detail::GenericDrawPolygon<Derived>;
            this->DrawSolidPolygonFcn = detail::GenericDrawSolidPolygon<Derived>;
            this->DrawCircleFcn = detail::GenericDrawCircle<Derived>;
            this->DrawSolidCircleFcn = detail::GenericDrawSolidCircle<Derived>;
            this->DrawSolidCapsuleFcn = detail::GenericDrawSolidCapsule<Derived>;
            this->DrawSegmentFcn = detail::GenericDrawSegment<Derived>;
            this->DrawTransformFcn = detail::GenericDrawTransform<Derived>;
            this->DrawPointFcn = detail::GenericDrawPoint<Derived>;
            this->DrawStringFcn = detail::GenericDrawString<Derived>;
            this->context = reinterpret_cast<void*>(this);
        }

        void draw_polygon(const b2Vec2* vertices, int vertexCount, b2HexColor color)
        {
            this->derived_cast()->draw_polygon(vertices, vertexCount, color);
        }

        void
        draw_solid_polygon(b2Transform transform, const b2Vec2* vertices, int vertexCount, float radius, b2HexColor color)
        {
            this->derived_cast()->draw_solid_polygon(transform, vertices, vertexCount, radius, color);
        }

        void draw_circle(b2Vec2 center, float radius, b2HexColor color)
        {
            this->derived_cast()->draw_circle(center, radius, color);
        }

        void draw_solid_cirlce(b2Transform transform, float radius, b2HexColor color)
        {
            this->derived_cast()->draw_solid_cirlce(transform, radius, color);
        }

        void draw_solid_capsule(b2Vec2 p1, b2Vec2 p2, float radius, b2HexColor color)
        {
            this->derived_cast()->draw_solid_capsule(p1, p2, radius, color);
        }

        void draw_segment(b2Vec2 p1, b2Vec2 p2, b2HexColor color)
        {
            this->derived_cast()->draw_segment(p1, p2, color);
        }

        void draw_transform(b2Transform transform)
        {
            this->derived_cast()->draw_transform(transform);
        }

        void draw_point(b2Vec2 p, float size, b2HexColor color)
        {
            this->derived_cast()->draw_point(p, size, color);
        }

        void draw_string(b2Vec2 p, const char* s, b2HexColor color)
        {
            this->derived_cast()->draw_string(p, s, color);
        }

    private:

        Derived* derived_cast()
        {
            return static_cast<Derived*>(this);
        }
    };

    // // *CollectingDebugDraw* is a DebugDraw that collects the data that would be
    // drawn
    // // by the *DebugDraw* methods. This is useful when drawing in languages like
    // Python.
    // // We absolutely want to minimize the number of times we need to cross the
    // language
    // // barrier, so we collect the data in C++ and and then convert it to numpy
    // arrays.
    // // On the python side we can then call functions like **draw_polygons** (note
    // the plural)
    // // that will draw all the polygons in one go. This way, the number of times
    // we cross
    // // the language barrier is constant and independent of the number of shapes
    // we want to draw.
    // //
    // // The Transform template parameter is a class that will be used to apply
    // // arbitrary transformations to the coordinats, length units, and colors.
    // // This is usefull to already apply world to screen transformations in C++.
    // // Furthermore this can be used to already round floats to screen pixel
    // integers. template<class TRANSFORM> class CollectingDebugDraw : public
    // DebugDraw<CollectingDebugDraw<TRANSFORM>>
    // {
    //     public:
    //         using transform_type = TRANSFORM;
    //         using t_coord = typename TRANSFORM::t_coord;
    //         using t_color = typename TRANSFORM::t_color;
    //         using t_scale = typename TRANSFORM::t_scale;

    //         void draw_polygon(const b2Vec2* vertices, int vertexCount, b2HexColor
    //         color)
    //         {
    //             for(int i = 0; i < vertexCount; i++)
    //             {
    //                 m_draw_polygon_vertices.push_back(transform.coordinate(vertices[i]));
    //             }
    //             m_draw_polygon_acc_vertex_counts.push_back(
    //             m_draw_polygon_acc_vertex_counts.empty() ? vertexCount :
    //             m_draw_polygon_acc_vertex_counts.back() + vertexCount );
    //             m_draw_polygon_colors.push_back(transform.color(color));
    //         }

    //         void draw_solid_polygon(b2Transform t, const b2Vec2* vertices, int
    //         vertexCount, float radius, b2HexColor color)
    //         {
    //         }

    //         void draw_circle(b2Vec2 center, float radius, b2HexColor color)
    //         {
    //         }

    //         void draw_solid_cirlce(b2Transform t, float radius, b2HexColor color)
    //         {
    //         }

    //         void draw_solid_capsule(b2Vec2 p1, b2Vec2 p2, float radius,
    //         b2HexColor color)
    //         {
    //         }

    //         void draw_segment(b2Vec2 p1, b2Vec2 p2, b2HexColor color)
    //         {
    //         }

    //         void draw_transform(b2Transform t)
    //         {
    //         }

    //         void draw_point(b2Vec2 p, float size, b2HexColor color)
    //         {
    //         }

    //         void draw_string(b2Vec2 p, const char* s)
    //         {
    //         }
    //     private:
    //         TRANSFORM transform;

    //         // collected data

    //         // *draw_polygon* data
    //         std::vector<t_coord> m_draw_polygon_vertices;
    //         std::vector<int> m_draw_polygon_acc_vertex_counts;
    //         std::vector<t_color> m_draw_polygon_colors;

    // };

}  // namespace pyb2d
