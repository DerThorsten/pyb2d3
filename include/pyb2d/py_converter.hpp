#pragma once

#include <iostream>

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

// C
// extern "C"
// {
#include <box2d/box2d.h>
#include <box2d/collision.h>
#include <box2d/math_functions.h>

#include "pyb2d/wrapper_structs.hpp"
// }

namespace nb = nanobind;

using ArrayVec2 = nb::ndarray<float, nb::numpy, nb::shape<-1, 2>, nb::c_contig>;
using ConstArrayVec2 = nb::ndarray<const float, nb::numpy, nb::shape<-1, 2>, nb::c_contig>;
// typedef user_data_int = //  unsiged integer with size of ptr
using user_data_uint = std::uintptr_t;

namespace nanobind::detail
{

    // Custom type caster for b2Vec2
    template <>
    struct type_caster<b2Vec2>
    {
        NB_TYPE_CASTER(b2Vec2, const_name("b2Vec2"));

        // Python -> C++
        bool from_python(nb::handle src, uint8_t flags, cleanup_list*) noexcept
        {
            if (!nb::isinstance<nb::tuple>(src) || nb::len(src) != 2)
            {
                return false;
            }

            auto x = nb::cast<float>(src[0]);
            auto y = nb::cast<float>(src[1]);
            value = b2Vec2{x, y};
            return true;
        }

        // C++ -> Python
        static nb::handle from_cpp(const b2Vec2& src, rv_policy policy, cleanup_list*)
        {
            return nb::make_tuple(src.x, src.y).release();
        }
    };

#define MY_CASTER(ID_TYPE, STRUCT_TYPE, LOADER)                                         \
    template <>                                                                         \
    struct type_caster<ID_TYPE>                                                         \
    {                                                                                   \
        NB_TYPE_CASTER(ID_TYPE, const_name(#ID_TYPE));                                  \
        bool from_python(nb::handle src, uint8_t flags, cleanup_list*) noexcept         \
        {                                                                               \
            if (nb::isinstance<nb::int_>(src))                                          \
            {                                                                           \
                value = LOADER(nb::cast<uint64_t>(src));                                \
                return true;                                                            \
            }                                                                           \
            else if (nb::isinstance<nb::object>(src))                                   \
            {                                                                           \
                try                                                                     \
                {                                                                       \
                    auto id = nb::cast<uint64_t>(src.attr("id"));                       \
                    value = LOADER(id);                                                 \
                    return true;                                                        \
                }                                                                       \
                catch (const nb::cast_error&)                                           \
                {                                                                       \
                    return false;                                                       \
                }                                                                       \
            }                                                                           \
            return false;                                                               \
        }                                                                               \
        static nb::handle from_cpp(const ID_TYPE& src, rv_policy policy, cleanup_list*) \
        {                                                                               \
            auto thing = STRUCT_TYPE(src);                                              \
            return nb::cast(thing).release();                                           \
        }                                                                               \
    }


    MY_CASTER(b2BodyId, Body, b2LoadBodyId);
    MY_CASTER(b2WorldId, WorldView, b2LoadWorldId);
    MY_CASTER(b2ChainId, Chain, b2LoadChainId);

#undef MY_CASTER

    // Custom type caster for b2ShapeId
    template <>
    struct type_caster<b2ShapeId>
    {
        NB_TYPE_CASTER(b2ShapeId, const_name("b2ShapeId"));

        // Python -> C++ (from int or long)
        bool from_python(nb::handle src, uint8_t flags, cleanup_list*) noexcept
        {
            if (nb::isinstance<nb::int_>(src))
            {
                uint32_t x = nb::cast<uint32_t>(src);
                value = b2LoadShapeId(x);
                return true;
            }
            else if (nb::isinstance<nb::object>(src))
            {
                try
                {
                    value = b2LoadShapeId(nb::cast<uint64_t>(src.attr("id")));
                    return true;
                }
                catch (const nb::cast_error& e)
                {
                    return false;
                }
            }
            return false;
        }

        // C++ -> Python (to int)
        static nb::handle from_cpp(const b2ShapeId& src, rv_policy policy, cleanup_list*)
        {
            return GetCastedShape(src).release();
        }
    };

    // Custom type caster for b2JointId
    template <>
    struct type_caster<b2JointId>
    {
        NB_TYPE_CASTER(b2JointId, const_name("b2JointId"));

        // Python -> C++ (from int or long)
        bool from_python(nb::handle src, uint8_t flags, cleanup_list*) noexcept
        {
            if (nb::isinstance<nb::int_>(src))
            {
                uint32_t x = nb::cast<uint32_t>(src);
                value = b2LoadJointId(x);
                return true;
            }
            else if (nb::isinstance<nb::object>(src))
            {
                try
                {
                    value = b2LoadJointId(nb::cast<uint64_t>(src.attr("id")));
                    return true;
                }
                catch (const nb::cast_error& e)
                {
                    return false;
                }
            }
            return false;
        }

        // C++ -> Python (to int)
        static nb::handle from_cpp(const b2JointId& src, rv_policy policy, cleanup_list*)
        {
            return GetCastedJoint(src).release();
        }
    };


}  // namespace nanobind::detail
