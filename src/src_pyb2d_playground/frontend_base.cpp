

#include <frontend_base.hpp>

namespace pyb2d
{
    FrontendBase::FrontendBase(
        // nanobind::object & sample_cls,
        Settings& settings
    )
        : m_settings(settings)
    //,
    //    m_sample_cls(sample_cls)
    {
    }

}
