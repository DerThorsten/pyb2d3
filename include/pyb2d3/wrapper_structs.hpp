#pragma once

#include <optional>

#include <box2d/box2d.h>
#include <box2d/math_functions.h>

#include "py_chain_def.hpp"

namespace nb = nanobind;

struct WorldView;
struct Body;
struct Shape;
struct Chain;
struct Joint;

/*

/// Create a chain shape
/// @see b2ChainDef for details
B2_API b2ChainId b2CreateChain( b2BodyId bodyId, const b2ChainDef* def );

/// Destroy a chain shape
B2_API void b2DestroyChain( b2ChainId chainId );

/// Get the world that owns this chain shape
B2_API b2WorldId b2Chain_GetWorld( b2ChainId chainId );

/// Get the number of segments on this chain
B2_API int b2Chain_GetSegmentCount( b2ChainId chainId );

/// Fill a user array with chain segment shape ids up to the specified capacity. Returns
/// the actual number of segments returned.
B2_API int b2Chain_GetSegments( b2ChainId chainId, b2ShapeId* segmentArray, int capacity );

/// Set the chain friction
/// @see b2ChainDef::friction
B2_API void b2Chain_SetFriction( b2ChainId chainId, float friction );

/// Get the chain friction
B2_API float b2Chain_GetFriction( b2ChainId chainId );

/// Set the chain restitution (bounciness)
/// @see b2ChainDef::restitution
B2_API void b2Chain_SetRestitution( b2ChainId chainId, float restitution );

/// Get the chain restitution
B2_API float b2Chain_GetRestitution( b2ChainId chainId );

/// Set the chain material
/// @see b2ChainDef::material
B2_API void b2Chain_SetMaterial( b2ChainId chainId, int material );

/// Get the chain material
B2_API int b2Chain_GetMaterial( b2ChainId chainId );

/// Chain identifier validation. Provides validation for up to 64K allocations.
B2_API bool b2Chain_IsValid( b2ChainId id );
*/
struct Chain
{
    using id_type = b2ChainId;

    static auto int_to_id(uint64_t id) -> id_type
    {
        return b2LoadChainId(id);
    }

    static auto id_to_int(id_type id) -> uint64_t
    {
        return b2StoreChainId(id);
    }

    b2ChainId id;

    inline Chain(b2ChainId chainId)
        : id(chainId)
    {
    }

    inline Chain(uint64_t chain_id)
        : id(b2LoadChainId(chain_id))
    {
    }

    inline bool IsValid() const
    {
        return b2Chain_IsValid(id);
    }

    inline b2WorldId GetWorld() const
    {
        return b2Chain_GetWorld(id);
    }

    inline int GetSegmentCount() const
    {
        return b2Chain_GetSegmentCount(id);
    }

    inline int GetSegments(b2ShapeId* segmentArray, int capacity) const
    {
        return b2Chain_GetSegments(id, segmentArray, capacity);
    }

    inline void SetFriction(float friction)
    {
        b2Chain_SetFriction(id, friction);
    }

    inline float GetFriction() const
    {
        return b2Chain_GetFriction(id);
    }

    inline void SetRestitution(float restitution)
    {
        b2Chain_SetRestitution(id, restitution);
    }

    inline float GetRestitution() const
    {
        return b2Chain_GetRestitution(id);
    }

    inline void SetMaterial(int material)
    {
        b2Chain_SetMaterial(id, material);
    }

    inline int GetMaterial() const
    {
        return b2Chain_GetMaterial(id);
    }
};

struct Joint
{
    b2JointId id;
    using id_type = b2JointId;

    static auto int_to_id(uint64_t id) -> id_type
    {
        return b2LoadJointId(id);
    }

    static auto id_to_int(id_type id) -> uint64_t
    {
        return b2StoreJointId(id);
    }

    inline Joint(b2JointId jointId)
        : id(jointId)
    {
    }

    inline Joint(uint64_t joint_id)
        : id(b2LoadJointId(joint_id))
    {
    }

    inline bool IsValid() const
    {
        return b2Joint_IsValid(id);
    }

    inline void Destroy()
    {
        b2DestroyJoint(id);
        id = b2_nullJointId;
    }

    inline b2JointType GetType() const
    {
        return b2Joint_GetType(id);
    }

    inline b2BodyId GetBodyA() const
    {
        return b2Joint_GetBodyA(id);
    }

    inline b2BodyId GetBodyB() const
    {
        return b2Joint_GetBodyB(id);
    }

    inline b2WorldId GetWorld() const
    {
        return b2Joint_GetWorld(id);
    }

    inline b2Vec2 GetLocalAnchorA() const
    {
        return b2Joint_GetLocalAnchorA(id);
    }

    inline b2Vec2 GetLocalAnchorB() const
    {
        return b2Joint_GetLocalAnchorB(id);
    }

    inline void SetCollideConnected(bool shouldCollide)
    {
        b2Joint_SetCollideConnected(id, shouldCollide);
    }

    inline bool GetCollideConnected() const
    {
        return b2Joint_GetCollideConnected(id);
    }

    inline void SetUserData(void* userData)
    {
        b2Joint_SetUserData(id, userData);
    }

    inline void* GetUserData() const
    {
        return b2Joint_GetUserData(id);
    }

    inline void WakeBodies()
    {
        b2Joint_WakeBodies(id);
    }

    inline b2Vec2 GetConstraintForce() const
    {
        return b2Joint_GetConstraintForce(id);
    }

    inline float GetConstraintTorque() const
    {
        return b2Joint_GetConstraintTorque(id);
    }

    // get and set reference angle
    inline float GetReferenceAngle() const
    {
        return b2Joint_GetReferenceAngle(id);
    }

    inline void SetReferenceAngle(float angle)
    {
        b2Joint_SetReferenceAngle(id, angle);
    }
};

struct DistanceJoint : public Joint
{
    using Joint::Joint;

