#pragma once

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

// C
// extern "C"
// {
#include <box2d/box2d.h>
#include <box2d/collision.h>
#include <box2d/math_functions.h>

// }

namespace nb = nanobind;

using ArrayVec2 = nb::ndarray<float, nb::numpy, nb::shape<-1, 2>, nb::c_contig>;

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

    // Custom type caster for b2BodyId
    template <>
    struct type_caster<b2BodyId>
    {
        NB_TYPE_CASTER(b2BodyId, const_name("b2BodyId"));

        // Python -> C++ (from int or long)
        bool from_python(nb::handle src, uint8_t flags, cleanup_list*) noexcept
        {
            if (!nb::isinstance<nb::int_>(src))
            {
                return false;
            }
            value = b2LoadBodyId(nb::cast<uint64_t>(src));
            return true;
        }

        // C++ -> Python (to int)
        static nb::handle from_cpp(const b2BodyId& src, rv_policy policy, cleanup_list*)
        {
            return nb::cast(b2StoreBodyId(src)).release();
        }
    };

    // shape id
    template <>
    struct type_caster<b2ShapeId>
    {
        NB_TYPE_CASTER(b2ShapeId, const_name("b2ShapeId"));

        // Python -> C++ (from int or long)
        bool from_python(nb::handle src, uint8_t flags, cleanup_list*) noexcept
        {
            if (!nb::isinstance<nb::int_>(src))
            {
                return false;
            }
            value = b2LoadShapeId(nb::cast<uint64_t>(src));
            return true;
        }

        // C++ -> Python (to int)
        static nb::handle from_cpp(const b2ShapeId& src, rv_policy policy, cleanup_list*)
        {
            return nb::cast(b2StoreShapeId(src)).release();
        }
    };

    // ChainId
    template <>
    struct type_caster<b2ChainId>
    {
        NB_TYPE_CASTER(b2ChainId, const_name("b2ChainId"));

        // Python -> C++ (from int or long)
        bool from_python(nb::handle src, uint8_t flags, cleanup_list*) noexcept
        {
            if (!nb::isinstance<nb::int_>(src))
            {
                return false;
            }
            value = b2LoadChainId(nb::cast<uint64_t>(src));
            return true;
        }

        // C++ -> Python (to int)
        static nb::handle from_cpp(const b2ChainId& src, rv_policy policy, cleanup_list*)
        {
            return nb::cast(b2StoreChainId(src)).release();
        }
    };

    // joint id
    template <>
    struct type_caster<b2JointId>
    {
        NB_TYPE_CASTER(b2JointId, const_name("b2JointId"));

        // Python -> C++ (from int or long)
        bool from_python(nb::handle src, uint8_t flags, cleanup_list*) noexcept
        {
            if (!nb::isinstance<nb::int_>(src))
            {
                return false;
            }
            value = b2LoadJointId(nb::cast<uint64_t>(src));
            return true;
        }

        // C++ -> Python (to int)
        static nb::handle from_cpp(const b2JointId& src, rv_policy policy, cleanup_list*)
        {
            return nb::cast(b2StoreJointId(src)).release();
        }
    };

    // Custom type caster for b2WorldId
    template <>
    struct type_caster<b2WorldId>
    {
        NB_TYPE_CASTER(b2WorldId, const_name("b2WorldId"));

        // Python -> C++ (from int or long)
        bool from_python(nb::handle src, uint8_t flags, cleanup_list*) noexcept
        {
            if (!nb::isinstance<nb::int_>(src))
            {
                return false;
            }
            uint32_t x = nb::cast<uint32_t>(src);
            value = b2WorldId{(uint16_t) (x >> 16), (uint16_t) (x)};
            return true;
        }

        // C++ -> Python (to int)
        static nb::handle from_cpp(const b2WorldId& src, rv_policy policy, cleanup_list*)
        {
            return nb::cast((uint32_t) (src.index1 << 16) | (uint32_t) (src.generation)).release();
        }
    };

}  // namespace nanobind::detail
