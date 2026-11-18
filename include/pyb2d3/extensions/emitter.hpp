#pragma once

// Particle emitters: a pyb2d3 extension, not part of Box2D.
//
// An emitter creates small dynamic bodies (particles) at a rate, ages them and destroys them
// when their lifetime is over: per-particle work every step that would be too slow in python.
// `step` returns the reaction impulse of the particles emitted in that step (for rockets,
// sprinklers, recoil: the caller applies it to the body carrying the emitter).

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <deque>
#include <limits>
#include <random>
#include <utility>
#include <variant>
#include <vector>

#include <box2d/box2d.h>
#include <box2d/math_functions.h>

namespace pyb2d3::extensions
{
    // a random value: constant (a), uniform in [a, b], normal (mean a, standard deviation b)
    struct Distribution
    {
        enum class Kind
        {
            Constant,
            Uniform,
            Normal
        };

        Kind kind = Kind::Constant;
        float a = 0.0f;
        float b = 0.0f;

        Distribution() = default;

        Distribution(float value)
            : kind(Kind::Constant)
            , a(value)
        {
        }

        Distribution(Kind kind_, float a_, float b_)
            : kind(kind_)
            , a(a_)
            , b(b_)
        {
        }

        float sample(std::mt19937& rng) const
        {
            switch (kind)
            {
                case Kind::Uniform:
                    return std::uniform_real_distribution<float>(std::min(a, b), std::max(a, b))(rng);
                case Kind::Normal:
                    return b > 0.0f ? std::normal_distribution<float>(a, b)(rng) : a;
                default:
                    return a;
            }
        }
    };

    // what happens when a particle should be emitted while `capacity` particles are alive
    enum class OnCapacityReached
    {
        DestroyOldest,
        DestroyRandom,
        Stop
    };

    using Geometry = std::variant<b2Circle, b2Capsule, b2Polygon>;

    // the reaction of emitted particles on the emitter: linear and angular impulse
    struct Reaction
    {
        b2Vec2 impulse = {0.0f, 0.0f};
        float angular_impulse = 0.0f;
    };

    class Emitter
    {
    public:

        // settings (python: read / write)
        float rate = 10.0f;  // particles per second
        int capacity = 100;  // particles alive at most
        Distribution speed = 1.0f;
        Distribution lifetime = 1.0f;
        float max_lifetime = std::numeric_limits<float>::infinity();
        OnCapacityReached on_capacity_reached = OnCapacityReached::DestroyOldest;
        std::vector<std::pair<float, uint32_t>> colors;  // (life fraction, 0xRRGGBB) stops
        b2Transform transform = b2Transform_identity;    // the pose without an owner body
        b2Transform local_frame = b2Transform_identity;  // the pose on the owner body
        bool collide_with_owner = true;                  // false: a filter joint per particle
        bool enabled = true;                             // false: step emits nothing (pause)

        Emitter(
            b2WorldId world,
            const b2ShapeDef& shape_def,
            Geometry geometry,
            b2BodyDef body_def,
            b2BodyId owner,
            uint32_t seed
        )
            : m_world(world)
            , m_shape_def(shape_def)
            , m_geometry(std::move(geometry))
            , m_body_def(body_def)
            , m_owner(owner)
            , m_rng(seed)
        {
            m_body_def.type = b2_dynamicBody;
            m_body_def.name = nullptr;  // not kept alive by us
        }

        virtual ~Emitter()
        {
            clear();
        }

        Emitter(const Emitter&) = delete;
        Emitter& operator=(const Emitter&) = delete;

        // age the particles, destroy expired ones, emit rate * dt (with a fractional carry);
        // returns the reaction of this step's particles
        Reaction step(float dt)
        {
            expire(dt);
            m_carry = enabled ? m_carry + std::max(rate, 0.0f) * dt : 0.0f;
            const int n = static_cast<int>(m_carry);
            m_carry -= static_cast<float>(n);
            Reaction reaction = emit(n);
            update_colors();
            return reaction;
        }

        // emit `n` particles now (independent of the rate)
        Reaction burst(int n)
        {
            Reaction reaction = emit(n);
            update_colors();
            return reaction;
        }

        // destroy all particles
        void clear()
        {
            if (b2World_IsValid(m_world))
            {
                for (const Particle& p : m_particles)
                {
                    destroy(p);
                }
            }
            m_particles.clear();
        }

        std::size_t size() const
        {
            return m_particles.size();
        }

        bool has_owner() const
        {
            return B2_IS_NON_NULL(m_owner) && b2Body_IsValid(m_owner);
        }

