#pragma once


// helper to map the value of a function to a numpy array
// ie to get a batch of values for the property "positions" of a body
// one needs a 2d array of shape (N, 2) where N is the number of bodies in the batch
// and the second dimension is the x and y coordinates of the position
// but for the property like "angular_velocities" one needs a 1d array of shape (N,)
// for a b2Rot we need two values (ie c,s)
// for b2Mat22

// nice Table
// | Type       | Shape   |Comment (opt)
// |------------|--------- |----------------------------------------------------------------------------|
// | float      | (N,)     | scalar value for each body in the batch                                    |
// | b2Vec2     | (N, 2)   | vector value for each body in the batch (x,y)                              |
// | b2Rot      | (N, 2)   | rotation value for each body in the batch (c,s)                            |
// | b2Mat22    | (N, 2, 2)| matrix value for each body in the batch (c1,c2,s1,s2)                      |
// | b2AABB     | (N, 2, 2)| axis aligned bounding box for each body in the batch (lower, upper)        |
// | b2Transform| (N, 3, 2)| transform value for each body in the batch (p.x,p.y,c,s)                   |

#include <array>
#include <cstddef>
#include <cstdint>

#include <box2d/box2d.h>
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/optional.h>
#include <pyb2d3/numpy_utils.hpp>

template <class TYPE>
struct ndarray_traits;

// Specialization for b2Vec2
template <>
struct ndarray_traits<b2Vec2>
{
    using value_type = b2Vec2;
    using array_value_type = float;

    // how much do we skip in the **FLAT** array to get to the next item
    static constexpr std::size_t skip_size = 2;


    static constexpr std::size_t n_dim = 2;
    using shape_type = nb::shape<-1, 2>;  // 2D array with second dimension of size 2
    using nd_array_type = nb::ndarray<array_value_type, nb::numpy, shape_type, nb::c_contig>;

    static value_type read(const array_value_type* arr)
    {
        value_type value;
        value.x = arr[0];
        value.y = arr[1];
        return value;
    }

    static void write(const value_type& value, array_value_type* arr)
    {
        arr[0] = value.x;
        arr[1] = value.y;
    }

    static std::array<std::size_t, n_dim> make_shape(std::size_t n)
    {
        return {n, 2};
    }
};

// Specialization for b2Rot
template <>
struct ndarray_traits<b2Rot>
{
    using value_type = b2Rot;
    using array_value_type = float;

    // how much do we skip in the **FLAT** array to get to the next item
    static constexpr std::size_t skip_size = 2;

    static constexpr std::size_t n_dim = 2;
    using shape_type = nb::shape<-1, 2>;  // 2D array with second dimension of size 2
    using nd_array_type = nb::ndarray<array_value_type, nb::numpy, shape_type, nb::c_contig>;

    static value_type read(const array_value_type* arr)
    {
        value_type value;
        value.c = arr[0];
        value.s = arr[1];
        return value;
    }

    static void write(const value_type& value, array_value_type* arr)
    {
        arr[0] = value.c;
        arr[1] = value.s;
    }

    static std::array<std::size_t, n_dim> make_shape(std::size_t n)
    {
        return {n, 2};
    }
};

// store b2Transform as (p.x, p.y, c, s)
template <>
struct ndarray_traits<b2Transform>
{
    using value_type = b2Transform;
    using array_value_type = float;

    // how much do we skip in the **FLAT** array to get to the next item
    static constexpr std::size_t skip_size = 4;

    static constexpr std::size_t n_dim = 2;
    using shape_type = nb::shape<-1, 4>;  // 2D array with second dimension of size 4
    using nd_array_type = nb::ndarray<array_value_type, nb::numpy, shape_type, nb::c_contig>;

    static value_type read(const array_value_type* arr)
    {
        value_type value;
        value.p.x = arr[0];
        value.p.y = arr[1];
        value.q.c = arr[2];
        value.q.s = arr[3];
        return value;
    }

    static void write(const value_type& value, array_value_type* arr)
    {
        arr[0] = value.p.x;
        arr[1] = value.p.y;
        arr[2] = value.q.c;
        arr[3] = value.q.s;
    }

    static std::array<std::size_t, n_dim> make_shape(std::size_t n)
    {
        return {n, 3};
    }
};

template <class T>
struct scalar_ndarray_traits
{
    using value_type = T;
    using array_value_type = value_type;
    static constexpr std::size_t n_dim = 1;

    // how much do we skip in the **FLAT** array to get to the next item
    static constexpr std::size_t skip_size = 1;

    using shape_type = nb::shape<-1>;  // 1D array
    using nd_array_type = nb::ndarray<array_value_type, nb::numpy, shape_type, nb::c_contig>;

    static value_type read(const array_value_type* arr)
    {
        return static_cast<value_type>(*arr);
    }

    static void write(const value_type& value, array_value_type* arr)
    {
        *arr = static_cast<array_value_type>(value);
    }

    static std::array<std::size_t, n_dim> make_shape(std::size_t n)
    {
        return {n};
    }
};

template <>
struct ndarray_traits<float> : public scalar_ndarray_traits<float>
{
};

template <>
struct ndarray_traits<double> : public scalar_ndarray_traits<double>
{
};

template <>
struct ndarray_traits<uint8_t> : public scalar_ndarray_traits<uint8_t>
{
};

template <>
struct ndarray_traits<uint16_t> : public scalar_ndarray_traits<uint16_t>
{
};

template <>
struct ndarray_traits<uint32_t> : public scalar_ndarray_traits<uint32_t>
{
};

template <>
struct ndarray_traits<uint64_t> : public scalar_ndarray_traits<uint64_t>
{
};

template <>
struct ndarray_traits<int8_t> : public scalar_ndarray_traits<int8_t>
{
};

template <>
struct ndarray_traits<int16_t> : public scalar_ndarray_traits<int16_t>
{
};

template <>
struct ndarray_traits<int32_t> : public scalar_ndarray_traits<int32_t>
{
};

template <>
struct ndarray_traits<int64_t> : public scalar_ndarray_traits<int64_t>
{
};

// bool is special, we use int8_t to represent it in numpy
template <>
struct ndarray_traits<bool>
{
    using value_type = bool;
    using array_value_type = uint8_t;  //
    static constexpr std::size_t n_dim = 1;
    // how much do we skip in the **FLAT** array to get to the next item
    static constexpr std::size_t skip_size = 1;
    using shape_type = nb::shape<-1>;  // 1D array
    using nd_array_type = nb::ndarray<array_value_type, nb::numpy, shape_type, nb::c_contig>;

    static value_type read(const array_value_type* arr)
    {
        return static_cast<value_type>(*arr);
    }

    static void write(const value_type& value, array_value_type* arr)
    {
        *arr = static_cast<array_value_type>(value);
    }

    static std::array<std::size_t, n_dim> make_shape(std::size_t n)
    {
        return {n};
    }
};

// alloc for traits
template <class VALUE_TYPE>
inline auto alloc_for_batch(const std::size_t batch_size)
{
    using ndarray_traits_type = ndarray_traits<VALUE_TYPE>;
    using nd_array_type = typename ndarray_traits_type::nd_array_type;

    return alloc_array<nd_array_type, typename ndarray_traits_type::array_value_type>(
        ndarray_traits_type::make_shape(batch_size)
    );
}