    inline void SetLength(float length)
    {
        b2DistanceJoint_SetLength(id, length);
    }

    inline float GetLength() const
    {
        return b2DistanceJoint_GetLength(id);
    }

    inline void EnableSpring(bool enableSpring)
    {
        b2DistanceJoint_EnableSpring(id, enableSpring);
    }

    inline bool IsSpringEnabled() const
    {
        return b2DistanceJoint_IsSpringEnabled(id);
    }

    inline void SetSpringHertz(float hertz)
    {
        b2DistanceJoint_SetSpringHertz(id, hertz);
    }

    inline float GetSpringHertz() const
    {
        return b2DistanceJoint_GetSpringHertz(id);
    }

    inline void SetSpringDampingRatio(float dampingRatio)
    {
        b2DistanceJoint_SetSpringDampingRatio(id, dampingRatio);
    }

    inline float GetSpringDampingRatio() const
    {
        return b2DistanceJoint_GetSpringDampingRatio(id);
    }

    inline void EnableLimit(bool enableLimit)
    {
        b2DistanceJoint_EnableLimit(id, enableLimit);
    }

    inline bool IsLimitEnabled() const
    {
        return b2DistanceJoint_IsLimitEnabled(id);
    }

    inline void SetLengthRange(float minLength, float maxLength)
    {
        b2DistanceJoint_SetLengthRange(id, minLength, maxLength);
    }

    inline float GetMinLength() const
    {
        return b2DistanceJoint_GetMinLength(id);
    }

    inline float GetMaxLength() const
    {
        return b2DistanceJoint_GetMaxLength(id);
    }

    inline float GetCurrentLength() const
    {
        return b2DistanceJoint_GetCurrentLength(id);
    }

    inline void EnableMotor(bool enableMotor)
    {
        b2DistanceJoint_EnableMotor(id, enableMotor);
    }

    inline bool IsMotorEnabled() const
    {
        return b2DistanceJoint_IsMotorEnabled(id);
    }

    inline void SetMotorSpeed(float motorSpeed)
    {
        b2DistanceJoint_SetMotorSpeed(id, motorSpeed);
    }

    inline float GetMotorSpeed() const
    {
        return b2DistanceJoint_GetMotorSpeed(id);
    }

    inline void SetMaxMotorForce(float maxForce)
    {
        b2DistanceJoint_SetMaxMotorForce(id, maxForce);
    }

    inline float GetMaxMotorForce() const
    {
        return b2DistanceJoint_GetMaxMotorForce(id);
    }

    inline float GetMotorForce() const
    {
        return b2DistanceJoint_GetMotorForce(id);
    }
};

struct FilterJoint : public Joint
{
    using Joint::Joint;
};

struct MotorJoint : public Joint
{
    using Joint::Joint;

    inline void SetLinearOffset(b2Vec2 linearOffset)
    {
        b2MotorJoint_SetLinearOffset(id, linearOffset);
    }

    inline b2Vec2 GetLinearOffset() const
    {
        return b2MotorJoint_GetLinearOffset(id);
    }

    inline void SetAngularOffset(float angularOffset)
    {
        b2MotorJoint_SetAngularOffset(id, angularOffset);
    }

    inline float GetAngularOffset() const
    {
        return b2MotorJoint_GetAngularOffset(id);
    }

    inline void SetMaxForce(float maxForce)
    {
        b2MotorJoint_SetMaxForce(id, maxForce);
    }

    inline float GetMaxForce() const
    {
        return b2MotorJoint_GetMaxForce(id);
    }

    inline void SetMaxTorque(float maxTorque)
    {
        b2MotorJoint_SetMaxTorque(id, maxTorque);
    }

    inline float GetMaxTorque() const
    {
        return b2MotorJoint_GetMaxTorque(id);
    }

    inline void SetCorrectionFactor(float correctionFactor)
    {
        b2MotorJoint_SetCorrectionFactor(id, correctionFactor);
    }

    inline float GetCorrectionFactor() const
    {
        return b2MotorJoint_GetCorrectionFactor(id);
    }
};

struct MouseJoint : public Joint
{
    using Joint::Joint;

    inline void SetTarget(b2Vec2 target)
    {
        b2MouseJoint_SetTarget(id, target);
    }

    inline b2Vec2 GetTarget() const
    {
        return b2MouseJoint_GetTarget(id);
    }

    inline void SetSpringHertz(float hertz)
    {
        b2MouseJoint_SetSpringHertz(id, hertz);
    }

    inline float GetSpringHertz() const
    {
        return b2MouseJoint_GetSpringHertz(id);
    }

    inline void SetSpringDampingRatio(float dampingRatio)
    {
        b2MouseJoint_SetSpringDampingRatio(id, dampingRatio);
    }

    inline float GetSpringDampingRatio() const
    {
        return b2MouseJoint_GetSpringDampingRatio(id);
    }

    inline void SetMaxForce(float maxForce)
    {
        b2MouseJoint_SetMaxForce(id, maxForce);
    }

    inline float GetMaxForce() const
    {
        return b2MouseJoint_GetMaxForce(id);
    }
};

struct PrismaticJoint : public Joint
{
    using Joint::Joint;

    inline void EnableSpring(bool enableSpring)
    {
        b2PrismaticJoint_EnableSpring(id, enableSpring);
    }

    inline bool IsSpringEnabled() const
    {
        return b2PrismaticJoint_IsSpringEnabled(id);
    }

    inline void SetSpringHertz(float hertz)
    {
        b2PrismaticJoint_SetSpringHertz(id, hertz);
    }

    inline float GetSpringHertz() const
    {
        return b2PrismaticJoint_GetSpringHertz(id);
    }

    inline void SetSpringDampingRatio(float dampingRatio)
    {
        b2PrismaticJoint_SetSpringDampingRatio(id, dampingRatio);
    }

    inline float GetSpringDampingRatio() const
    {
        return b2PrismaticJoint_GetSpringDampingRatio(id);
    }

