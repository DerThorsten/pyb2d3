#pragma once

#include <algorithm>
#include <cstdint>
#include <functional>
#include <tuple>
#include <type_traits>
#include <utility>
#include <vector>

#include <box2d/box2d.h>
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

#include "pyb2d3/core/handle.hpp"
#include "pyb2d3/generated/docstrings.hpp"

namespace pyb2d3
{
    namespace nb = nanobind;

    // Batch bindings can be compiled out (-DPYB2D3_BATCH_API=OFF in CMake) to
    // compare / reduce binary size. When disabled, no batch template is instantiated.
#ifdef PYB2D3_NO_BATCH_API
    inline constexpr bool batch_api_enabled = false;
#else
    inline constexpr bool batch_api_enabled = true;
#endif

    // -------------------------------------------------------------------------
    // method<F>: turn a box2d C function `R f(IdT, Args...)` into a "member function"
    // of any wrapper type that has an `id` member.
    // -------------------------------------------------------------------------
    template <auto F>
    struct method;

    template <class R, class IdT, class... Args, R (*F)(IdT, Args...)>
    struct method<F>
    {
        using result_type = R;
        using id_type = IdT;
        using args_type = std::tuple<Args...>;

        template <class Self>
        static R call(const Self& self, Args... args)
        {
            return F(self.id, args...);
        }
    };

    template <auto F>
    using result_of_t = typename method<F>::result_type;

    template <auto F, std::size_t I>
    using arg_of_t = std::decay_t<std::tuple_element_t<I, typename method<F>::args_type>>;

    // generic id helpers usable as `auto` template arguments
    template <class IdT>
    bool is_valid_fn(IdT id)
    {
        return IdTraits<IdT>::is_valid(id);
    }

    template <class IdT>
    uint64_t get_user_data_fn(IdT id)
    {
        return static_cast<uint64_t>(reinterpret_cast<std::uintptr_t>(IdTraits<IdT>::get_user_data(id)));
    }

    template <class IdT>
    void set_user_data_fn(IdT id, uint64_t value)
    {
        IdTraits<IdT>::set_user_data(id, reinterpret_cast<void*>(static_cast<std::uintptr_t>(value)));
    }

    // -------------------------------------------------------------------------
    // batch_value<V>: how a value type maps onto a row of a numpy array.
    // Only types with a specialization are batchable.
    // -------------------------------------------------------------------------
    template <class V, class Enable = void>
    struct batch_value
    {
        static constexpr bool enabled = false;
    };

    template <class V, class S, std::size_t W>
    struct batch_value_base
    {
        static constexpr bool enabled = true;
        using scalar = S;
        static constexpr std::size_t width = W;
    };

    template <class V>
    struct batch_value<V, std::enable_if_t<std::is_arithmetic_v<V>>> : batch_value_base<V, V, 1>
    {
        static void store(V* dst, V v)
        {
            dst[0] = v;
        }

        static V load(const V* src)
        {
            return src[0];
        }
    };

    template <class V>
    struct batch_value<V, std::enable_if_t<std::is_enum_v<V>>> : batch_value_base<V, int32_t, 1>
    {
        static void store(int32_t* dst, V v)
        {
            dst[0] = static_cast<int32_t>(v);
        }

        static V load(const int32_t* src)
        {
            return static_cast<V>(src[0]);
        }
    };

    template <>
    struct batch_value<b2Vec2> : batch_value_base<b2Vec2, float, 2>
    {
        static void store(float* dst, b2Vec2 v)
        {
            dst[0] = v.x;
            dst[1] = v.y;
        }

        static b2Vec2 load(const float* src)
        {
            return b2Vec2{src[0], src[1]};
        }
    };

    template <>
    struct batch_value<b2Rot> : batch_value_base<b2Rot, float, 2>
    {
        static void store(float* dst, b2Rot v)
        {
            dst[0] = v.c;
            dst[1] = v.s;
        }

        static b2Rot load(const float* src)
        {
            return b2Rot{src[0], src[1]};
        }
    };

    template <>
    struct batch_value<b2Transform> : batch_value_base<b2Transform, float, 4>
    {
        static void store(float* dst, b2Transform v)
        {
            dst[0] = v.p.x;
            dst[1] = v.p.y;
            dst[2] = v.q.c;
            dst[3] = v.q.s;
        }

        static b2Transform load(const float* src)
        {
            return b2Transform{{src[0], src[1]}, {src[2], src[3]}};
        }
    };

    template <class V>
    inline constexpr bool is_batchable_v = batch_value<std::decay_t<V>>::enabled;

