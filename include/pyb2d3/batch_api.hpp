#pragma once
#include <vector>

#include <box2d/box2d.h>
#include <box2d/math_functions.h>
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <pyb2d3/py_converter.hpp>
#include <pyb2d3/wrapper_structs.hpp>


namespace nb = nanobind;

template <class ENTITY_TYPE>
struct Ids
{
    using entity_type = ENTITY_TYPE;
    using id_type = typename ENTITY_TYPE::id_type;
    using int_id_type = uint64_t;

    static auto int_to_id(uint64_t id) -> id_type
    {
        return ENTITY_TYPE::int_to_id(id);
    }

    static auto id_to_int(id_type id) -> uint64_t
    {
        return ENTITY_TYPE::id_to_int(id);
    }

    void push_back(id_type id)
    {
        ids.push_back(entity_type::id_to_int(id));
    }

    std::size_t size() const
    {
        return ids.size();
    }

    std::vector<int_id_type> ids;
};

using Bodies = Ids<Body>;
using Shapes = Ids<Shape>;
using Chains = Ids<Chain>;
using Joints = Ids<Joint>;
