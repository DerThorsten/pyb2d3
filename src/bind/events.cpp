#include <cstdint>
#include <vector>

#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>

#include "bind.hpp"
#include "pyb2d3/core/binder.hpp"
#include "pyb2d3/py_converter.hpp"

namespace pyb2d3::bind
{
    namespace
    {
        // events live in box2d owned memory until the next step: copy them out
        template <class T>
        std::vector<T> to_vector(const T* data, int count)
        {
            return std::vector<T>(data, data + count);
        }

        template <class T, class... Extra>
        void event_user_data(nb::class_<T, Extra...>& cls)
        {
            cls.def_prop_ro(
                "user_data",
                [](const T& e)
                {
                    return reinterpret_cast<user_data_uint>(e.userData);
                }
            );
        }
    }  // namespace

    void export_events(nb::module_& m)
    {
        // ---- contacts -------------------------------------------------------------------
        nb::class_<Contact>(m, "Contact")
            .def_prop_ro("is_valid", &Contact::IsValid)
            .def_prop_ro(
                "data",
                [](const Contact& c)
                {
                    return b2Contact_GetData(c.id);
                }
            )
            .def(
                "__eq__",
                [](const Contact& a, const Contact& b)
                {
                    return a == b;
                },
                nb::is_operator()
            );

        nb::class_<b2ContactData>(m, "ContactData")
            .def_ro("contact", &b2ContactData::contactId)
            .def_ro("shape_a", &b2ContactData::shapeIdA)
            .def_ro("shape_b", &b2ContactData::shapeIdB)
            .def_ro("manifold", &b2ContactData::manifold);

        // ---- sensor events ----------------------------------------------------------------
        nb::class_<b2SensorBeginTouchEvent>(m, "SensorBeginTouchEvent")
            .def_ro("sensor_shape", &b2SensorBeginTouchEvent::sensorShapeId)
            .def_ro("visitor_shape", &b2SensorBeginTouchEvent::visitorShapeId);

        nb::class_<b2SensorEndTouchEvent>(m, "SensorEndTouchEvent")
            .def_ro("sensor_shape", &b2SensorEndTouchEvent::sensorShapeId)
            .def_ro("visitor_shape", &b2SensorEndTouchEvent::visitorShapeId);

        nb::class_<b2SensorEvents>(m, "SensorEvents")
            .def_ro("begin_count", &b2SensorEvents::beginCount)
            .def_ro("end_count", &b2SensorEvents::endCount)
            .def(
                "begin_events",
                [](const b2SensorEvents& e)
                {
                    return to_vector(e.beginEvents, e.beginCount);
                }
            )
            .def(
                "end_events",
                [](const b2SensorEvents& e)
                {
                    return to_vector(e.endEvents, e.endCount);
                }
            );

        // ---- contact events ---------------------------------------------------------------
        nb::class_<b2ContactBeginTouchEvent>(m, "ContactBeginTouchEvent")
            .def_ro("shape_a", &b2ContactBeginTouchEvent::shapeIdA)
            .def_ro("shape_b", &b2ContactBeginTouchEvent::shapeIdB)
            .def_ro("contact", &b2ContactBeginTouchEvent::contactId);

        nb::class_<b2ContactEndTouchEvent>(m, "ContactEndTouchEvent")
            .def_ro("shape_a", &b2ContactEndTouchEvent::shapeIdA)
            .def_ro("shape_b", &b2ContactEndTouchEvent::shapeIdB)
            .def_ro("contact", &b2ContactEndTouchEvent::contactId);

        nb::class_<b2ContactHitEvent>(m, "ContactHitEvent")
            .def_ro("shape_a", &b2ContactHitEvent::shapeIdA)
            .def_ro("shape_b", &b2ContactHitEvent::shapeIdB)
            .def_ro("contact", &b2ContactHitEvent::contactId)
            .def_ro("point", &b2ContactHitEvent::point)
            .def_ro("normal", &b2ContactHitEvent::normal)
            .def_ro("approach_speed", &b2ContactHitEvent::approachSpeed);

        nb::class_<b2ContactEvents>(m, "ContactEvents")
            .def_ro("begin_count", &b2ContactEvents::beginCount)
            .def_ro("end_count", &b2ContactEvents::endCount)
            .def_ro("hit_count", &b2ContactEvents::hitCount)
            .def(
                "begin_events",
                [](const b2ContactEvents& e)
                {
                    return to_vector(e.beginEvents, e.beginCount);
                }
            )
            .def(
                "end_events",
                [](const b2ContactEvents& e)
                {
                    return to_vector(e.endEvents, e.endCount);
                }
            )
            .def(
                "hit_events",
                [](const b2ContactEvents& e)
                {
                    return to_vector(e.hitEvents, e.hitCount);
                }
            );

        // ---- body move events -------------------------------------------------------------
        nb::class_<b2BodyMoveEvent> move_event(m, "BodyMoveEvent");
        move_event.def_ro("transform", &b2BodyMoveEvent::transform)
            .def_ro("body", &b2BodyMoveEvent::bodyId)
            .def_ro("fell_asleep", &b2BodyMoveEvent::fellAsleep);
        event_user_data(move_event);

        nb::class_<b2BodyEvents>(m, "BodyEvents")
            .def_ro("move_count", &b2BodyEvents::moveCount)
            .def(
                "move_events",
                [](const b2BodyEvents& e)
                {
                    return to_vector(e.moveEvents, e.moveCount);
                }
            )
            // array view of the same data: the cheapest way to sync many moved bodies
            .def_prop_ro(
                "bodies",
                [](const b2BodyEvents& e)
                {
                    Batch<Body> batch;
                    batch.ids.reserve(e.moveCount);
                    for (int i = 0; i < e.moveCount; ++i)
                    {
                        batch.ids.push_back(b2StoreBodyId(e.moveEvents[i].bodyId));
                    }
                    return batch;
                }
            )
            .def_prop_ro(
                "transforms",
                [](const b2BodyEvents& e)
                {
                    float* data = nullptr;
                    nb::object arr = detail::make_array<float>(e.moveCount, 4, data);
                    for (int i = 0; i < e.moveCount; ++i)
                    {
                        batch_value<b2Transform>::store(data + 4 * i, e.moveEvents[i].transform);
                    }
                    return arr;
                }
            )
            .def_prop_ro(
                "fell_asleep",
                [](const b2BodyEvents& e)
                {
                    bool* data = nullptr;
                    nb::object arr = detail::make_array<bool>(e.moveCount, 1, data);
                    for (int i = 0; i < e.moveCount; ++i)
                    {
                        data[i] = e.moveEvents[i].fellAsleep;
                    }
                    return arr;
                }
            );

        // ---- joint events -----------------------------------------------------------------
        nb::class_<b2JointEvent> joint_event(m, "JointEvent");
        joint_event.def_ro("joint", &b2JointEvent::jointId);
        event_user_data(joint_event);

        nb::class_<b2JointEvents>(m, "JointEvents")
            .def_ro("count", &b2JointEvents::count)
            .def(
                "events",
                [](const b2JointEvents& e)
                {
                    return to_vector(e.jointEvents, e.count);
                }
            );
    }
}  // namespace pyb2d3::bind
