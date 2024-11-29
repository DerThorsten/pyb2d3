#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>


// C
extern "C" {
#include <box2d/math_functions.h>
#include <box2d/collision.h>
#include <box2d/box2d.h>
}

namespace nb = nanobind;


using ArrayVec2 = nb::ndarray<float, nb::numpy, nb::shape<-1, 2>, nb::c_contig>;



namespace nanobind::detail 
{

// Custom type caster for b2Vec2
template <>
struct type_caster<b2Vec2>
{
    NB_TYPE_CASTER(b2Vec2, const_name("b2Vec2"));

    // Python -> C++
    bool from_python(nb::handle src, uint8_t flags, cleanup_list *) noexcept {
        if (!nb::isinstance<nb::tuple>(src) || nb::len(src) != 2) {
            return false;
        }

        auto x = nb::cast<float>(src[0]);
        auto y = nb::cast<float>(src[1]);
        value = b2Vec2{x,y};
        return true;
    }

    // C++ -> Python
    static nb::handle from_cpp(const b2Vec2 &src, rv_policy policy, cleanup_list *) {
        return nb::make_tuple(src.x, src.y).release();
    }
};







} // namespace nanobind::detail
