#include <cstdint>

#include <box2d/collision.h>
#include <nanobind/nanobind.h>

#include "bind.hpp"
#include "pyb2d3/core/binder.hpp"
#include "query_context.hpp"

namespace pyb2d3::bind
{
    namespace
    {
        // owning wrapper; the member is called `id` so the Binder can forward b2DynamicTree_* calls
        struct PyDynamicTree
        {
            explicit PyDynamicTree(int proxy_capacity)
                : id(b2CreateDynamicTree(proxy_capacity))
            {
            }

            PyDynamicTree(const PyDynamicTree&) = delete;
            PyDynamicTree& operator=(const PyDynamicTree&) = delete;

            ~PyDynamicTree()
            {
                b2DestroyDynamicTree(id);
            }

            b2DynamicTree* id;
        };

        bool tree_query_trampoline(int proxy_id, uint64_t user_data, void* ctx)
        {
            return static_cast<QueryContext*>(ctx)->call(false, continue_or_bool, proxy_id, user_data);
        }

        float tree_ray_trampoline(const b2RayCastInput* input, int proxy_id, uint64_t user_data, void* ctx)
        {
            return static_cast<QueryContext*>(ctx)
                ->call(0.0f, [&](nb::handle r) { return r.is_none() ? input->maxFraction : nb::cast<float>(r); },
                       *input, proxy_id, user_data);
        }

        float tree_box_trampoline(const b2BoxCastInput* input, int proxy_id, uint64_t user_data, void* ctx)
        {
            return static_cast<QueryContext*>(ctx)
                ->call(0.0f, [&](nb::handle r) { return r.is_none() ? input->maxFraction : nb::cast<float>(r); },
                       *input, proxy_id, user_data);
        }
    }  // namespace

    void export_dynamic_tree(nb::module_& m)
    {
        nb::class_<b2BoxCastInput>(m, "BoxCastInput")
            .def(nb::init<>())
            .def_rw("box", &b2BoxCastInput::box)
            .def_rw("translation", &b2BoxCastInput::translation)
            .def_rw("max_fraction", &b2BoxCastInput::maxFraction);

        nb::class_<PyDynamicTree> cls(m, "DynamicTree");
        cls.def(nb::init<int>(), nb::arg("proxy_capacity") = 16);

        Binder(cls)
            .def<b2CreateTreeProxy>("create_proxy", nb::arg("aabb"), nb::arg("category_bits"), nb::arg("user_data") = 0)
            .def<b2DestroyTreeProxy>("destroy_proxy", nb::arg("proxy_id"))
            .def<b2DynamicTree_MoveProxy>("move_proxy", nb::arg("proxy_id"), nb::arg("aabb"))
            .def<b2DynamicTree_SetCategoryBits>("set_category_bits", nb::arg("proxy_id"), nb::arg("category_bits"))
            .def<b2DynamicTree_GetCategoryBits>("get_category_bits", nb::arg("proxy_id"))
            .def<b2DynamicTree_GetUserData>("get_user_data", nb::arg("proxy_id"))
            .def<b2DynamicTree_GetProxyBounds>("get_proxy_bounds", nb::arg("proxy_id"))
            .ro<b2DynamicTree_GetHeight>("height")
            .ro<b2DynamicTree_GetAreaRatio>("area_ratio")
            .ro<b2DynamicTree_GetRootBounds>("root_bounds")
            .ro<b2DynamicTree_GetProxyCount>("proxy_count")
            .ro<b2DynamicTree_GetByteCount>("byte_count")
            .def<b2DynamicTree_Validate>("validate");

        cls.def(
               "overlap_aabb",
               [](const PyDynamicTree& self, b2AABB aabb, nb::object callback, uint64_t mask_bits)
               {
                   QueryContext q(std::move(callback));
                   auto stats = b2DynamicTree_OverlapAABB(self.id, aabb, mask_bits, tree_query_trampoline, &q);
                   q.rethrow();
                   return stats;
               },
               nb::arg("aabb"),
               nb::arg("callback"),
               nb::arg("mask_bits") = B2_DEFAULT_MASK_BITS,
               "callback(proxy_id, user_data) -> bool | None; return False to stop"
        )
            .def(
                "overlap_aabb_all",
                [](const PyDynamicTree& self, b2AABB aabb, nb::object callback)
                {
                    QueryContext q(std::move(callback));
                    auto stats = b2DynamicTree_OverlapAABBAll(self.id, aabb, tree_query_trampoline, &q);
                    q.rethrow();
                    return stats;
                },
                nb::arg("aabb"),
                nb::arg("callback")
            )
            .def(
                "cast_ray",
                [](const PyDynamicTree& self, const b2RayCastInput& input, nb::object callback, uint64_t mask_bits)
                {
                    QueryContext q(std::move(callback));
                    auto stats = b2DynamicTree_CastRay(self.id, &input, mask_bits, tree_ray_trampoline, &q);
                    q.rethrow();
                    return stats;
                },
                nb::arg("input"),
                nb::arg("callback"),
                nb::arg("mask_bits") = B2_DEFAULT_MASK_BITS,
                "callback(input, proxy_id, user_data) -> float | None; the returned value clips the ray"
            )
            .def(
                "cast_box",
                [](const PyDynamicTree& self, const b2BoxCastInput& input, nb::object callback, uint64_t mask_bits)
                {
                    QueryContext q(std::move(callback));
                    auto stats = b2DynamicTree_CastBox(self.id, &input, mask_bits, tree_box_trampoline, &q);
                    q.rethrow();
                    return stats;
                },
                nb::arg("input"),
                nb::arg("callback"),
                nb::arg("mask_bits") = B2_DEFAULT_MASK_BITS
            );
    }
}  // namespace pyb2d3::bind
