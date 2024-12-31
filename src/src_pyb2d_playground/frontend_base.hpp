#pragma once

#include <settings.h>

namespace pyb2d
{


    class FrontendBase
    {
    public:

        FrontendBase(
            // nanobind::object & sample_cls,
            Settings& settings
        );

        virtual ~FrontendBase() = default;

    protected:

        Settings& m_settings;
        // nanobind::object m_sample_cls;
    };


}  // namespace pyb2d
