#include "opengl_frontend.hpp"




#include "draw.h"
#include "sample.h"
#include <pyb2d_playground/settings.h>

#include "box2d/base.h"
#include "box2d/box2d.h"
#include "box2d/math_functions.h"

// clang-format off 
#include <GLFW/glfw3.h>
// clang-format on


namespace pyb2d
{

    OpenGlFrontend::OpenGlFrontend(
        Settings& settings//,
        //nanobind::object & sample_cls,
    )
    : FrontendBase(settings)
    {

        if ( !glfwInit() )
        {
            const char* description;
            glfwGetError(&description); 
            throw std::runtime_error("GLFW initialization failed" + std::string(description));
        }   

        this->create_window();
        glfwSetWindowUserPointer( m_mainWindow, this );
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

        glfwWindowHint( GLFW_CONTEXT_VERSION_MAJOR, 3 );
        glfwWindowHint( GLFW_CONTEXT_VERSION_MINOR, 3 );
        glfwWindowHint( GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE );
        glfwWindowHint( GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE );

        // MSAA
        glfwWindowHint( GLFW_SAMPLES, 4 );

        b2Version version = b2GetVersion();
        auto title = "Box2d";

        if ( GLFWmonitor* primaryMonitor = glfwGetPrimaryMonitor() )
        {
            #ifdef __APPLE__
            glfwGetMonitorContentScale( primaryMonitor, &s_framebufferScale, &s_framebufferScale );
            #else
            glfwGetMonitorContentScale( primaryMonitor, &s_windowScale, &s_windowScale );
            #endif
        }

        bool fullscreen = false;
        if ( fullscreen )
        {
            m_mainWindow = glfwCreateWindow( int( 1920 * s_windowScale ), int( 1080 * s_windowScale ), title,
                                            glfwGetPrimaryMonitor(), nullptr );
        }
        else
        {
            
            m_mainWindow = glfwCreateWindow( int( g_camera.m_width * s_windowScale ), int( g_camera.m_height * s_windowScale ), title
                                                , nullptr, nullptr );

        }

        if ( m_mainWindow == nullptr )
        {
            fprintf( stderr, "Failed to open GLFW mainWindow.\n" );
            glfwTerminate();
            throw std::runtime_error("Failed to open GLFW mainWindow");
        }

        #ifdef __APPLE__
        glfwGetWindowContentScale( m_mainWindow, &s_framebufferScale, &s_framebufferScale );
        #else
        glfwGetWindowContentScale( m_mainWindow, &s_windowScale, &s_windowScale );
        #endif

        glfwMakeContextCurrent( m_mainWindow );

        // Load OpenGL functions using glad
        if ( !gladLoadGL() )
        {
            fprintf( stderr, "Failed to initialize glad\n" );
            glfwTerminate();
            throw std::runtime_error("Failed to initialize glad");
        }

    }


} // namespace pyb2d