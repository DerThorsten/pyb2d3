#include <cmath>
#include <string>

#include <box2d/math_functions.h>
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>

#include "bind.hpp"

namespace pyb2d3::bind
{
    namespace
    {
        float& component(b2Vec2& v, int index)
        {
            switch (index)
            {
                case 0:
                case -2:
                    return v.x;
                case 1:
                case -1:
                    return v.y;
                default:
                    throw nb::index_error("Vec2 index out of range");
            }
        }

        // apply a scalar function to both components
        template <class F>
        b2Vec2 map(b2Vec2 v, F f)
        {
            return b2Vec2{f(v.x), f(v.y)};
        }
    }  // namespace

    void export_vec2(nb::module_& m)
    {
        using Float2 = nb::ndarray<float, nb::numpy, nb::shape<2>>;
        using Double2 = nb::ndarray<double, nb::numpy, nb::shape<2>>;

        nb::class_<b2Vec2>(m, "Vec2")
            .def(
                "__init__",
                [](b2Vec2* t, float x, float y)
                {
                    new (t) b2Vec2{x, y};
                },
                nb::arg("x") = 0.0f,
                nb::arg("y") = 0.0f
            )
            .def(
                "__init__",
                [](b2Vec2* t, const b2Vec2& other)
                {
                    new (t) b2Vec2(other);
                }
            )
            // any sequence of two numbers: (x, y), [x, y], ...
            .def(
                "__init__",
                [](b2Vec2* t, nb::sequence seq)
                {
                    if (nb::len(seq) != 2)
                    {
                        throw nb::value_error("Vec2 needs a sequence of length 2");
                    }
                    new (t) b2Vec2{nb::cast<float>(seq[0]), nb::cast<float>(seq[1])};
                }
            )
            .def(
                "__init__",
                [](b2Vec2* t, Float2 a)
                {
                    new (t) b2Vec2{a(0), a(1)};
                }
            )
            .def(
                "__init__",
                [](b2Vec2* t, Double2 a)
                {
                    new (t) b2Vec2{float(a(0)), float(a(1))};
                }
            )
            .def_rw("x", &b2Vec2::x)
            .def_rw("y", &b2Vec2::y)
            .def("normalize", &b2Normalize)
            .def("length", &b2Length)
            .def("length_squared", &b2LengthSquared)
            .def(
                "__len__",
                [](const b2Vec2&)
                {
                    return 2;
                }
            )
            .def(
                "__getitem__",
                [](b2Vec2& v, int i)
                {
                    return component(v, i);
                }
            )
            .def(
                "__setitem__",
                [](b2Vec2& v, int i, float value)
                {
                    component(v, i) = value;
                }
            )
            .def(
                "__repr__",
                [](const b2Vec2& v)
                {
                    return "Vec2(" + std::to_string(v.x) + ", " + std::to_string(v.y) + ")";
                }
            )
            .def(
                "__eq__",
                [](const b2Vec2& a, const b2Vec2& b)
                {
                    return a.x == b.x && a.y == b.y;
                },
                nb::is_operator()  // NotImplemented for other types (e.g. pytest.approx)
            )
            // arithmetic
            .def("__add__", &b2Add, nb::is_operator())
            .def("__sub__", &b2Sub, nb::is_operator())
            .def("__neg__", &b2Neg)
            .def(
                "__mul__",
                [](b2Vec2 a, float s)
                {
                    return b2MulSV(s, a);
                },
                nb::is_operator()
            )
            .def(
                "__rmul__",
                [](b2Vec2 a, float s)
                {
                    return b2MulSV(s, a);
                },
                nb::is_operator()
            )
            .def(
                "__truediv__",
                [](b2Vec2 a, float s)
                {
                    return b2MulSV(1.0f / s, a);
                },
                nb::is_operator()
            )
            .def(
                "__floordiv__",
                [](b2Vec2 a, float s)
                {
                    return map(
                        a,
                        [s](float c)
                        {
                            return std::floor(c / s);
                        }
                    );
                }
            )
            .def(
                "__floor__",
                [](b2Vec2 a)
                {
                    return map(
                        a,
                        [](float c)
                        {
                            return std::floor(c);
                        }
                    );
                }
            )
            .def(
                "__ceil__",
                [](b2Vec2 a)
                {
                    return map(
                        a,
                        [](float c)
                        {
                            return std::ceil(c);
                        }
                    );
                }
            )
            // in-place
            .def(
                "__iadd__",
                [](b2Vec2& a, b2Vec2 b)
                {
                    a = b2Add(a, b);
                    return a;
                }
            )
            .def(
                "__iadd__",
                [](b2Vec2& a, float s)
                {
                    a = b2Add(a, b2Vec2{s, s});
                    return a;
                }
            )
            .def(
                "__isub__",
                [](b2Vec2& a, b2Vec2 b)
                {
                    a = b2Sub(a, b);
                    return a;
                }
            )
            .def(
                "__isub__",
                [](b2Vec2& a, float s)
                {
                    a = b2Sub(a, b2Vec2{s, s});
                    return a;
                }
            )
            .def(
                "__imul__",
                [](b2Vec2& a, float s)
                {
                    a = b2MulSV(s, a);
                    return a;
                }
            )
            .def(
                "__itruediv__",
                [](b2Vec2& a, float s)
                {
                    a = b2MulSV(1.0f / s, a);
                    return a;
                }
            );

        // tuples, lists and length-2 numpy arrays are accepted wherever a Vec2 is expected
        nb::implicitly_convertible<nb::tuple, b2Vec2>();
        nb::implicitly_convertible<nb::list, b2Vec2>();
        nb::implicitly_convertible<Float2, b2Vec2>();
        nb::implicitly_convertible<Double2, b2Vec2>();
    }
}  // namespace pyb2d3::bind
