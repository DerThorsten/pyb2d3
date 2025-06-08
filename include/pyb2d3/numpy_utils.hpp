#pragma once

#include <cstddef>
#include <initializer_list>

#include <nanobind/nanobind.h>


// nanobind namespace
namespace nb = nanobind;

template <class VALUE_TYPE>
nb::capsule deleter_capsule(VALUE_TYPE* data)
{
    // Create a capsule that will delete the array when done
    return nb::capsule(
        data,
        [](void* p) noexcept
        {
            delete[] (VALUE_TYPE*) p;
        }
    );
}

// same but with initializer list
template <class ARR_TYPE, class SCALAR_TYPE>
ARR_TYPE alloc_array(const std::initializer_list<std::size_t>& shape)
{
    using value_type = SCALAR_TYPE;
    std::size_t size = 1;
    for (auto dim : shape)
    {
        size *= dim;
    };
    // Allocate a new array of the given shape
    value_type* data = new value_type[size];

    // Create a nanobind array from the data pointer
    auto arr = ARR_TYPE(data, shape, deleter_capsule(data));

    // Return the array
    return arr;
}

// same but with std::array
template <class ARR_TYPE, class SCALAR_TYPE, std::size_t N>
ARR_TYPE alloc_array(const std::array<std::size_t, N>& shape)
{
    using value_type = SCALAR_TYPE;
    std::size_t size = 1;
    for (std::size_t i = 0; i < N; ++i)
    {
        size *= shape[i];
    };
    // Allocate a new array of the given shape
    value_type* data = new value_type[size];

    // Create a nanobind array from the data pointer
    auto arr = ARR_TYPE(data, shape.size(), shape.data(), deleter_capsule(data));

    // Return the array
    return arr;
}