        // the emitter's pose in the world: on the owner body, else `transform`
        b2Transform pose() const
        {
            if (has_owner())
            {
                return b2MulWorldTransforms(b2Body_GetTransform(m_owner), local_frame);
            }
            return transform;
        }

        // the live particles, oldest first
        std::vector<b2BodyId> bodies() const
        {
            std::vector<b2BodyId> ids;
            ids.reserve(m_particles.size());
            for (const Particle& p : m_particles)
            {
                ids.push_back(p.body);
            }
            return ids;
        }

        std::vector<b2ShapeId> shapes() const
        {
            std::vector<b2ShapeId> ids;
            ids.reserve(m_particles.size());
            for (const Particle& p : m_particles)
            {
                ids.push_back(p.shape);
            }
            return ids;
        }

        std::vector<float> ages() const
        {
            std::vector<float> values;
            values.reserve(m_particles.size());
            for (const Particle& p : m_particles)
            {
                values.push_back(p.age);
            }
            return values;
        }

        std::vector<float> lifetimes() const
        {
            std::vector<float> values;
            values.reserve(m_particles.size());
            for (const Particle& p : m_particles)
            {
                values.push_back(p.lifetime);
            }
            return values;
        }

    protected:

        // where (point) and in which direction (unit vector) a particle starts, both in the
        // emitter's frame
        virtual void spawn(std::mt19937& rng, b2Vec2& point, b2Vec2& direction) = 0;

    private:

        struct Particle
        {
            b2BodyId body;
            b2ShapeId shape;
            float age;
            float lifetime;
        };

        void destroy(const Particle& p)
        {
            // (its filter joint goes with it; the body may be gone already, e.g. a snapshot
            // restore or the world destroyed)
            if (b2Body_IsValid(p.body))
            {
                b2DestroyBody(p.body);
            }
        }

        void expire(float dt)
        {
            if (!b2World_IsValid(m_world))
            {
                // (the world is gone: its slot may hold a new world, with bodies whose ids
                // look like ours)
                m_particles.clear();
                return;
            }
            auto gone = [&](Particle& p)
            {
                p.age += dt;
                if (p.age >= p.lifetime || !b2Body_IsValid(p.body))
                {
                    destroy(p);
                    return true;
                }
                return false;
            };
            m_particles.erase(std::remove_if(m_particles.begin(), m_particles.end(), gone), m_particles.end());
        }

        Reaction emit(int n)
        {
            Reaction reaction;
            if (n <= 0 || !b2World_IsValid(m_world))
            {
                return reaction;
            }
            const b2Transform frame = pose();
            const bool owned = has_owner();
            const b2Vec2 center = owned ? b2Body_GetWorldCenter(m_owner) : frame.p;
            for (int i = 0; i < n; ++i)
            {
                if (capacity <= 0)
                {
                    break;
                }
                if (static_cast<int>(m_particles.size()) >= capacity)
                {
                    if (on_capacity_reached == OnCapacityReached::Stop)
                    {
                        break;
                    }
                    std::size_t index = 0;  // the oldest
                    if (on_capacity_reached == OnCapacityReached::DestroyRandom)
                    {
                        index = std::uniform_int_distribution<std::size_t>(0, m_particles.size() - 1)(m_rng);
                    }
                    destroy(m_particles[index]);
                    m_particles.erase(m_particles.begin() + static_cast<std::ptrdiff_t>(index));
                }

                b2Vec2 local_point = {0.0f, 0.0f};
                b2Vec2 local_direction = {1.0f, 0.0f};
                spawn(m_rng, local_point, local_direction);
                const b2Vec2 point = b2TransformPoint(frame, local_point);
                const b2Vec2 direction = b2RotateVector(frame.q, local_direction);
                const float s = std::max(speed.sample(m_rng), 0.0f);
                const b2Vec2 base_velocity = owned ? b2Body_GetWorldPointVelocity(m_owner, point) : b2Vec2_zero;
                const b2Vec2 relative_velocity = b2MulSV(s, direction);

                b2BodyDef def = m_body_def;
                def.position = point;
                def.rotation = b2MakeRot(std::atan2(direction.y, direction.x));
                def.linearVelocity = b2Add(base_velocity, relative_velocity);
                const b2BodyId body = b2CreateBody(m_world, &def);
                b2ShapeDef shape_def = m_shape_def;
                if (!colors.empty())
                {
                    shape_def.material.customColor = color_at(0.0f);
                }
                const b2ShapeId shape = std::visit(
                    [&](const auto& geometry)
                    {
                        return create_shape(body, shape_def, geometry);
                    },
                    m_geometry
                );
                if (owned && !collide_with_owner)
                {
                    b2FilterJointDef joint_def = b2DefaultFilterJointDef();
                    joint_def.base.bodyIdA = m_owner;
                    joint_def.base.bodyIdB = body;
                    b2CreateFilterJoint(m_world, &joint_def);
                }

                float life = lifetime.sample(m_rng);
                life = std::min(std::max(life, 1e-6f), max_lifetime);
                m_particles.push_back(Particle{body, shape, 0.0f, life});

                // the particle takes momentum m * v_rel away from the emitter
                const b2Vec2 impulse = b2MulSV(-b2Body_GetMass(body), relative_velocity);
                reaction.impulse = b2Add(reaction.impulse, impulse);
                reaction.angular_impulse += b2Cross(b2Sub(point, center), impulse);
            }
            return reaction;
        }

