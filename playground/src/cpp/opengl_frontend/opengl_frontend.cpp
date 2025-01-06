#include "opengl_frontend.hpp"

#include <sample.h>
#include <settings.h>

#include "box2d/base.h"
#include "box2d/box2d.h"
#include "box2d/math_functions.h"
#include "draw.h"

// clang-format off
#include <GLFW/glfw3.h>
// clang-format on

#include <iostream>

#include <imgui.h>
#include <imgui_impl_glfw.h>
#include <imgui_impl_opengl3.h>

namespace pyb2d
{

    static void DestroyUI()
    {
        ImGui_ImplOpenGL3_Shutdown();
        ImGui_ImplGlfw_Shutdown();
        ImGui::DestroyContext();
    }

    static void CreateUI(GLFWwindow* window, const char* glslVersion, const char* font_dir)
    {
        auto ui = static_cast<OpenGlFrontend*>(glfwGetWindowUserPointer(window));


        IMGUI_CHECKVERSION();
        ImGui::CreateContext();

        bool success = ImGui_ImplGlfw_InitForOpenGL(window, false);
        if (success == false)
        {
            printf("ImGui_ImplGlfw_InitForOpenGL failed\n");
            assert(false);
        }

        success = ImGui_ImplOpenGL3_Init(glslVersion);
        if (success == false)
        {
            printf("ImGui_ImplOpenGL3_Init failed\n");
            assert(false);
        }

        // const char* fontPath = "samples/data/droid_sans.ttf";

        // join the font directory with the font file
        std::string fontPath = std::string(font_dir) + "/droid_sans.ttf";

        FILE* file = fopen(fontPath.c_str(), "rb");

        if (file != NULL)
        {
            ImFontConfig fontConfig;
            fontConfig.RasterizerMultiply = ui->window_scale * ui->framebuffer_scale;
            ui->m_draw.m_smallFont = ImGui::GetIO().Fonts->AddFontFromFileTTF(fontPath.c_str(), 14.0f, &fontConfig);
            ui->m_draw.m_mediumFont = ImGui::GetIO().Fonts->AddFontFromFileTTF(fontPath.c_str(), 40.0f, &fontConfig);
            ui->m_draw.m_largeFont = ImGui::GetIO().Fonts->AddFontFromFileTTF(fontPath.c_str(), 64.0f, &fontConfig);
        }
        else
        {
            printf("\n\nERROR: the Box2D samples working directory must be the top "
                   "level Box2D directory (same as README.md)\n\n");
            exit(EXIT_FAILURE);
        }
    }

    OpenGlFrontend::OpenGlFrontend(nanobind::list& samples, std::size_t selected_index, Settings& settings)
        : FrontendBase(settings)
        , m_samples(samples)
        , m_selected_index(selected_index)
        , m_settings(settings)
        , m_sample(nullptr)
    {
        std::size_t n_examples = samples.size();
        m_example_names.reserve(n_examples);
        m_example_groups.reserve(n_examples);

        for (std::size_t i = 0; i < n_examples; ++i)
        {
            nanobind::str name = samples[i][1];
            nanobind::str group = samples[i][2];
            m_example_names.push_back(name.c_str());
            m_example_groups.push_back(group.c_str());
        }

        glfwSetErrorCallback(
            [](int error, const char* description)
            {
                throw std::runtime_error(description);
            }
        );

        if (!glfwInit())
        {
            const char* description;
            glfwGetError(&description);
            throw std::runtime_error("GLFW initialization failed" + std::string(description));
        }

        this->create_window();
        glfwSetWindowUserPointer(m_mainWindow, this);
#if __APPLE__
        const char* glslVersion = "#version 150";
#else
        const char* glslVersion = nullptr;
#endif

        CreateUI(m_mainWindow, "#version 150", settings.data_dir.c_str());

        m_draw.Create(m_settings.data_dir.c_str());
    }

    GLFWwindow* OpenGlFrontend::main_window()
    {
        return m_mainWindow;
    }

    void OpenGlFrontend::create_window()
    {
#if __APPLE__
        const char* glslVersion = "#version 150";
#else
        const char* glslVersion = nullptr;
#endif

        glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
        glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
        glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
        glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

        // MSAA
        glfwWindowHint(GLFW_SAMPLES, 4);

        b2Version version = b2GetVersion();
        auto title = "Box2d";

        if (GLFWmonitor* primaryMonitor = glfwGetPrimaryMonitor())
        {
#ifdef __APPLE__
            glfwGetMonitorContentScale(primaryMonitor, &framebuffer_scale, &framebuffer_scale);
#else
            glfwGetMonitorContentScale(primaryMonitor, &window_scale, &window_scale);
#endif
        }

        bool fullscreen = false;
        if (fullscreen)
        {
            m_mainWindow = glfwCreateWindow(
                int(1920 * window_scale),
                int(1080 * window_scale),
                title,
                glfwGetPrimaryMonitor(),
                nullptr
            );
        }
        else
        {
            m_mainWindow = glfwCreateWindow(
                int(m_draw.m_camera.m_width * window_scale),
                int(m_draw.m_camera.m_height * window_scale),
                title,
                nullptr,
                nullptr
            );
        }

        if (m_mainWindow == nullptr)
        {
            fprintf(stderr, "Failed to open GLFW mainWindow.\n");
            glfwTerminate();
            throw std::runtime_error("Failed to open GLFW mainWindow");
        }

#ifdef __APPLE__
        glfwGetWindowContentScale(m_mainWindow, &framebuffer_scale, &framebuffer_scale);
#else
        glfwGetWindowContentScale(m_mainWindow, &window_scale, &window_scale);
#endif

        glfwMakeContextCurrent(m_mainWindow);

        // Load OpenGL functions using glad
        if (!gladLoadGL())
        {
            fprintf(stderr, "Failed to initialize glad\n");
            glfwTerminate();
            throw std::runtime_error("Failed to initialize glad");
        }
    }

    OpenGlFrontend::~OpenGlFrontend()
    {
        DestroyUI();
        glfwTerminate();
        if (m_sample != nullptr)
        {
            m_sample->prepare_destruction();
            // m_sample_instance.dec_ref();
            m_sample = nullptr;
        }
        m_draw.Destroy();
    }

    void OpenGlFrontend::key_callback(GLFWwindow* window, int key, int scancode, int action, int mods)
    {
    }

    void OpenGlFrontend::restart_sample()
    {
        if (m_sample != nullptr)
        {
            m_sample->prepare_destruction();
            m_sample = nullptr;
            m_settings.restart = true;
            nanobind::object sample_cls = m_samples[m_selected_index][0];
            m_sample_instance = sample_cls(m_settings);
            m_sample = nanobind::cast<pyb2d::Sample*>(m_sample_instance);
            m_settings.restart = false;
        }
        else
        {
            nanobind::object sample_cls = m_samples[m_selected_index][0];
            m_sample_instance = sample_cls(m_settings);
            m_sample = nanobind::cast<pyb2d::Sample*>(m_sample_instance);
        }
        m_sample->p_debugDraw = &(m_draw.m_debugDraw);
    }

    Settings& OpenGlFrontend::settings()
    {
        return m_settings;
    }

    void OpenGlFrontend::change_sample(std::size_t index)
    {
        m_selected_index = index;
        restart_sample();
    }


}  // namespace pyb2d