    // -------------------------------------------------------------------------
    // Batch<T>: a flat array of ids of wrapper type T. Batch accessors are
    // generated automatically from the same declarations as the single-object API.
    // -------------------------------------------------------------------------
    template <class T>
    struct Batch
    {
        using entity_type = T;
        using id_type = typename T::id_type;

        std::vector<uint64_t> ids;

        std::size_t size() const
        {
            return ids.size();
        }

        id_type id(std::size_t i) const
        {
            return T::int_to_id(ids[i]);
        }
    };

    namespace detail
    {
        template <class S>
        nb::object make_array(std::size_t n, std::size_t width, S*& data)
        {
            data = new S[n * width];
            nb::capsule owner(
                data,
                [](void* p) noexcept
                {
                    delete[] static_cast<S*>(p);
                }
            );
            if (width == 1)
            {
                return nb::cast(nb::ndarray<nb::numpy, S, nb::ndim<1>>(data, {n}, owner));
            }
            return nb::cast(nb::ndarray<nb::numpy, S, nb::ndim<2>>(data, {n, width}, owner));
        }

        template <class S>
        const char* numpy_dtype_name()
        {
            if constexpr (std::is_same_v<S, float>)
            {
                return "float32";
            }
            else if constexpr (std::is_same_v<S, double>)
            {
                return "float64";
            }
            else if constexpr (std::is_same_v<S, bool>)
            {
                return "bool";
            }
            else if constexpr (std::is_same_v<S, int32_t>)
            {
                return "int32";
            }
            else if constexpr (std::is_same_v<S, uint64_t>)
            {
                return "uint64";
            }
            else
            {
                static_assert(sizeof(S) == 0, "unsupported batch scalar type");
            }
        }

        // convert any array-like python object into a contiguous array of the given scalar type
        template <class S>
        nb::ndarray<const S, nb::c_contig, nb::device::cpu> as_array(nb::handle value)
        {
            nb::object np = nb::module_::import_("numpy");
            nb::object arr = np.attr("ascontiguousarray")(value, nb::arg("dtype") = numpy_dtype_name<S>());
            return nb::cast<nb::ndarray<const S, nb::c_contig, nb::device::cpu>>(arr);
        }
    }  // namespace detail

    // getter: batch.name -> array of shape (n,) or (n, width)
    template <class T, auto Get>
    nb::object batch_get(const Batch<T>& batch)
    {
        using V = std::decay_t<result_of_t<Get>>;
        using bv = batch_value<V>;
        using S = typename bv::scalar;
        const std::size_t n = batch.size();
        S* data = nullptr;
        nb::object result = detail::make_array<S>(n, bv::width, data);
        for (std::size_t i = 0; i < n; ++i)
        {
            bv::store(data + i * bv::width, Get(batch.id(i)));
        }
        return result;
    }

    // setter: batch.name = value; value is broadcast if it is a single element
    template <class T, auto Set>
    void batch_set(Batch<T>& batch, nb::handle value)
    {
        using V = arg_of_t<Set, 0>;
        using bv = batch_value<V>;
        using S = typename bv::scalar;
        auto arr = detail::as_array<S>(value);
        const std::size_t n = batch.size();
        const std::size_t total = arr.size();
        const bool broadcast = (total == bv::width);
        if (!broadcast && total != n * bv::width)
        {
            throw nb::value_error("value has the wrong size: expected one element or one element per batch entry");
        }
        const S* ptr = arr.data();
        for (std::size_t i = 0; i < n; ++i)
        {
            Set(batch.id(i), bv::load(ptr + (broadcast ? 0 : i * bv::width)));
        }
    }

    // -------------------------------------------------------------------------
    // batch methods: `batch.f(a, b)` calls `f(id_i, a_i, b_i)` for every id.
    // Every argument is either one value per batch entry or a single value that
    // is broadcast. Returns an array of results (or None for void functions).
    // -------------------------------------------------------------------------
    namespace detail
    {
        template <class V>
        struct batch_arg
        {
            using bv = batch_value<V>;
            using S = typename bv::scalar;

            batch_arg(nb::handle value, std::size_t n)
                : array(as_array<S>(value))
            {
                const std::size_t total = array.size();
                broadcast = (total == bv::width);
                if (!broadcast && total != n * bv::width)
                {
                    throw nb::value_error(
                        "argument has the wrong size: expected one element or one element per batch entry"
                    );
                }
            }

            V get(std::size_t i) const
            {
                return bv::load(array.data() + (broadcast ? 0 : i * bv::width));
            }

