// pyb2d3's own extensions on top of box2d (not part of Box2D): the submodule
// `_pyb2d3.extensions`, used as `pyb2d3.extensions` (src/module/pyb2d3/extensions.py adds the
// keyword constructors). So far: particle emitters (include/pyb2d3/extensions/emitter.hpp).

#include <algorithm>
#include <optional>
#include <tuple>

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/variant.h>
#include <nanobind/stl/vector.h>

#include "bind.hpp"
#include "pyb2d3/core/binder.hpp"
#include "pyb2d3/extensions/emitter.hpp"
#include "pyb2d3/extensions/neighbors.hpp"
#include "pyb2d3/wrapper_structs.hpp"

namespace pyb2d3::bind
{
    namespace
    {
        using namespace pyb2d3::extensions;

        template <class T, class IdT>
        Batch<T> batch_of(const std::vector<IdT>& ids)
        {
            Batch<T> batch;
            batch.ids.reserve(ids.size());
            for (IdT id : ids)
            {
                batch.ids.push_back(T::id_to_int(id));
            }
            return batch;
        }

        nb::object float_array(const std::vector<float>& values)
        {
            float* data = nullptr;
            nb::object array = pyb2d3::detail::make_array<float>(values.size(), 1, data);
            std::copy(values.begin(), values.end(), data);
            return array;
        }

        template <class S>
        nb::object to_array(const std::vector<S>& values, std::size_t width)
        {
            S* data = nullptr;
            nb::object array = pyb2d3::detail::make_array<S>(values.size() / width, width, data);
            std::copy(values.begin(), values.end(), data);
            return array;
        }

        std::tuple<b2Vec2, float> as_tuple(const Reaction& reaction)
        {
            return {reaction.impulse, reaction.angular_impulse};
        }

        // the constructor of both emitter types: (world, shape_def, geometry, body, body_def,
        // seed); the other settings are properties (set by the python keyword constructor)
        template <class E>
        void bind_init(nb::class_<E, Emitter>& cls)
        {
            cls.def(
                "__init__",
                [](E* self,
                   const WorldView& world,
                   const b2ShapeDef& shape_def,
                   Geometry geometry,
                   std::optional<Body> body,
                   std::optional<b2BodyDef> body_def,
                   uint32_t seed)
                {
                    new (self)
                        E(world.id,
                          shape_def,
                          std::move(geometry),
                          body_def.value_or(b2DefaultBodyDef()),
                          body ? body->id : b2_nullBodyId,
                          seed);
                },
                nb::arg("world"),
                nb::arg("shape_def"),
                nb::arg("geometry"),
                nb::arg("body") = nb::none(),
                nb::arg("body_def") = nb::none(),
                nb::arg("seed") = 0
            );
        }
    }  // namespace

