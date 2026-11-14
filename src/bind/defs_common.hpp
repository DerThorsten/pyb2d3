#pragma once

// helpers shared by defs.cpp and joint_defs.cpp

#include <cstdint>

#include <nanobind/nanobind.h>

namespace pyb2d3::bind
{
    namespace nb = nanobind;

    // a def class: default constructed via box2d's b2Default*Def(), plus `copy()`
    template <class T, T (*Default)()>
    nb::class_<T> def_class(nb::module_& m, const char* name)
    {
        nb::class_<T> cls(m, name);
        cls.def(
               "__init__",
               [](T* t)
               {
                   new (t) T(Default());
               }
        )
            .def(
                "copy",
                [](const T& self)
                {
                    return T(self);
                }
            )
            .def(
                "__copy__",
                [](const T& self)
                {
                    return T(self);
                }
            );
        return cls;
    }

    // `user_data` as a pointer sized integer, for any def with a `void* userData` member
    template <class T, class... Extra>
    void def_user_data(nb::class_<T, Extra...>& cls)
    {
        cls.def_prop_rw(
            "user_data",
            [](const T& self)
            {
                return reinterpret_cast<std::uintptr_t>(self.userData);
            },
            [](T& self, std::uintptr_t value)
            {
                self.userData = reinterpret_cast<void*>(value);
            }
        );
    }
}  // namespace pyb2d3::bind
