#pragma once
#include <frontend_base.hpp>

#include <nanobind/nanobind.h>

#include "draw.h"
#include <sample.h>
#include <settings.h>

#include "box2d/base.h"
#include "box2d/box2d.h"
#include "box2d/math_functions.h"

// clang-format off
#include <glad/glad.h>
#include <GLFW/glfw3.h>
// clang-format on


namespace pyb2d
{

    class OpenGlFrontend : public FrontendBase
    {
    public:

        OpenGlFrontend(const OpenGlFrontend&) = delete;
        OpenGlFrontend& operator=(const OpenGlFrontend&) = delete;
        OpenGlFrontend(OpenGlFrontend&&) = delete;
        OpenGlFrontend& operator=(OpenGlFrontend&&) = delete;

        OpenGlFrontend(
            //nanobind::object & sample_cls,
            Settings& settings
        );

        ~OpenGlFrontend();

        GLFWwindow* main_window();

    private:

        void create_window();

        GLFWwindow* m_mainWindow;
        float s_windowScale = 1.0f;
        float s_framebufferScale = 1.0f;

    };


} // namespace pyb2d
