#pragma once
#include <frontend_base.hpp>
#include <nanobind/nanobind.h>
#include <sample.h>
#include <settings.h>

#include "box2d/base.h"
#include "box2d/box2d.h"
#include "box2d/math_functions.h"
#include "draw.h"

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

        OpenGlFrontend(nanobind::list& samples, std::size_t selected_index, Settings& settings);

        ~OpenGlFrontend();

        GLFWwindow* main_window();


        void key_callback(GLFWwindow* window, int key, int scancode, int action, int mods);

        Sample* sample()
        {
            return m_sample;
        }

        void restart_sample();

        Settings& settings();

        void change_sample(std::size_t index);

    public:

        void create_window();

        nanobind::list m_samples;
        std::size_t m_selected_index;
        Settings m_settings;
        Sample* m_sample = nullptr;
        Draw m_draw;

        nanobind::object m_sample_instance;


        GLFWwindow* m_mainWindow;
        // float s_windowScale = 1.0f;
        // float s_framebufferScale = 1.0f;

        std::vector<std::string> m_example_names;
        std::vector<std::string> m_example_groups;
        b2Vec2 s_click_point_ws = b2Vec2_zero;
        bool right_mouse_down = false;
        float window_scale = 1.0f;
        float framebuffer_scale = 1.0f;
    };

}  // namespace pyb2d