        static b2ShapeId create_shape(b2BodyId body, const b2ShapeDef& def, const b2Circle& circle)
        {
            return b2CreateCircleShape(body, &def, &circle);
        }

        static b2ShapeId create_shape(b2BodyId body, const b2ShapeDef& def, const b2Capsule& capsule)
        {
            return b2CreateCapsuleShape(body, &def, &capsule);
        }

        static b2ShapeId create_shape(b2BodyId body, const b2ShapeDef& def, const b2Polygon& polygon)
        {
            return b2CreatePolygonShape(body, &def, &polygon);
        }

        // the color at life fraction t (linear between the stops, sorted by fraction)
        uint32_t color_at(float t) const
        {
            if (t <= colors.front().first)
            {
                return colors.front().second;
            }
            for (std::size_t i = 1; i < colors.size(); ++i)
            {
                if (t <= colors[i].first)
                {
                    const float t0 = colors[i - 1].first, t1 = colors[i].first;
                    const uint32_t c0 = colors[i - 1].second, c1 = colors[i].second;
                    const float u = t1 > t0 ? (t - t0) / (t1 - t0) : 1.0f;
                    auto channel = [&](int shift)
                    {
                        const float a = static_cast<float>((c0 >> shift) & 0xFF);
                        const float b = static_cast<float>((c1 >> shift) & 0xFF);
                        return static_cast<uint32_t>(std::lround(a + u * (b - a))) << shift;
                    };
                    return channel(16) | channel(8) | channel(0);
                }
            }
            return colors.back().second;
        }

        void update_colors()
        {
            if (colors.empty())
            {
                return;
            }
            for (const Particle& p : m_particles)
            {
                // particles that never expire keep the first color
                const float t = std::isfinite(p.lifetime) ? p.age / p.lifetime : 0.0f;
                b2SurfaceMaterial material = b2Shape_GetSurfaceMaterial(p.shape);
                material.customColor = color_at(t);
                b2Shape_SetSurfaceMaterial(p.shape, &material);
            }
        }

        b2WorldId m_world;
        b2ShapeDef m_shape_def;
        Geometry m_geometry;
        b2BodyDef m_body_def;
        b2BodyId m_owner;
        std::mt19937 m_rng;
        float m_carry = 0.0f;
        std::deque<Particle> m_particles;  // oldest first
    };

    // particles leave a point at `radius` from the emitter's origin, in a direction between
    // `angle_min` and `angle_max` (radians, from the emitter's x axis)
    class RadialEmitter : public Emitter
    {
    public:

        float angle_min = 0.0f;
        float angle_max = 0.0f;
        float radius = 0.0f;

        using Emitter::Emitter;

    protected:

        void spawn(std::mt19937& rng, b2Vec2& point, b2Vec2& direction) override
        {
            const float angle = Distribution(Distribution::Kind::Uniform, angle_min, angle_max).sample(rng);
            direction = {std::cos(angle), std::sin(angle)};
            point = b2MulSV(radius, direction);
        }
    };

    // particles leave the line p1 -> p2 along its left normal, at t = `along` (0: p1, 1: p2)
    class LinearEmitter : public Emitter
    {
    public:

        b2Vec2 p1 = {-1.0f, 0.0f};
        b2Vec2 p2 = {1.0f, 0.0f};
        Distribution along = Distribution(Distribution::Kind::Uniform, 0.0f, 1.0f);

        using Emitter::Emitter;

    protected:

        void spawn(std::mt19937& rng, b2Vec2& point, b2Vec2& direction) override
        {
            const float t = std::clamp(along.sample(rng), 0.0f, 1.0f);
            const b2Vec2 edge = b2Sub(p2, p1);
            point = b2MulAdd(p1, t, edge);
            direction = b2Normalize(b2LeftPerp(edge));
        }
    };
}  // namespace pyb2d3::extensions
