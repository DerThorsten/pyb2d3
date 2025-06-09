#pragma once
#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <pyb2d3/batch_api.hpp>
#include <pyb2d3/batch_api/ndarray_traits.hpp>
#include <pyb2d3/numpy_utils.hpp>

namespace nb = nanobind;

template <class TYPE, class ENTITY_TYPE, class FUNCTION_TYPE>
void export_batch_r(nb::class_<Ids<ENTITY_TYPE>>& cls, const char* pname, FUNCTION_TYPE function)
{
    std::string fname = std::string("get_") + pname;
    std::string doc_str = std::string("Get ") + pname;

    using ndarray_traits_type = ndarray_traits<TYPE>;
    using nd_array_type = typename ndarray_traits_type::nd_array_type;

    cls.def(
        fname.c_str(),
        [function](Ids<ENTITY_TYPE>& self, std::optional<nd_array_type> output_array) -> nd_array_type
        {
            auto arr = output_array.has_value()
                           ? output_array.value()
                           : alloc_array<nd_array_type, float>(ndarray_traits_type::make_shape(self.ids.size()));
            auto view = arr.view();
            auto data_ptr = arr.data();
            for (std::size_t i = 0; i < self.ids.size(); ++i)
            {
                auto value = function(ENTITY_TYPE::int_to_id(self.ids[i]));
                ndarray_traits_type::write(value, data_ptr + i * ndarray_traits_type::skip_size);
            }
            return arr;
        },
        nb::arg("output") = nb::none(),
        doc_str.c_str()
    );
}

template <class TYPE, class ENTITY_TYPE, class FUNCTION_TYPE>
void export_batch_w(nb::class_<Ids<ENTITY_TYPE>>& cls, const char* pname, FUNCTION_TYPE function)
{
    using value_type = TYPE;
    using ndarray_traits_type = ndarray_traits<TYPE>;
    using nd_array_type = typename ndarray_traits_type::nd_array_type;

    std::string fname = std::string("set_") + pname;
    std::string doc = std::string("Set ") + pname;

    // from numpy array
    cls.def(
        fname.c_str(),
        [function](Ids<ENTITY_TYPE>& self, nd_array_type input_array)
        {
            auto data = input_array.data();
            const bool broadcast = input_array.shape(0) == 1;
            for (std::size_t i = 0; i < self.ids.size(); ++i)
            {
                value_type value = ndarray_traits_type::read(
                    data + (broadcast ? 0 : i) * ndarray_traits_type::skip_size
                );
                function(ENTITY_TYPE::int_to_id(self.ids[i]), value);
            }
        },
        nb::arg(pname),
        doc.c_str()
    );

    // from the value itself
    cls.def(
        fname.c_str(),
        [function](Ids<ENTITY_TYPE>& self, TYPE value)
        {
            for (std::size_t i = 0; i < self.ids.size(); ++i)
            {
                function(ENTITY_TYPE::int_to_id(self.ids[i]), value);
            }
        },
        nb::arg(pname),
        doc.c_str()
    );
}

// get & set methods
template <class SCALAR_TYPE, class ENTITY_TYPE, class GET_FUNCTION_TYPE, class SET_FUNCTION_TYPE>
void export_batch_rw(
    nb::class_<Ids<ENTITY_TYPE>>& cls,
    const char* pname,
    GET_FUNCTION_TYPE&& get_function,
    SET_FUNCTION_TYPE&& set_function
)
{
    export_batch_r<SCALAR_TYPE>(cls, pname, std::forward<GET_FUNCTION_TYPE>(get_function));
    export_batch_w<SCALAR_TYPE>(cls, pname, std::forward<SET_FUNCTION_TYPE>(set_function));
}

template <class ENTITY_TYPE, class FUNCTION>
void export_batch_vec2_to_vec2(
    nb::class_<Ids<ENTITY_TYPE>>& cls,
    const char* fname,
    const char* input_name,
    FUNCTION&& function,
    const char* doc
)
{
    cls.def(
        fname,
        [function](
            Ids<ENTITY_TYPE>& self,
            ndarray_traits<b2Vec2>::nd_array_type input_array,
            std::optional<ndarray_traits<b2Vec2>::nd_array_type> output_array
        ) -> ndarray_traits<b2Vec2>::nd_array_type
        {
            using vec2_traits = ndarray_traits<b2Vec2>;

            auto out_arr = output_array.has_value() ? output_array.value()
                                                    : alloc_for_batch<b2Vec2>(self.ids.size());
            auto out_data_ptr = out_arr.data();
            auto input_data_ptr = input_array.data();

            const bool broadcast_input_array = input_array.shape(0) == 1;

            for (std::size_t i = 0; i < self.ids.size(); ++i)
            {
                // get the input value
                b2Vec2 input_value = vec2_traits::read(
                    input_data_ptr + (broadcast_input_array ? 0 : i * vec2_traits::skip_size)
                );


                auto value = function(ENTITY_TYPE::int_to_id(self.ids[i]), input_value);
                vec2_traits::write(value, out_data_ptr + i * vec2_traits::skip_size);
            }
            return out_arr;
        },
        nb::arg(input_name),
        nb::arg("output") = nb::none(),
        doc
    );


    cls.def(
        fname,
        [function](
            Ids<ENTITY_TYPE>& self,
            b2Vec2 input_value,
            std::optional<ndarray_traits<b2Vec2>::nd_array_type> output_array
        ) -> ndarray_traits<b2Vec2>::nd_array_type
        {
            using vec2_traits = ndarray_traits<b2Vec2>;

            auto out_arr = output_array.has_value() ? output_array.value()
                                                    : alloc_for_batch<b2Vec2>(self.ids.size());
            auto out_data_ptr = out_arr.data();

            for (std::size_t i = 0; i < self.ids.size(); ++i)
            {
                auto value = function(ENTITY_TYPE::int_to_id(self.ids[i]), input_value);
                vec2_traits::write(value, out_data_ptr + i * vec2_traits::skip_size);
            }
            return out_arr;
        },
        nb::arg(input_name),
        nb::arg("output") = nb::none(),
        doc
    );
}
