#pragma once

// `pyb2d3::Points`: a function argument that accepts any collection of 2d points.
//
//   1. fast path (zero copy): a C-contiguous float32 numpy array of shape (n, 2)
//   2. other array-likes (float64, non-contiguous, buffer protocol, __array__):
//      converted once by numpy (vectorized, so big arrays stay fast)
//   3. any other iterable (list / tuple / generator of tuples, Vec2, ...):
//      iterated in C++, every item is converted like a Vec2 argument

#include <cstddef>
#include <vector>

#include <box2d/math_functions.h>
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

namespace pyb2d3
{
    namespace nb = nanobind;

    struct Points
    {
        const b2Vec2* data() const
        {
            return storage.empty() ? view : storage.data();
        }

        std::size_t size() const
        {
            return storage.empty() ? view_size : storage.size();
        }

        int count() const
        {
            return static_cast<int>(size());
        }

        // paths 1 and 2: a view into a numpy array kept alive by `owner`
        const b2Vec2* view = nullptr;
        std::size_t view_size = 0;
        nb::object owner;

        // path 3: copied points
        std::vector<b2Vec2> storage;
    };
}  // namespace pyb2d3

namespace nanobind::detail
{
    template <>
    struct type_caster<pyb2d3::Points>
    {
        NB_TYPE_CASTER(pyb2d3::Points, const_name("collections.abc.Iterable[Vec2-like] | numpy.ndarray[float32, (n, 2)]"))

        using FastArray = ndarray<const float, shape<-1, 2>, c_contig, device::cpu>;

        bool from_python(handle src, uint8_t flags, cleanup_list* cleanup) noexcept
        {
            value = pyb2d3::Points{};

            // 1. zero copy
            if (from_array(src, flags & ~uint8_t(cast_flags::convert), cleanup))
            {
                return true;
            }

            // 2. array-likes: let numpy convert them in one go
            if (PyObject_CheckBuffer(src.ptr()) || hasattr(src, "__array_interface__") || hasattr(src, "__array__"))
            {
                try
                {
                    object np = module_::import_("numpy");
                    object converted = np.attr("ascontiguousarray")(src, arg("dtype") = "float32");
                    if (len(converted) == 0)
                    {
                        value.owner = converted;
                        return true;
                    }
                    return from_array(converted, flags & ~uint8_t(cast_flags::convert), cleanup);
                }
                catch (...)
                {
                    PyErr_Clear();
                    return false;
                }
            }

            // 3. any other iterable
            PyObject* iter = PyObject_GetIter(src.ptr());
            if (!iter)
            {
                PyErr_Clear();
                return false;
            }
            bool ok = true;
            while (PyObject* item = PyIter_Next(iter))
            {
                make_caster<b2Vec2> point;
                ok = point.from_python(item, flags | uint8_t(cast_flags::convert), cleanup);
                if (ok)
                {
                    value.storage.push_back(point.operator b2Vec2&());
                }
                Py_DECREF(item);
                if (!ok)
                {
                    break;
                }
            }
            Py_DECREF(iter);
            if (PyErr_Occurred())
            {
                PyErr_Clear();
                ok = false;
            }
            return ok;
        }

    private:

        bool from_array(handle src, uint8_t flags, cleanup_list* cleanup) noexcept
        {
            make_caster<FastArray> array;
            if (!array.from_python(src, flags, cleanup))
            {
                return false;
            }
            const FastArray& arr = array.value;
            value.view = reinterpret_cast<const b2Vec2*>(arr.data());
            value.view_size = arr.shape(0);
            value.owner = borrow(src);
            return true;
        }
    };
}  // namespace nanobind::detail