    inline void EnableLimit(bool enableLimit)
    {
        b2PrismaticJoint_EnableLimit(id, enableLimit);
    }

    inline bool IsLimitEnabled() const
    {
        return b2PrismaticJoint_IsLimitEnabled(id);
    }

    inline void SetLimits(float lower, float upper)
    {
        b2PrismaticJoint_SetLimits(id, lower, upper);
    }

    inline float GetLowerLimit() const
    {
        return b2PrismaticJoint_GetLowerLimit(id);
    }

    inline float GetUpperLimit() const
    {
        return b2PrismaticJoint_GetUpperLimit(id);
    }

    inline void EnableMotor(bool enableMotor)
    {
        b2PrismaticJoint_EnableMotor(id, enableMotor);
    }

    inline bool IsMotorEnabled() const
    {
        return b2PrismaticJoint_IsMotorEnabled(id);
    }

    inline void SetMotorSpeed(float motorSpeed)
    {
        b2PrismaticJoint_SetMotorSpeed(id, motorSpeed);
    }

    inline float GetMotorSpeed() const
    {
        return b2PrismaticJoint_GetMotorSpeed(id);
    }

    inline void SetMaxMotorForce(float force)
    {
        b2PrismaticJoint_SetMaxMotorForce(id, force);
    }

    inline float GetMaxMotorForce() const
    {
        return b2PrismaticJoint_GetMaxMotorForce(id);
    }

    inline float GetMotorForce() const
    {
        return b2PrismaticJoint_GetMotorForce(id);
    }

    inline float GetTranslation() const
    {
        return b2PrismaticJoint_GetTranslation(id);
    }

    inline float GetSpeed() const
    {
        return b2PrismaticJoint_GetSpeed(id);
    }
};

struct RevoluteJoint : public Joint
{
    using Joint::Joint;

    inline void EnableSpring(bool enableSpring)
    {
        b2RevoluteJoint_EnableSpring(id, enableSpring);
    }

    inline bool IsSpringEnabled() const
    {
        return b2RevoluteJoint_IsSpringEnabled(id);
    }

    inline void SetSpringHertz(float hertz)
    {
        b2RevoluteJoint_SetSpringHertz(id, hertz);
    }

    inline float GetSpringHertz() const
    {
        return b2RevoluteJoint_GetSpringHertz(id);
    }

    inline void SetSpringDampingRatio(float dampingRatio)
    {
        b2RevoluteJoint_SetSpringDampingRatio(id, dampingRatio);
    }

    inline float GetSpringDampingRatio() const
    {
        return b2RevoluteJoint_GetSpringDampingRatio(id);
    }

    inline float GetAngle() const
    {
        return b2RevoluteJoint_GetAngle(id);
    }

    inline void EnableLimit(bool enableLimit)
    {
        b2RevoluteJoint_EnableLimit(id, enableLimit);
    }

    inline bool IsLimitEnabled() const
    {
        return b2RevoluteJoint_IsLimitEnabled(id);
    }

    inline float GetLowerLimit() const
    {
        return b2RevoluteJoint_GetLowerLimit(id);
    }

    inline float GetUpperLimit() const
    {
        return b2RevoluteJoint_GetUpperLimit(id);
    }

    inline void SetLimits(float lower, float upper)
    {
        b2RevoluteJoint_SetLimits(id, lower, upper);
    }

    inline void EnableMotor(bool enableMotor)
    {
        b2RevoluteJoint_EnableMotor(id, enableMotor);
    }

    inline bool IsMotorEnabled() const
    {
        return b2RevoluteJoint_IsMotorEnabled(id);
    }

    inline void SetMotorSpeed(float motorSpeed)
    {
        b2RevoluteJoint_SetMotorSpeed(id, motorSpeed);
    }

    inline float GetMotorSpeed() const
    {
        return b2RevoluteJoint_GetMotorSpeed(id);
    }

    inline float GetMotorTorque() const
    {
        return b2RevoluteJoint_GetMotorTorque(id);
    }

    inline void SetMaxMotorTorque(float torque)
    {
        b2RevoluteJoint_SetMaxMotorTorque(id, torque);
    }

    inline float GetMaxMotorTorque() const
    {
        return b2RevoluteJoint_GetMaxMotorTorque(id);
    }
};

struct WeldJoint : public Joint
{
    using Joint::Joint;

    inline void SetLinearHertz(float hertz)
    {
        b2WeldJoint_SetLinearHertz(id, hertz);
    }

    inline float GetLinearHertz() const
    {
        return b2WeldJoint_GetLinearHertz(id);
    }

    inline void SetLinearDampingRatio(float dampingRatio)
    {
        b2WeldJoint_SetLinearDampingRatio(id, dampingRatio);
    }

    inline float GetLinearDampingRatio() const
    {
        return b2WeldJoint_GetLinearDampingRatio(id);
    }

    inline void SetAngularHertz(float hertz)
    {
        b2WeldJoint_SetAngularHertz(id, hertz);
    }

    inline float GetAngularHertz() const
    {
        return b2WeldJoint_GetAngularHertz(id);
    }

    inline void SetAngularDampingRatio(float dampingRatio)
    {
        b2WeldJoint_SetAngularDampingRatio(id, dampingRatio);
    }

    inline float GetAngularDampingRatio() const
    {
        return b2WeldJoint_GetAngularDampingRatio(id);
    }
};

struct WheelJoint : public Joint
{
    using Joint::Joint;

    inline void EnableSpring(bool enableSpring)
    {
        b2WheelJoint_EnableSpring(id, enableSpring);
    }

    inline bool IsSpringEnabled() const
    {
        return b2WheelJoint_IsSpringEnabled(id);
    }

    inline void SetSpringHertz(float hertz)
    {
        b2WheelJoint_SetSpringHertz(id, hertz);
    }

    inline float GetSpringHertz() const
    {
        return b2WheelJoint_GetSpringHertz(id);
    }

