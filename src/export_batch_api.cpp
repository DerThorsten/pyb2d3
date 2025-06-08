#include <iostream>
#include <string>

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <pyb2d3/batch_api.hpp>
#include <pyb2d3/numpy_utils.hpp>
#include <pyb2d3/py_converter.hpp>
// string_view
#include <string_view>

// nanobind namespace
namespace nb = nanobind;


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

template <class ENTITY_TYPE>
void export_batch_core(nb::class_<Ids<ENTITY_TYPE>>& cls)
{
    // Export the Ids struct
    cls.def(nb::init<>())
        .def("append", &Ids<ENTITY_TYPE>::push_back, nb::arg("id"), "Append an item to the batch")
        .def("__len__", &Ids<ENTITY_TYPE>::size, "Get the number of items in the batch");
}

void export_body_batch_api(nb::module_& m)
{
    // Export the Ids struct
    auto body_cls = nb::class_<Ids<Body>>(m, "Bodies");

    // constructors, appned / push_back, size
    export_batch_core(body_cls);

    // clang-format off



    export_batch_r<uint8_t>(body_cls, "is_valid", [](b2BodyId bodyId) -> uint8_t {return b2Body_IsValid(bodyId) ? 1 : 0;});
    export_batch_rw<uint8_t>(body_cls, "types",
        [](b2BodyId bodyId) -> uint8_t { return static_cast<uint8_t>(b2Body_GetType(bodyId)); },
        [](b2BodyId bodyId, uint8_t type) { b2Body_SetType(bodyId, static_cast<b2BodyType>(type)); });

    // user data
    export_batch_rw<uint64_t>(body_cls, "user_data",
        [](b2BodyId bodyId) -> uint64_t {return reinterpret_cast<uint64_t>(b2Body_GetUserData(bodyId));},
        [](b2BodyId bodyId, uint64_t user_data) { b2Body_SetUserData(bodyId, reinterpret_cast<void*>(user_data));});

    export_batch_r<b2Vec2>(body_cls,"positions",&b2Body_GetPosition);
    export_batch_r<b2Rot>(body_cls,"rotations",&b2Body_GetRotation);

    // transform is a b2Vec2 + b2Rot
    export_batch_rw<b2Transform>(body_cls,"transforms",&b2Body_GetTransform, [](b2BodyId bodyId, const b2Transform & transform) {
        b2Body_SetTransform(bodyId, transform.p, transform.q); // why box2d, why?
    });

    export_batch_rw<b2Vec2>(body_cls,"linear_velocities",&b2Body_GetLinearVelocity, &b2Body_SetLinearVelocity);
    export_batch_r<float>(body_cls, "linear_velocities_magnitude", [](b2BodyId bodyId) -> float { return b2Length(b2Body_GetLinearVelocity(bodyId));});
    export_batch_rw<float>(body_cls, "angular_velocities", &b2Body_GetAngularVelocity, &b2Body_SetAngularVelocity);

    // clang-format on
}

void export_batch_api(nb::module_& m)
{
    export_body_batch_api(m);
}
