#include <string>

#include <nanobind/make_iterator.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <pyb2d3/batch_api.hpp>
#include <pyb2d3/batch_api/batch_exporters.hpp>

// nanobind namespace
namespace nb = nanobind;

template <class ENTITY_TYPE>
void export_batch_core(nb::class_<Ids<ENTITY_TYPE>>& cls)
{
    using exported_type = Ids<ENTITY_TYPE>;
    // Export the Ids struct
    cls.def(nb::init<>())
        .def("append", &Ids<ENTITY_TYPE>::push_back, nb::arg("id"), "Append an item to the batch")
        .def("__len__", &Ids<ENTITY_TYPE>::size, "Get the size of the batch")
        .def(
            "__bool__",
            [](const exported_type& self)
            {
                return !self.ids.empty();
            },
            "Check if the batch is not empty"
        )
        .def(
            "id_iter",
            [](Ids<ENTITY_TYPE>& self)
            {
                return nb::make_iterator(nb::type<exported_type>(), "iterator", self.ids.begin(), self.ids.end());
            },
            nb::keep_alive<0, 1>()
        );
}

void export_body_batch_api(nb::module_& m)
{
    // Export the Ids struct
    auto body_cls = nb::class_<Ids<Body>>(m, "Bodies");

    // constructors, appned / push_back, size
    export_batch_core(body_cls);

    // clang-format off


    // simple "get_" and "set_" methods for body properties
    export_batch_r<uint8_t>(body_cls, "is_valid", [](b2BodyId bodyId) -> uint8_t {return b2Body_IsValid(bodyId) ? 1 : 0;});
    export_batch_rw<uint8_t>(body_cls, "types",
        [](b2BodyId bodyId) -> uint8_t { return static_cast<uint8_t>(b2Body_GetType(bodyId)); },
        [](b2BodyId bodyId, uint8_t type) { b2Body_SetType(bodyId, static_cast<b2BodyType>(type)); });

    // user data
    export_batch_rw<uint64_t>(body_cls, "user_data",
        [](b2BodyId bodyId) -> uint64_t {return reinterpret_cast<uint64_t>(b2Body_GetUserData(bodyId));},
        [](b2BodyId bodyId, uint64_t user_data) { b2Body_SetUserData(bodyId, reinterpret_cast<void*>(user_data));});

    export_batch_r<b2Vec2>(body_cls,"positions",&b2Body_GetPosition);
    export_batch_r<b2Rot>(body_cls,"rotations",&b2Body_GetRotation);

    // transform is a b2Vec2 + b2Rot
    export_batch_rw<b2Transform>(body_cls,"transforms",&b2Body_GetTransform, [](b2BodyId bodyId, const b2Transform & transform) {
        b2Body_SetTransform(bodyId, transform.p, transform.q); // why box2d, why?
    });
    export_batch_rw<b2Vec2>(body_cls,"linear_velocities",&b2Body_GetLinearVelocity, &b2Body_SetLinearVelocity);
    export_batch_r<float>(body_cls, "linear_velocities_magnitude", [](b2BodyId bodyId) -> float { return b2Length(b2Body_GetLinearVelocity(bodyId));});
    export_batch_rw<float>(body_cls, "angular_velocities", &b2Body_GetAngularVelocity, &b2Body_SetAngularVelocity);

    export_batch_vec2_to_vec2<Body>(body_cls, "get_local_points", "world_points", &b2Body_GetLocalPoint, "Get a local point on a body given a world point");
    export_batch_vec2_to_vec2<Body>(body_cls, "get_world_points", "local_points", &b2Body_GetWorldPoint, "Get a world point on a body given a local point");
    export_batch_vec2_to_vec2<Body>(body_cls, "get_local_vectors", "world_vectors", &b2Body_GetLocalVector, "Get a local vector on a body given a world vector");
    export_batch_vec2_to_vec2<Body>(body_cls, "get_world_vectors", "local_vectors", &b2Body_GetWorldVector, "Get a world vector on a body given a local vector");
    export_batch_vec2_to_vec2<Body>(body_cls, "get_local_point_velocities", "world_points", &b2Body_GetLocalPointVelocity, "Get the linear velocity of a local point attached to a body. Usually in meters per second.");
    export_batch_vec2_to_vec2<Body>(body_cls, "get_world_point_velocities", "local_points", &b2Body_GetWorldPointVelocity, "Get the linear velocity of a world point attached to a body. Usually in meters per second.");


    // apply forces and impulses etc.


    // clang-format on
}

void export_batch_api(nb::module_& m)
{
    export_body_batch_api(m);
}