    inline void SetSpringDampingRatio(float dampingRatio)
    {
        b2WheelJoint_SetSpringDampingRatio(id, dampingRatio);
    }

    inline float GetSpringDampingRatio() const
    {
        return b2WheelJoint_GetSpringDampingRatio(id);
    }

    inline void EnableLimit(bool enableLimit)
    {
        b2WheelJoint_EnableLimit(id, enableLimit);
    }

    inline bool IsLimitEnabled() const
    {
        return b2WheelJoint_IsLimitEnabled(id);
    }

    inline void SetLimits(float lower, float upper)
    {
        b2WheelJoint_SetLimits(id, lower, upper);
    }

    inline float GetLowerLimit() const
    {
        return b2WheelJoint_GetLowerLimit(id);
    }

    inline float GetUpperLimit() const
    {
        return b2WheelJoint_GetUpperLimit(id);
    }

    inline void EnableMotor(bool enableMotor)
    {
        b2WheelJoint_EnableMotor(id, enableMotor);
    }

    inline bool IsMotorEnabled() const
    {
        return b2WheelJoint_IsMotorEnabled(id);
    }

    inline void SetMotorSpeed(float motorSpeed)
    {
        b2WheelJoint_SetMotorSpeed(id, motorSpeed);
    }

    inline float GetMotorSpeed() const
    {
        return b2WheelJoint_GetMotorSpeed(id);
    }

    inline void SetMaxMotorTorque(float torque)
    {
        b2WheelJoint_SetMaxMotorTorque(id, torque);
    }

    inline float GetMaxMotorTorque() const
    {
        return b2WheelJoint_GetMaxMotorTorque(id);
    }

    inline float GetMotorTorque() const
    {
        return b2WheelJoint_GetMotorTorque(id);
    }
};

// // for consitency with the other IDs
// inline uint64_t b2StoreWorldId(b2WorldId id)
// {
//     return ((uint64_t) id.index1 << 16) | ((uint64_t) id.generation);
// }

// inline b2WorldId b2LoadWorldId(uint64_t x)
// {
//     b2WorldId id = {(uint16_t) (x >> 16), (uint16_t) (x)};
//     return id;
// }

struct Shape
{
    b2ShapeId id;

    using id_type = b2ShapeId;

    static auto int_to_id(uint64_t id) -> id_type
    {
        return b2LoadShapeId(id);
    }

    static auto id_to_int(id_type id) -> uint64_t
    {
        return b2StoreShapeId(id);
    }

    inline Shape(b2ShapeId shapeId)
        : id(shapeId)
    {
    }

    inline Shape(uint64_t shapeId)
        : id(b2LoadShapeId(shapeId))
    {
    }

    void Destroy(bool updateBodyMass)
    {
        b2DestroyShape(id, updateBodyMass);
    }

    inline bool IsValid() const
    {
        return b2Shape_IsValid(id);
    }

    inline b2ShapeType GetType() const
    {
        return b2Shape_GetType(id);
    }

    inline b2BodyId GetBody() const
    {
        return b2Shape_GetBody(id);
    }

    inline b2WorldId GetWorld() const
    {
        return b2Shape_GetWorld(id);
    }

    inline bool IsSensor() const
    {
        return b2Shape_IsSensor(id);
    }

    inline void SetUserData(void* userData)
    {
        b2Shape_SetUserData(id, userData);
    }

    inline void* GetUserData() const
    {
        return b2Shape_GetUserData(id);
    }

    inline void SetDensity(float density, bool updateBodyMass)
    {
        b2Shape_SetDensity(id, density, updateBodyMass);
    }

    inline float GetDensity() const
    {
        return b2Shape_GetDensity(id);
    }

    inline void SetFriction(float friction)
    {
        b2Shape_SetFriction(id, friction);
    }

    inline float GetFriction() const
    {
        return b2Shape_GetFriction(id);
    }

    inline void SetRestitution(float restitution)
    {
        b2Shape_SetRestitution(id, restitution);
    }

    inline float GetRestitution() const
    {
        return b2Shape_GetRestitution(id);
    }

    inline void SetMaterial(int material)
    {
        b2Shape_SetMaterial(id, material);
    }

    inline int GetMaterial() const
    {
        return b2Shape_GetMaterial(id);
    }

    inline b2Filter GetFilter() const
    {
        return b2Shape_GetFilter(id);
    }

    inline void SetFilter(b2Filter filter)
    {
        b2Shape_SetFilter(id, filter);
    }

    inline void EnableSensorEvents(bool flag)
    {
        b2Shape_EnableSensorEvents(id, flag);
    }

    inline bool AreSensorEventsEnabled() const
    {
        return b2Shape_AreSensorEventsEnabled(id);
    }

    inline void EnableContactEvents(bool flag)
    {
        b2Shape_EnableContactEvents(id, flag);
    }

    inline bool AreContactEventsEnabled() const
    {
        return b2Shape_AreContactEventsEnabled(id);
    }

    inline void EnablePreSolveEvents(bool flag)
    {
        b2Shape_EnablePreSolveEvents(id, flag);
    }

    inline bool ArePreSolveEventsEnabled() const
    {
        return b2Shape_ArePreSolveEventsEnabled(id);
    }

    inline void EnableHitEvents(bool flag)
    {
        b2Shape_EnableHitEvents(id, flag);
    }

    inline bool AreHitEventsEnabled() const
    {
        return b2Shape_AreHitEventsEnabled(id);
    }

    inline bool TestPoint(b2Vec2 point) const
    {
        return b2Shape_TestPoint(id, point);
    }

    inline b2CastOutput RayCast(const b2RayCastInput* input) const
    {
        return b2Shape_RayCast(id, input);
    }
};

struct CircleShape : public Shape
{
    using Shape::Shape;

    inline b2Circle GetCircle() const
    {
        return b2Shape_GetCircle(id);
    }

    inline void SetCircle(const b2Circle* circle)
    {
        b2Shape_SetCircle(id, circle);
    }
};

