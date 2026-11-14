#pragma once

#include <optional>
#include <utility>

#include <nanobind/nanobind.h>

namespace pyb2d3::bind
{
    namespace nb = nanobind;

    // Context for box2d queries that call back into python synchronously (GIL held).
    // A python exception must not unwind through box2d's C frames: the trampoline
    // stores it, stops the query, and `rethrow()` raises it once box2d returned.
    struct QueryContext
    {
        nb::object fn;
        std::optional<nb::python_error> error;

        explicit QueryContext(nb::object f)
            : fn(std::move(f))
        {
        }

        // call fn(args...); on error remember the exception and return `on_error`
        template <class R, class Convert, class... Args>
        R call(R on_error, Convert convert, Args&&... args)
        {
            try
            {
                return convert(fn(std::forward<Args>(args)...));
            }
            catch (nb::python_error& e)
            {
                error.emplace(std::move(e));
                return on_error;
            }
        }

        void rethrow()
        {
            if (error)
            {
                nb::python_error e = std::move(*error);
                error.reset();
                throw e;
            }
        }
    };

    // conversions of callback results: None means "continue"
    inline bool continue_or_bool(nb::handle r)
    {
        return r.is_none() || nb::cast<bool>(r);
    }

    inline float fraction_or_continue(nb::handle r)
    {
        return r.is_none() ? 1.0f : nb::cast<float>(r);
    }
}  // namespace pyb2d3::bind