            nb::ndarray<const S, nb::c_contig, nb::device::cpu> array;
            bool broadcast = false;
        };

        template <class>
        using as_object = nb::object;
    }  // namespace detail

    template <class T, auto F, class Args = typename method<F>::args_type>
    struct batch_method;

    template <class T, auto F, class... A>
    struct batch_method<T, F, std::tuple<A...>>
    {
        using R = result_of_t<F>;

        static constexpr bool enabled = (is_batchable_v<A> && ...)
                                        && (std::is_void_v<R> || is_batchable_v<R>);

        static nb::object call(Batch<T>& batch, detail::as_object<A>... args)
        {
            return call_impl(batch, std::index_sequence_for<A...>{}, args...);
        }

    private:

        template <std::size_t... I>
        static nb::object call_impl(Batch<T>& batch, std::index_sequence<I...>, detail::as_object<A>... args)
        {
            const std::size_t n = batch.size();
            std::tuple<detail::batch_arg<std::decay_t<A>>...> arrays{
                detail::batch_arg<std::decay_t<A>>(args, n)...
            };

            if constexpr (std::is_void_v<R>)
            {
                for (std::size_t i = 0; i < n; ++i)
                {
                    F(batch.id(i), std::get<I>(arrays).get(i)...);
                }
                return nb::none();
            }
            else
            {
                using bv = batch_value<std::decay_t<R>>;
                typename bv::scalar* data = nullptr;
                nb::object result = detail::make_array<typename bv::scalar>(n, bv::width, data);
                for (std::size_t i = 0; i < n; ++i)
                {
                    bv::store(data + i * bv::width, F(batch.id(i), std::get<I>(arrays).get(i)...));
                }
                return result;
            }
        }
    };

    // -------------------------------------------------------------------------
    // Binder: declarative binding of box2d C functions as properties / methods.
    //
    //   Binder(cls, batch_cls)       // with batch mirror (Binder<Body, void, true>)
    //       .rw<b2Body_GetLinearDamping, b2Body_SetLinearDamping>("linear_damping")
    //       .def<b2Body_ApplyTorque>("apply_torque", nb::arg("torque"), nb::arg("wake") = true);
    //
    //   Binder(cls)                  // no batch class: no batch code is instantiated
    //
    // Whether batch versions are generated is a compile time property, so binders
    // without a batch class do not pay for the batch templates in binary size.
    //
    // Docstrings come from box2d's own doc comments (docs::doc<F>, generated by
    // scripts/generate_docstrings.py); a property uses the getter's doc.
    // -------------------------------------------------------------------------
    template <class T, class Base = void, bool WithBatch = false>
    class Binder
    {
    public:

        using cls_type = std::conditional_t<std::is_void_v<Base>, nb::class_<T>, nb::class_<T, Base>>;
        using batch_cls_type = nb::class_<Batch<T>>;

        static constexpr bool with_batch = WithBatch && batch_api_enabled;

        explicit Binder(cls_type& cls)
            : m_cls(cls)
            , m_batch_cls(nullptr)
        {
            static_assert(!WithBatch, "a batch binder needs a batch class");
        }

        Binder(cls_type& cls, batch_cls_type& batch_cls)
            : m_cls(cls)
            , m_batch_cls(&batch_cls)
        {
        }

        template <auto Get>
        Binder& ro(const char* name)
        {
            m_cls.def_prop_ro(name, &method<Get>::template call<T>, docs::doc<Get>);
            if constexpr (with_batch && is_batchable_v<result_of_t<Get>>)
            {
                m_batch_cls->def_prop_ro(name, &batch_get<T, Get>, docs::doc<Get>);
            }
            return *this;
        }

        template <auto Get, auto Set>
        Binder& rw(const char* name)
        {
            m_cls.def_prop_rw(name, &method<Get>::template call<T>, &method<Set>::template call<T>, docs::doc<Get>);
            if constexpr (with_batch && is_batchable_v<result_of_t<Get>> && is_batchable_v<arg_of_t<Set, 0>>)
            {
                m_batch_cls->def_prop_rw(name, &batch_get<T, Get>, &batch_set<T, Set>, docs::doc<Get>);
            }
            return *this;
        }

        // method; mirrored on the batch class if all arguments / the result are batchable
        template <auto F, class... Extra>
        Binder& def(const char* name, const Extra&... extra)
        {
            m_cls.def(name, &method<F>::template call<T>, extra..., docs::doc<F>);
            if constexpr (with_batch && batch_method<T, F>::enabled)
            {
                m_batch_cls->def(name, &batch_method<T, F>::call, extra..., docs::doc<F>);
            }
            return *this;
        }