struct CapsuleShape : public Shape
{
    using Shape::Shape;

    inline b2Capsule GetCapsule() const
    {
        return b2Shape_GetCapsule(id);
    }

    inline void SetCapsule(const b2Capsule* capsule)
    {
        b2Shape_SetCapsule(id, capsule);
    }
};

struct SegmentShape : public Shape
{
    using Shape::Shape;

    inline b2Segment GetSegment() const
    {
        return b2Shape_GetSegment(id);
    }

    inline void SetSegment(const b2Segment* segment)
    {
        b2Shape_SetSegment(id, segment);
    }
};

struct PolygonShape : public Shape
{
    using Shape::Shape;

    inline b2Polygon GetPolygon() const
    {
        return b2Shape_GetPolygon(id);
    }

    inline void SetPolygon(const b2Polygon* polygon)
    {
        b2Shape_SetPolygon(id, polygon);
    }
};

struct ChainSegmentShape : public Shape
{
    inline ChainSegmentShape(b2ShapeId shapeId)
        : Shape(shapeId)
    {
    }

    inline ChainSegmentShape(uint64_t shapeId)
        : Shape(shapeId)
    {
    }

    inline b2ChainSegment GetChainSegment() const
    {
        return b2Shape_GetChainSegment(id);
    }

    inline b2ChainId GetParentChain() const
    {
        return b2Shape_GetParentChain(id);
    }
};

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
            // This should never happen if the shape is valid
            throw std::runtime_error("Invalid shape type");
            return nb::none();
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
        case b2_mouseJoint:
            return nb::cast(MouseJoint(jointId));
        case b2_prismaticJoint:
            return nb::cast(PrismaticJoint(jointId));
        case b2_revoluteJoint:
            return nb::cast(RevoluteJoint(jointId));
        case b2_weldJoint:
            return nb::cast(WeldJoint(jointId));
        case b2_wheelJoint:
            return nb::cast(WheelJoint(jointId));
        default:
            // This should never happen if the joint is valid
            throw std::runtime_error("Invalid joint type");
            return nb::none();
    }
}

struct Body
{
    b2BodyId id;

    using id_type = b2BodyId;

    static auto int_to_id(uint64_t id) -> id_type
    {
        return b2LoadBodyId(id);
    }

    static auto id_to_int(id_type id) -> uint64_t
    {
        return b2StoreBodyId(id);
    }

    // inline Body() { id = b2InvalidBodyId; }
    inline Body(b2BodyId bodyId)
        : id(bodyId)
    {
    }

    inline Body(uint64_t bodyId)
        : id(b2LoadBodyId(bodyId))
    {
    }

    inline void Destroy()
    {
        b2DestroyBody(id);
        id = b2_nullBodyId;  // Invalidate the ID after destruction
    }

    inline bool IsValid() const
    {
        return b2Body_IsValid(id);
    }

    inline b2BodyType GetType() const
    {
        return b2Body_GetType(id);
    }

    inline void SetType(b2BodyType type)
    {
        b2Body_SetType(id, type);
    }

    inline void SetTransform(b2Vec2 position, b2Rot rotation)
    {
        b2Body_SetTransform(id, position, rotation);
    }

    inline b2Transform GetTransform() const
    {
        return b2Body_GetTransform(id);
    }

    inline void SetLinearVelocity(b2Vec2 velocity)
    {
        b2Body_SetLinearVelocity(id, velocity);
    }

    inline b2Vec2 GetLinearVelocity() const
    {
        return b2Body_GetLinearVelocity(id);
    }

    inline float GetLinearVelocityMagnitude() const
    {
        return b2Length(b2Body_GetLinearVelocity(id));
    }

    inline void SetAngularVelocity(float velocity)
    {
        b2Body_SetAngularVelocity(id, velocity);
    }

    inline float GetAngularVelocity() const
    {
        return b2Body_GetAngularVelocity(id);
    }

    inline void ApplyForce(b2Vec2 force, b2Vec2 point, bool wake = true)
    {
        b2Body_ApplyForce(id, force, point, wake);
    }

    inline void ApplyForceToCenter(b2Vec2 force, bool wake = true)
    {
        b2Body_ApplyForceToCenter(id, force, wake);
    }

    inline void ApplyTorque(float torque, bool wake = true)
    {
        b2Body_ApplyTorque(id, torque, wake);
    }

    inline void ApplyLinearImpulseToCenter(b2Vec2 impulse, bool wake = true)
    {
        b2Body_ApplyLinearImpulseToCenter(id, impulse, wake);
    }

    inline void ApplyLinearImpulse(b2Vec2 impulse, b2Vec2 point, bool wake = true)
    {
        b2Body_ApplyLinearImpulse(id, impulse, point, wake);
    }

    inline void ApplyAngularImpulse(float impulse, bool wake = true)
    {
        b2Body_ApplyAngularImpulse(id, impulse, wake);
    }

    inline void SetAwake(bool flag)
    {
        b2Body_SetAwake(id, flag);
    }

    inline bool IsAwake() const
    {
        return b2Body_IsAwake(id);
    }

    inline void SetGravityScale(float scale)
    {
        b2Body_SetGravityScale(id, scale);
    }

    inline float GetGravityScale() const
    {
        return b2Body_GetGravityScale(id);
    }

    inline void SetFixedRotation(bool flag)
    {
        b2Body_SetFixedRotation(id, flag);
    }

    inline bool IsFixedRotation() const
    {
        return b2Body_IsFixedRotation(id);
    }

    inline void SetBullet(bool flag)
    {
        b2Body_SetBullet(id, flag);
    }

    inline bool IsBullet() const
    {
        return b2Body_IsBullet(id);
    }

    inline void SetName(const char* name)
    {
        b2Body_SetName(id, name);
    }

    inline const char* GetName() const
    {
        return b2Body_GetName(id);
    }

