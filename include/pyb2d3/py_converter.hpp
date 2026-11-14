#pragma once

#include <cstdint>

#include <box2d/box2d.h>
#include <box2d/collision.h>
#include <box2d/math_functions.h>
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

#include "pyb2d3/core/handle.hpp"
#include "pyb2d3/wrapper_structs.hpp"

namespace nb = nanobind;

using ArrayVec2 = nb::ndarray<float, nb::numpy, nb::shape<-1, 2>, nb::c_contig>;
using ArrayDoubleVec2 = nb::ndarray<double, nb::numpy, nb::shape<-1, 2>, nb::c_contig>;
using ConstArrayVec2 = nb::ndarray<const float, nb::numpy, nb::shape<-1, 2>, nb::c_contig>;

// user data is exposed to python as an integer of pointer size
using user_data_uint = std::uintptr_t;

namespace pyb2d3
{
    // python object for a valid id: the typed wrapper (CircleShape, RevoluteJoint, ...)
    inline nb::object to_python(b2WorldId id)
    {
        return nb::cast(WorldView(id));
    }

    inline nb::object to_python(b2BodyId id)
    {
        return nb::cast(Body(id));
    }

    inline nb::object to_python(b2ChainId id)
    {
        return nb::cast(Chain(id));
    }

    inline nb::object to_python(b2ShapeId id)
    {
        return GetCastedShape(id);
    }

    inline nb::object to_python(b2JointId id)
    {
        return GetCastedJoint(id);
    }
}  // namespace pyb2d3

namespace nanobind::detail
{
    // Conversion between a box2d id and python.
    //   python -> C++ : a wrapper object of the right type, or a packed integer id
    //   C++ -> python : the (typed) wrapper object, or None for invalid ids
    template <class IdT, class Wrapper>
    bool box2d_id_from_python(handle src, IdT& value) noexcept
    {
        if (nb::isinstance<Wrapper>(src))
        {
            value = nb::cast<const Wrapper&>(src).id;
            return true;
        }
        if (PyLong_Check(src.ptr()))
        {
            const unsigned long long v = PyLong_AsUnsignedLongLong(src.ptr());
            if (PyErr_Occurred())
            {
                PyErr_Clear();
                return false;
            }
            value = pyb2d3::IdTraits<IdT>::load(static_cast<uint64_t>(v));
            return true;
        }
        return false;
    }

    template <class IdT>
    handle box2d_id_from_cpp(const IdT& id) noexcept
    {
        try
        {
            if (!pyb2d3::IdTraits<IdT>::is_valid(id))
            {
                return none().release();
            }
            return pyb2d3::to_python(id).release();
        }
        catch (...)
        {
            return handle();
        }
    }

#define PYB2D3_ID_CASTER(ID_TYPE, WRAPPER, PY_NAME)                                     \
    template <>                                                                         \
    struct type_caster<ID_TYPE>                                                         \
    {                                                                                   \
        NB_TYPE_CASTER(ID_TYPE, const_name(PY_NAME))                                    \
        bool from_python(handle src, uint8_t, cleanup_list*) noexcept                   \
        {                                                                               \
            return box2d_id_from_python<ID_TYPE, WRAPPER>(src, value);                  \
        }                                                                               \
        static handle from_cpp(const ID_TYPE& id, rv_policy, cleanup_list*) noexcept    \
        {                                                                               \
            return box2d_id_from_cpp(id);                                               \
        }                                                                               \
    }

    PYB2D3_ID_CASTER(b2WorldId, WorldView, "WorldView");
    PYB2D3_ID_CASTER(b2BodyId, Body, "Body");
    PYB2D3_ID_CASTER(b2ChainId, Chain, "Chain");
    PYB2D3_ID_CASTER(b2ShapeId, Shape, "Shape");
    PYB2D3_ID_CASTER(b2JointId, Joint, "Joint");

#undef PYB2D3_ID_CASTER

    // contact ids map onto the `Contact` class
    template <>
    struct type_caster<b2ContactId>
    {
        NB_TYPE_CASTER(b2ContactId, const_name("Contact"))

        bool from_python(handle src, uint8_t, cleanup_list*) noexcept
        {
            if (nb::isinstance<Contact>(src))
            {
                value = nb::cast<const Contact&>(src).id;
                return true;
            }
            return false;
        }

        static handle from_cpp(const b2ContactId& id, rv_policy, cleanup_list*) noexcept
        {
            try
            {
                return nb::cast(Contact{id}).release();
            }
            catch (...)
            {
                return handle();
            }
        }
    };

}  // namespace nanobind::detail
