#pragma once

// Thin C++ handle types around the opaque box2d ids.
//
// box2d exposes free C functions like `b2Body_GetMass(bodyId)`. Plain 1:1 forwards
// are NOT written as member functions here: they are bound directly from the C
// function via `pyb2d3::Binder` (see core/binder.hpp). These structs only carry
// the id (through `pyb2d3::Handle`) plus logic that is not a 1:1 forward.
//
// Destroy() is a no-op for ids that are already gone (e.g. a joint destroyed together
// with its body): box2d asserts / crashes on stale ids. It keeps the id: box2d ids carry a
// generation, so a destroyed id is reported invalid, and the handle's hash / equality stay
// stable (a destroyed body can still be removed from a python set or dict).

#include <optional>
#include <stdexcept>

#include <box2d/box2d.h>
#include <box2d/math_functions.h>
#include <nanobind/nanobind.h>

#include "pyb2d3/core/handle.hpp"
#include "pyb2d3/py_chain_def.hpp"

namespace nb = nanobind;

struct Chain : pyb2d3::Handle<b2ChainId>
{
    using Handle::Handle;

    void Destroy()
    {
        if (IsValid())
        {
            b2DestroyChain(id);
        }
    }
};

struct Joint : pyb2d3::Handle<b2JointId>
{
    Joint(b2JointId id_)
        : Handle(id_)
    {
    }

    explicit Joint(uint64_t int_id)
        : Handle(int_id)
    {
    }

    void Destroy()
    {
        if (IsValid())
        {
            b2DestroyJoint(id);
        }
    }
};

// one subclass per joint type (only used for typed dispatch / python classes)
struct DistanceJoint : Joint
{
    using Joint::Joint;
};

struct FilterJoint : Joint
{
    using Joint::Joint;
};

struct MotorJoint : Joint
{
    using Joint::Joint;
};

struct MoverJoint : Joint
{
    using Joint::Joint;
};

struct PogoJoint : Joint
{
    using Joint::Joint;
};

struct PrismaticJoint : Joint
{
    using Joint::Joint;
};

struct RevoluteJoint : Joint
{
    using Joint::Joint;
};

struct WeldJoint : Joint
{
    using Joint::Joint;
};

struct WheelJoint : Joint
{
    using Joint::Joint;
};

struct Shape : pyb2d3::Handle<b2ShapeId>
{
    Shape(b2ShapeId id_)
        : Handle(id_)
    {
    }

    explicit Shape(uint64_t int_id)
        : Handle(int_id)
    {
    }

    void Destroy(bool updateBodyMass)
    {
        if (IsValid())
        {
            b2DestroyShape(id, updateBodyMass);
        }
    }
};

struct CircleShape : Shape
{
    using Shape::Shape;
};

struct CapsuleShape : Shape
{
    using Shape::Shape;
};

struct SegmentShape : Shape
{
    using Shape::Shape;
};

struct PolygonShape : Shape
{
    using Shape::Shape;
};

struct ChainSegmentShape : Shape
{
    using Shape::Shape;
};

struct Body : pyb2d3::Handle<b2BodyId>
{
    using Handle::Handle;

    void Destroy()
    {
        if (IsValid())
        {
            b2DestroyBody(id);
        }
    }
};

// contact ids are 96 bit and have no user data, so they are not a pyb2d3::Handle
struct Contact
{
    b2ContactId id;

    bool IsValid() const
    {
        return b2Contact_IsValid(id);
    }

    bool operator==(const Contact& o) const
    {
        return id.index1 == o.id.index1 && id.world0 == o.id.world0 && id.generation == o.id.generation;
    }
};

struct WorldView : pyb2d3::Handle<b2WorldId>
{
    using Handle::Handle;

    void Destroy()
    {
        if (b2World_IsValid(id))
        {
            b2DestroyWorld(id);
        }
    }

    // first shape (optionally only shapes on dynamic bodies) containing `point`
    std::optional<b2ShapeId> ShapeAtPoint(b2Vec2 point, b2QueryFilter filter, bool dynamicOnly) const
    {
        struct Context
        {
            b2Vec2 point;
            bool dynamicOnly;
            std::optional<b2ShapeId> result;
        } context{point, dynamicOnly, std::nullopt};

        const b2Vec2 d{0.001f, 0.001f};
        const b2AABB box{b2Neg(d), d};

        b2World_OverlapAABB(
            id,
            point,
            box,
            filter,
            [](b2ShapeId shapeId, void* ctx) -> bool
            {
                auto* c = static_cast<Context*>(ctx);
                if (c->dynamicOnly && b2Body_GetType(b2Shape_GetBody(shapeId)) != b2_dynamicBody)
                {
                    return true;
                }
                if (b2Shape_TestPoint(shapeId, c->point))
                {
                    c->result = shapeId;
                    return false;
                }
                return true;
            },
            &context
        );
        return context.result;
    }

    std::optional<b2BodyId> BodyAtPoint(b2Vec2 point, b2QueryFilter filter, bool dynamicOnly) const
    {
        if (auto shape = ShapeAtPoint(point, filter, dynamicOnly))
        {
            return b2Shape_GetBody(*shape);
        }
        return std::nullopt;
    }
};

// typed python object for a shape / joint id (e.g. a CircleShape for a circle)
inline nb::object GetCastedShape(b2ShapeId shapeId)
{
    switch (b2Shape_GetType(shapeId))
    {
        case b2_circleShape:
            return nb::cast(CircleShape(shapeId));
        case b2_capsuleShape:
            return nb::cast(CapsuleShape(shapeId));
        case b2_segmentShape:
            return nb::cast(SegmentShape(shapeId));
        case b2_polygonShape:
            return nb::cast(PolygonShape(shapeId));
        case b2_chainSegmentShape:
            return nb::cast(ChainSegmentShape(shapeId));
        default:
            throw std::runtime_error("Invalid shape type");
    }
}

inline nb::object GetCastedJoint(b2JointId jointId)
{
    switch (b2Joint_GetType(jointId))
    {
        case b2_distanceJoint:
            return nb::cast(DistanceJoint(jointId));
        case b2_filterJoint:
            return nb::cast(FilterJoint(jointId));
        case b2_motorJoint:
            return nb::cast(MotorJoint(jointId));
        case b2_moverJoint:
            return nb::cast(MoverJoint(jointId));
        case b2_pogoJoint:
            return nb::cast(PogoJoint(jointId));
        case b2_prismaticJoint:
            return nb::cast(PrismaticJoint(jointId));
        case b2_revoluteJoint:
            return nb::cast(RevoluteJoint(jointId));
        case b2_weldJoint:
            return nb::cast(WeldJoint(jointId));
        case b2_wheelJoint:
            return nb::cast(WheelJoint(jointId));
        default:
            throw std::runtime_error("Invalid joint type");
    }
}