    inline void SetUserData(void* userData)
    {
        b2Body_SetUserData(id, userData);
    }

    inline void* GetUserData() const
    {
        return b2Body_GetUserData(id);
    }

    inline b2WorldId GetWorld() const
    {
        return b2Body_GetWorld(id);
    }

    inline int GetShapeCount() const
    {
        return b2Body_GetShapeCount(id);
    }

    inline int GetShapes(b2ShapeId* shapeArray, int capacity) const
    {
        return b2Body_GetShapes(id, shapeArray, capacity);
    }

    inline int GetJointCount() const
    {
        return b2Body_GetJointCount(id);
    }

    inline int GetJoints(b2JointId* jointArray, int capacity) const
    {
        return b2Body_GetJoints(id, jointArray, capacity);
    }

    inline int GetContactCapacity() const
    {
        return b2Body_GetContactCapacity(id);
    }

    inline int GetContactData(b2ContactData* contactData, int capacity) const
    {
        return b2Body_GetContactData(id, contactData, capacity);
    }

    inline b2AABB ComputeAABB() const
    {
        return b2Body_ComputeAABB(id);
    }

    inline b2Vec2 GetPosition() const
    {
        return b2Body_GetPosition(id);
    }

    inline float GetDistanceTo(b2Vec2 point) const
    {
        return b2Length(b2Sub(b2Body_GetPosition(id), point));
    }

    inline b2Rot GetRotation() const
    {
        return b2Body_GetRotation(id);
    }

    inline float GetAngle() const
    {
        return b2Rot_GetAngle(b2Body_GetRotation(id));
    }

    inline b2Transform GetWorldTransform() const
    {
        return b2Body_GetTransform(id);
    }

    inline b2Vec2 GetLocalPoint(b2Vec2 worldPoint) const
    {
        return b2Body_GetLocalPoint(id, worldPoint);
    }

    inline b2Vec2 GetWorldPoint(b2Vec2 localPoint) const
    {
        return b2Body_GetWorldPoint(id, localPoint);
    }

    inline b2Vec2 GetLocalVector(b2Vec2 worldVector) const
    {
        return b2Body_GetLocalVector(id, worldVector);
    }

    inline b2Vec2 GetWorldVector(b2Vec2 localVector) const
    {
        return b2Body_GetWorldVector(id, localVector);
    }

    inline b2Vec2 GetLocalPointVelocity(b2Vec2 localPoint) const
    {
        return b2Body_GetLocalPointVelocity(id, localPoint);
    }

    inline b2Vec2 GetWorldPointVelocity(b2Vec2 worldPoint) const
    {
        return b2Body_GetWorldPointVelocity(id, worldPoint);
    }

    inline float GetMass() const
    {
        return b2Body_GetMass(id);
    }

    inline float GetRotationalInertia() const
    {
        return b2Body_GetRotationalInertia(id);
    }

    inline b2Vec2 GetLocalCenterOfMass() const
    {
        return b2Body_GetLocalCenterOfMass(id);
    }

    inline b2Vec2 GetWorldCenterOfMass() const
    {
        return b2Body_GetWorldCenterOfMass(id);
    }

    inline void SetMassData(b2MassData massData)
    {
        b2Body_SetMassData(id, massData);
    }

    inline b2MassData GetMassData() const
    {
        return b2Body_GetMassData(id);
    }

    inline void ApplyMassFromShapes()
    {
        b2Body_ApplyMassFromShapes(id);
    }

    inline void SetLinearDamping(float linearDamping)
    {
        b2Body_SetLinearDamping(id, linearDamping);
    }

    inline float GetLinearDamping() const
    {
        return b2Body_GetLinearDamping(id);
    }

    inline void SetAngularDamping(float angularDamping)
    {
        b2Body_SetAngularDamping(id, angularDamping);
    }

    inline float GetAngularDamping() const
    {
        return b2Body_GetAngularDamping(id);
    }

    inline void SetSleepThreshold(float sleepThreshold)
    {
        b2Body_SetSleepThreshold(id, sleepThreshold);
    }

    inline float GetSleepThreshold() const
    {
        return b2Body_GetSleepThreshold(id);
    }

    inline void SetEnabled(bool enabled)
    {
        enabled ? b2Body_Enable(id) : b2Body_Disable(id);
    }

    inline bool IsEnabled() const
    {
        return b2Body_IsEnabled(id);
    }

    inline void EnableSleep(bool enableSleep)
    {
        b2Body_EnableSleep(id, enableSleep);
    }

    inline bool IsSleepEnabled() const
    {
        return b2Body_IsSleepEnabled(id);
    }

    inline void SetContactEventsEnabled(bool flag)
    {
        b2Body_EnableContactEvents(id, flag);
    }

    inline void SetHitEventsEnabled(bool flag)
    {
        b2Body_EnableHitEvents(id, flag);
    }

    Shape CreateCircleShape(const b2ShapeDef* def, const b2Circle* circle)
    {
        return Shape(b2CreateCircleShape(id, def, circle));
    }

    Shape CreateSegmentShape(const b2ShapeDef* def, const b2Segment* segment)
    {
        return Shape(b2CreateSegmentShape(id, def, segment));
    }

    Shape CreateCapsuleShape(const b2ShapeDef* def, const b2Capsule* capsule)
    {
        return Shape(b2CreateCapsuleShape(id, def, capsule));
    }

    Shape CreatePolygonShape(const b2ShapeDef* def, const b2Polygon* polygon)
    {
        return Shape(b2CreatePolygonShape(id, def, polygon));
    }

    Chain CreateChain(PyChainDef& def)
    {
        return Chain(b2CreateChain(id, &def.chain_def));
    }
};

// all inline !
struct WorldView
{
    b2WorldId id;

    using id_type = b2WorldId;

    static auto int_to_id(uint64_t id) -> id_type
    {
        return b2LoadWorldId(id);
    }

    static auto id_to_int(id_type id) -> uint64_t
    {
        return b2StoreWorldId(id);
    }

