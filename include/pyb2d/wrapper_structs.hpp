#pragma once
#include <box2d/box2d.h>
#include <box2d/math_functions.h>


namespace nb = nanobind;

struct WorldView;
struct Body;
struct Shape;
struct Chain;
struct Joint;

struct Chain
{
    b2ChainId id;

    inline Chain(b2ChainId chainId)
        : id(chainId)
    {
    }
};

struct Joint
{
    b2JointId id;

    inline Joint(b2JointId jointId)
        : id(jointId)
    {
    }
};

// for consitency with the other IDs
inline uint64_t b2StoreWorldId(b2WorldId id)
{
    return ((uint64_t) id.index1 << 16) | ((uint64_t) id.generation);
}

inline b2WorldId b2LoadWorldId(uint64_t x)
{
    b2WorldId id = {(uint16_t) (x >> 16), (uint16_t) (x)};
    return id;
}

struct Shape
{
    b2ShapeId id;

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

    inline void SetSurfaceMaterial(b2SurfaceMaterial surfaceMaterial)
    {
        b2Shape_SetSurfaceMaterial(id, surfaceMaterial);
    }

    inline b2SurfaceMaterial GetSurfaceMaterial() const
    {
        return b2Shape_GetSurfaceMaterial(id);
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
    inline CircleShape(b2ShapeId shapeId)
        : Shape(shapeId)
    {
    }

    inline CircleShape(uint64_t shapeId)
        : Shape(shapeId)
    {
    }

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
    inline CapsuleShape(b2ShapeId shapeId)
        : Shape(shapeId)
    {
    }

    inline CapsuleShape(uint64_t shapeId)
        : Shape(shapeId)
    {
    }

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
    inline SegmentShape(b2ShapeId shapeId)
        : Shape(shapeId)
    {
    }

    inline SegmentShape(uint64_t shapeId)
        : Shape(shapeId)
    {
    }

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
    inline PolygonShape(b2ShapeId shapeId)
        : Shape(shapeId)
    {
    }

    inline PolygonShape(uint64_t shapeId)
        : Shape(shapeId)
    {
    }

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

struct Body
{
    b2BodyId id;

    // inline Body() { id = b2InvalidBodyId; }
    inline Body(b2BodyId bodyId)
        : id(bodyId)
    {
    }

    inline Body(uint64_t bodyId)
        : id(b2LoadBodyId(bodyId))
    {
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

    inline b2Rot GetRotation() const
    {
        return b2Body_GetRotation(id);
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
};

// all inline !
struct WorldView
{
    b2WorldId id;

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
        }
    }

    // inline ~WorldView() {
    //     if(b2World_IsValid(id))
    //     {
    //         b2DestroyWorld(id);
    //     }
    // }
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

    inline void SetJointTuning(float hertz, float dampingRatio)
    {
        b2World_SetJointTuning(id, hertz, dampingRatio);
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
};