        // escape hatch for anything that is not a 1:1 mapping
        cls_type& cls()
        {
            return m_cls;
        }

    private:

        cls_type& m_cls;
        batch_cls_type* m_batch_cls;
    };

    template <class T>
    Binder(nb::class_<T>&) -> Binder<T>;

    template <class T, class Base>
    Binder(nb::class_<T, Base>&) -> Binder<T, Base>;

    template <class T>
    Binder(nb::class_<T>&, nb::class_<Batch<T>>&) -> Binder<T, void, true>;

    // -------------------------------------------------------------------------
    // common bindings shared by every id-handle type (id, validity, equality,
    // hashing, user data) and by every batch type.
    // -------------------------------------------------------------------------
    namespace detail
    {
        template <class T, class B>
        void bind_handle_common(nb::class_<T>& cls, B& b)
        {
            using IdT = typename T::id_type;

            cls.def(nb::init<uint64_t>(), nb::arg("id"))
            .def_prop_ro(
                "id",
                [](const T& self)
                {
                    return self.int_id();
                }
            )
            // is_operator: comparing with another type (e.g. None) returns NotImplemented
            // instead of raising, so `body in [None, ...]` and `body == None` work
            .def(
                "__eq__",
                [](const T& self, const T& other)
                {
                    return self.int_id() == other.int_id();
                },
                nb::is_operator()
            )
            .def(
                "__ne__",
                [](const T& self, const T& other)
                {
                    return self.int_id() != other.int_id();
                },
                nb::is_operator()
            )
            .def(
                "__hash__",
                [](const T& self)
                {
                    return std::hash<uint64_t>{}(self.int_id());
                }
            )
            .def(
                "__repr__",
                [](nb::handle self)
                {
                    return nb::str("{}(id={})").format(
                        nb::type_name(self.type()),
                        nb::cast<const T&>(self).int_id()
                    );
                }
            );

            b.template ro<&is_valid_fn<IdT>>("is_valid");

            if constexpr (!std::is_same_v<IdT, b2ChainId>)
            {
                b.template rw<&get_user_data_fn<IdT>, &set_user_data_fn<IdT>>("user_data");
            }
        }
    }  // namespace detail

    // id, is_valid, ==, !=, hash, repr, user_data
    template <class T>
    void bind_handle(nb::class_<T>& cls)
    {
        Binder<T> b(cls);
        detail::bind_handle_common(cls, b);
    }

    // same, plus the batch class (construction from ids / handles, len, ids)
    template <class T>
    void bind_handle(nb::class_<T>& cls, nb::class_<Batch<T>>& batch_cls)
    {
        Binder<T, void, true> b(cls, batch_cls);
        detail::bind_handle_common(cls, b);

        {
            batch_cls.def(nb::init<>())
                // fast path: an array of ids
                .def(
                    "__init__",
                    [](Batch<T>* self, nb::ndarray<const uint64_t, nb::ndim<1>, nb::device::cpu> ids)
                    {
                        new (self) Batch<T>();
                        self->ids.resize(ids.shape(0));
                        auto view = ids.view();
                        for (std::size_t i = 0; i < ids.shape(0); ++i)
                        {
                            self->ids[i] = view(i);
                        }
                    },
                    nb::arg("ids")
                )
                // any iterable of handles or (numpy) integer ids
                .def(
                    "__init__",
                    [](Batch<T>* self, nb::iterable items)
                    {
                        new (self) Batch<T>();
                        for (nb::handle item : items)
                        {
                            if (nb::isinstance<T>(item))
                            {
                                self->ids.push_back(nb::cast<const T&>(item).int_id());
                            }
                            else
                            {
                                self->ids.push_back(nb::cast<uint64_t>(nb::int_(item)));
                            }
                        }
                    },
                    nb::arg("items")
                )
                .def(
                    "append",
                    [](Batch<T>& self, const T& item)
                    {
                        self.ids.push_back(item.int_id());
                    },
                    nb::arg("item")
                )
                .def("__len__", &Batch<T>::size)
                .def_prop_ro(
                    "ids",
                    [](const Batch<T>& self)
                    {
                        uint64_t* data = nullptr;
                        nb::object arr = detail::make_array<uint64_t>(self.size(), 1, data);
                        std::copy(self.ids.begin(), self.ids.end(), data);
                        return arr;
                    }
                );
        }
    }

}  // namespace pyb2d3