    // inline WorldView() { id = b2CreateWorld(nullptr); }
    WorldView(b2WorldId worldId)
        : id(worldId)
    {
    }

    inline WorldView(uint64_t worldId)
        : id(b2LoadWorldId(worldId))
    {
    }

    inline WorldView(const b2WorldDef* def)
    {
        id = b2CreateWorld(def);
    }

    inline void Destroy()
    {
        if (b2World_IsValid(id))
        {
            b2DestroyWorld(id);
            id = b2_nullWorldId;  // Invalidate the ID after destruction
        }
    }

    inline bool IsValid() const
    {
        return b2World_IsValid(id);
    }

    inline void Step(float timeStep, int subStepCount)
    {
        b2World_Step(id, timeStep, subStepCount);
    }

    inline void Draw(b2DebugDraw* draw)
    {
        b2World_Draw(id, draw);
    }

    inline b2BodyEvents GetBodyEvents()
    {
        return b2World_GetBodyEvents(id);
    }

    inline b2SensorEvents GetSensorEvents()
    {
        return b2World_GetSensorEvents(id);
    }

    inline b2ContactEvents GetContactEvents()
    {
        return b2World_GetContactEvents(id);
    }

    inline b2TreeStats OverlapAABB(b2AABB aabb, b2QueryFilter filter, b2OverlapResultFcn* fcn, void* context)
    {
        return b2World_OverlapAABB(id, aabb, filter, fcn, context);
    }

    inline std::optional<b2ShapeId> ShapeAtPoint(b2Vec2 point, b2QueryFilter filter)
    {
        // create a tiny aabb around the point
        b2AABB aabb;
        aabb.lowerBound = b2Sub(point, b2Vec2{0.001f, 0.001f});
        aabb.upperBound = b2Add(point, b2Vec2{0.001f, 0.001f});

        // make the point itself and the result the context
        using ctx_type = std::tuple<b2Vec2, b2ShapeId, bool>;
        ctx_type context = {point, b2ShapeId{}, false};

        auto fcn_lambda = [](b2ShapeId shape_id, void* void_context) -> bool
        {
            auto ctx = static_cast<ctx_type*>(void_context);
            const auto& p = std::get<0>(*ctx);  // get the point from the context
            if (b2Shape_TestPoint(shape_id, p))
            {
                std::get<1>(*ctx) = shape_id;  // store the shape id in the context
                std::get<2>(*ctx) = true;      // mark that we found a shape
                return false;                  // stop searching after the first hit
            }
            return true;  // continue searching
        };

        void* void_context = &context;
        b2World_OverlapAABB(this->id, aabb, filter, fcn_lambda, static_cast<void*>(&context));
        if (std::get<2>(context))  // if we found a shape
        {
            return std::make_optional(std::get<1>(context));  // return the shape id
        }
        else
        {
            return std::nullopt;  // no shape found at the point
        }
    }

    inline std::optional<b2ShapeId> DynamicBodyShapeAtPoint(b2Vec2 point, b2QueryFilter filter)
    {
        // create a tiny aabb around the point
        b2AABB aabb;
        aabb.lowerBound = b2Sub(point, b2Vec2{0.001f, 0.001f});
        aabb.upperBound = b2Add(point, b2Vec2{0.001f, 0.001f});

        // make the point itself and the result the context
        using ctx_type = std::tuple<b2Vec2, b2ShapeId, bool>;
        ctx_type context = {point, b2ShapeId{}, false};

        auto fcn_lambda = [](b2ShapeId shape_id, void* void_context) -> bool
        {
            auto ctx = static_cast<ctx_type*>(void_context);
            const auto& p = std::get<0>(*ctx);  // get the point from the context

            // get the body of the shape
            b2BodyId body_id = b2Shape_GetBody(shape_id);
            // check if the body is dynamic
            if (b2Body_GetType(body_id) != b2_dynamicBody)
            {
                return true;  // continue searching if the body is not dynamic
            }


            if (b2Shape_TestPoint(shape_id, p))
            {
                std::get<1>(*ctx) = shape_id;  // store the shape id in the context
                std::get<2>(*ctx) = true;      // mark that we found a shape
                return false;                  // stop searching after the first hit
            }
            return true;  // continue searching
        };

        void* void_context = &context;
        b2World_OverlapAABB(this->id, aabb, filter, fcn_lambda, static_cast<void*>(&context));
        if (std::get<2>(context))  // if we found a shape
        {
            return std::make_optional(std::get<1>(context));  // return the shape id
        }
        else
        {
            return std::nullopt;  // no shape found at the point
        }
    }

    inline std::optional<b2BodyId> BodyAtPoint(b2Vec2 point, b2QueryFilter filter)
    {
        auto res = ShapeAtPoint(point, filter);
        if (res.has_value())
        {
            b2ShapeId shapeId = res.value();
            b2BodyId bodyId = b2Shape_GetBody(shapeId);
            return std::make_optional(bodyId);
        }
        return std::nullopt;
    }

    inline std::optional<b2BodyId> DynamicBodyAtPoint(b2Vec2 point, b2QueryFilter filter)
    {
        auto res = DynamicBodyShapeAtPoint(point, filter);
        if (res.has_value())
        {
            b2ShapeId shapeId = res.value();
            b2BodyId bodyId = b2Shape_GetBody(shapeId);
            return std::make_optional(bodyId);
        }
        return std::nullopt;
    }

    inline b2TreeStats
    OverlapShape(const b2ShapeProxy* proxy, b2QueryFilter filter, b2OverlapResultFcn* fcn, void* context)
    {
        return b2World_OverlapShape(id, proxy, filter, fcn, context);
    }

    inline b2TreeStats
    CastRay(b2Vec2 origin, b2Vec2 translation, b2QueryFilter filter, b2CastResultFcn* fcn, void* context)
    {
        return b2World_CastRay(id, origin, translation, filter, fcn, context);
    }