    void export_extensions(nb::module_& m)
    {
        nb::module_ ext = m.def_submodule(
            "extensions",
            "pyb2d3's own extensions on top of Box2D (not part of Box2D): C++ helpers for work "
            "that would be too slow in python, e.g. particle emitters."
        );

        nb::class_<Distribution>(
            ext,
            "Distribution",
            "A random value of an emitter (speed, lifetime, position along a line): see "
            "constant(), uniform(), normal(); a plain number is a constant."
        )
            .def(nb::init<float>(), nb::arg("value"))
            .def_rw("a", &Distribution::a)
            .def_rw("b", &Distribution::b)
            .def(
                "__repr__",
                [](const Distribution& d)
                {
                    const char* kind = d.kind == Distribution::Kind::Uniform  ? "uniform"
                                       : d.kind == Distribution::Kind::Normal ? "normal"
                                                                              : "constant";
                    return nb::str("{}({}, {})").format(kind, d.a, d.b);
                }
            );
        nb::implicitly_convertible<float, Distribution>();
        ext.def(
            "constant",
            [](float value)
            {
                return Distribution(value);
            },
            nb::arg("value"),
            "Always `value`."
        );
        ext.def(
            "uniform",
            [](float low, float high)
            {
                return Distribution(Distribution::Kind::Uniform, low, high);
            },
            nb::arg("low"),
            nb::arg("high"),
            "Uniform in [low, high]."
        );
        ext.def(
            "normal",
            [](float mean, float std)
            {
                return Distribution(Distribution::Kind::Normal, mean, std);
            },
            nb::arg("mean"),
            nb::arg("std"),
            "Normal (Gaussian) with mean `mean` and standard deviation `std`."
        );

        nb::enum_<OnCapacityReached>(
            ext,
            "OnCapacityReached",
            "What an emitter does when `capacity` particles are alive."
        )
            .value("DESTROY_OLDEST", OnCapacityReached::DestroyOldest, "destroy the oldest particle, emit the new one")
            .value("DESTROY_RANDOM", OnCapacityReached::DestroyRandom, "destroy a random particle, emit the new one")
            .value("STOP", OnCapacityReached::Stop, "emit nothing until particles expire");

        nb::class_<Emitter>(
            ext,
            "Emitter",
            "Base class of the particle emitters (a pyb2d3 extension, not part of Box2D): "
            "creates small dynamic bodies at `rate`, ages them, destroys them after their "
            "lifetime. `step(dt)` returns the reaction (impulse, angular impulse) of the "
            "particles emitted in that step: apply it to the body carrying the emitter for "
            "thrust / recoil."
        )
            .def_rw("rate", &Emitter::rate, "Particles emitted per second.")
            .def_rw("capacity", &Emitter::capacity, "Particles alive at most (see on_capacity_reached).")
            .def_rw("speed", &Emitter::speed, "Speed of new particles (m/s, a Distribution).")
            .def_rw("lifetime", &Emitter::lifetime, "Lifetime of new particles (s, a Distribution).")
            .def_rw("max_lifetime", &Emitter::max_lifetime, "Upper bound of the lifetime (s, math.inf: none).")
            .def_rw(
                "on_capacity_reached",
                &Emitter::on_capacity_reached,
                "What happens when capacity particles are alive."
            )
            .def_prop_rw(
                "colors",
                [](const Emitter& e)
                {
                    return e.colors;
                },
                [](Emitter& e, std::vector<std::pair<float, uint32_t>> stops)
                {
                    std::sort(stops.begin(), stops.end());
                    e.colors = std::move(stops);
                },
                "Color over the life: [(life fraction 0..1, 0xRRGGBB), ...], interpolated and set "
                "on the particles by step (empty: the shape def's color)."
            )
            .def_rw("transform", &Emitter::transform, "The emitter's pose in the world (without an owner body).")
            .def_rw("local_frame", &Emitter::local_frame, "The emitter's pose on the owner body.")
            .def_rw(
                "collide_with_owner",
                &Emitter::collide_with_owner,
                "Whether particles collide with the owner body (default True; False costs a filter "
                "joint per particle, drawn by box2d's debug draw as two dots)."
            )
            .def_rw(
                "enabled",
                &Emitter::enabled,
                "False pauses the emission: step still ages and expires the particles but emits "
                "none (burst still works)."
            )
            .def_prop_ro("pose", &Emitter::pose, "The emitter's current pose in the world.")
            .def(
                "step",
                [](Emitter& e, float dt)
                {
                    return as_tuple(e.step(dt));
                },
                nb::arg("dt"),
                "Age the particles, destroy expired ones, emit rate * dt new ones. Returns the "
                "reaction (impulse, angular_impulse) of the new particles: -sum m * v (relative to "
                "the owner), the angular impulse about the owner's center of mass (else the "
                "emitter's origin). Call it before world.step."
            )
            .def(
                "burst",
                [](Emitter& e, int n)
                {
                    return as_tuple(e.burst(n));
                },
                nb::arg("n"),
                "Emit `n` particles now (whatever the rate). Returns the reaction like step."
            )
            .def("clear", &Emitter::clear, "Destroy all particles.")
            .def("__len__", &Emitter::size)
            .def_prop_ro(
                "particles",
                [](const Emitter& e)
                {
                    return batch_of<Body>(e.bodies());
                },
                "The live particles (Bodies), oldest first: same order as shapes, ages, lifetimes."
            )
            .def_prop_ro(
                "shapes",
                [](const Emitter& e)
                {
                    return batch_of<Shape>(e.shapes());
                },
                "The particles' shapes (Shapes), one each, same order as particles."
            )
            .def_prop_ro(
                "ages",
                [](const Emitter& e)
                {
                    return float_array(e.ages());
                },
                "Age of each particle (s), same order as particles."
            )
            .def_prop_ro(
                "lifetimes",
                [](const Emitter& e)
                {
                    return float_array(e.lifetimes());
                },
                "Lifetime of each particle (s), same order as particles."
            );

        ext.def(
            "_neighbor_pairs",
            [](nb::ndarray<const double, nb::shape<-1, 2>, nb::c_contig, nb::device::cpu> positions,
               double radius)
            {
                if (!(radius > 0.0))
                {
                    throw nb::value_error("radius must be > 0");
                }
                NeighborPairs pairs = neighbor_pairs(positions.data(), positions.shape(0), radius);
                return nb::make_tuple(
                    to_array(pairs.i, 1),
                    to_array(pairs.j, 1),
                    to_array(pairs.delta, 2),
                    to_array(pairs.distance, 1)
                );
            },
            nb::arg("positions"),
            nb::arg("radius"),
            "neighbor_pairs for a C-contiguous float64 (n, 2) array (see pyb2d3.extensions)."
        );

        nb::class_<RadialEmitter, Emitter> radial(
            ext,
            "RadialEmitter",
            "Particles leave a point at `radius` from the emitter's origin, in a direction between "
            "`angle_min` and `angle_max` (radians, from the emitter's x axis). A pyb2d3 extension, "
            "not part of Box2D."
        );
        bind_init(radial);
        radial.def_rw("angle_min", &RadialEmitter::angle_min, "Smallest emission angle (rad).")
            .def_rw("angle_max", &RadialEmitter::angle_max, "Largest emission angle (rad).")
            .def_rw("radius", &RadialEmitter::radius, "Distance from the origin where particles start (m).");

        nb::class_<LinearEmitter, Emitter> linear(
            ext,
            "LinearEmitter",
            "Particles leave the line p1 -> p2 (emitter frame) along its left normal, at t = "
            "`along` (0: p1, 1: p2). A pyb2d3 extension, not part of Box2D."
        );
        bind_init(linear);
        linear.def_rw("p1", &LinearEmitter::p1, "Start of the line (emitter frame).")
            .def_rw("p2", &LinearEmitter::p2, "End of the line (emitter frame).")
            .def_rw(
                "along",
                &LinearEmitter::along,
                "Where on the line particles start (t in [0, 1], a Distribution)."
            );
    }
}  // namespace pyb2d3::bind