    inline b2RayResult CastRayClosest(b2Vec2 origin, b2Vec2 translation, b2QueryFilter filter)
    {
        return b2World_CastRayClosest(id, origin, translation, filter);
    }

    inline b2TreeStats
    CastShape(const b2ShapeProxy* proxy, b2Vec2 translation, b2QueryFilter filter, b2CastResultFcn* fcn, void* context)
    {
        return b2World_CastShape(id, proxy, translation, filter, fcn, context);
    }

    inline float CastMover(const b2Capsule* mover, b2Vec2 translation, b2QueryFilter filter)
    {
        return b2World_CastMover(id, mover, translation, filter);
    }

    inline void CollideMover(const b2Capsule* mover, b2QueryFilter filter, b2PlaneResultFcn* fcn, void* context)
    {
        b2World_CollideMover(id, mover, filter, fcn, context);
    }

    inline void EnableSleeping(bool flag)
    {
        b2World_EnableSleeping(id, flag);
    }

    inline bool IsSleepingEnabled() const
    {
        return b2World_IsSleepingEnabled(id);
    }

    inline void EnableContinuous(bool flag)
    {
        b2World_EnableContinuous(id, flag);
    }

    inline bool IsContinuousEnabled() const
    {
        return b2World_IsContinuousEnabled(id);
    }

    inline void SetRestitutionThreshold(float value)
    {
        b2World_SetRestitutionThreshold(id, value);
    }

    inline float GetRestitutionThreshold() const
    {
        return b2World_GetRestitutionThreshold(id);
    }

    inline void SetHitEventThreshold(float value)
    {
        b2World_SetHitEventThreshold(id, value);
    }

    inline float GetHitEventThreshold() const
    {
        return b2World_GetHitEventThreshold(id);
    }

    inline void SetCustomFilterCallback(b2CustomFilterFcn* fcn, void* context)
    {
        b2World_SetCustomFilterCallback(id, fcn, context);
    }

    inline void SetPreSolveCallback(b2PreSolveFcn* fcn, void* context)
    {
        b2World_SetPreSolveCallback(id, fcn, context);
    }

    inline void SetGravity(b2Vec2 gravity)
    {
        b2World_SetGravity(id, gravity);
    }

    inline b2Vec2 GetGravity() const
    {
        return b2World_GetGravity(id);
    }

    inline void Explode(const b2ExplosionDef* explosionDef)
    {
        b2World_Explode(id, explosionDef);
    }

    inline void SetContactTuning(float hertz, float dampingRatio, float pushSpeed)
    {
        b2World_SetContactTuning(id, hertz, dampingRatio, pushSpeed);
    }

    inline void SetMaximumLinearSpeed(float maximumLinearSpeed)
    {
        b2World_SetMaximumLinearSpeed(id, maximumLinearSpeed);
    }

    inline float GetMaximumLinearSpeed() const
    {
        return b2World_GetMaximumLinearSpeed(id);
    }

    inline void EnableWarmStarting(bool flag)
    {
        b2World_EnableWarmStarting(id, flag);
    }

    inline bool IsWarmStartingEnabled() const
    {
        return b2World_IsWarmStartingEnabled(id);
    }

    inline int GetAwakeBodyCount() const
    {
        return b2World_GetAwakeBodyCount(id);
    }

    inline b2Profile GetProfile() const
    {
        return b2World_GetProfile(id);
    }

    inline b2Counters GetCounters() const
    {
        return b2World_GetCounters(id);
    }

    inline void SetUserData(void* userData)
    {
        b2World_SetUserData(id, userData);
    }

    inline void* GetUserData() const
    {
        return b2World_GetUserData(id);
    }

    inline void SetFrictionCallback(b2FrictionCallback* callback)
    {
        b2World_SetFrictionCallback(id, callback);
    }

    inline void SetRestitutionCallback(b2RestitutionCallback* callback)
    {
        b2World_SetRestitutionCallback(id, callback);
    }

    inline void DumpMemoryStats()
    {
        b2World_DumpMemoryStats(id);
    }

    inline void RebuildStaticTree()
    {
        b2World_RebuildStaticTree(id);
    }

    inline void EnableSpeculative(bool flag)
    {
        b2World_EnableSpeculative(id, flag);
    }

    // extra functions to create bodies
    inline b2BodyId CreateBodyId(const b2BodyDef* def)
    {
        return b2CreateBody(id, def);
    }

    inline Body CreateBody(const b2BodyDef* def)
    {
        return Body(b2CreateBody(id, def));
    }

    // extra functions to create joints
    inline DistanceJoint CreateDistanceJoint(const b2DistanceJointDef* def)
    {
        return DistanceJoint(b2CreateDistanceJoint(id, def));
    }

    inline FilterJoint CreateFilterJoint(const b2FilterJointDef* def)
    {
        return FilterJoint(b2CreateFilterJoint(id, def));
    }

    inline MotorJoint CreateMotorJoint(const b2MotorJointDef* def)
    {
        return MotorJoint(b2CreateMotorJoint(id, def));
    }

    inline MouseJoint CreateMouseJoint(const b2MouseJointDef* def)
    {
        return MouseJoint(b2CreateMouseJoint(id, def));
    }

    inline PrismaticJoint CreatePrismaticJoint(const b2PrismaticJointDef* def)
    {
        return PrismaticJoint(b2CreatePrismaticJoint(id, def));
    }

    inline RevoluteJoint CreateRevoluteJoint(const b2RevoluteJointDef* def)
    {
        return RevoluteJoint(b2CreateRevoluteJoint(id, def));
    }

    inline WeldJoint CreateWeldJoint(const b2WeldJointDef* def)
    {
        return WeldJoint(b2CreateWeldJoint(id, def));
    }

    inline WheelJoint CreateWheelJoint(const b2WheelJointDef* def)
    {
        return WheelJoint(b2CreateWheelJoint(id, def));
    }
};
