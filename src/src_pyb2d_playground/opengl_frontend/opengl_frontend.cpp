#include "opengl_frontend.hpp"




#include "draw.h"
#include <sample.h>
#include <settings.h>

#include "box2d/base.h"
#include "box2d/box2d.h"
#include "box2d/math_functions.h"

// clang-format off 
#include <GLFW/glfw3.h>
// clang-format on

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


    static void CreateUI( GLFWwindow* window, const char* glslVersion,
    const char* font_dir )
    {
                static float s_windowScale = 1.0f;
    static float s_framebufferScale = 1.0f;


        IMGUI_CHECKVERSION();
        ImGui::CreateContext();

        bool success = ImGui_ImplGlfw_InitForOpenGL( window, false );
        if ( success == false )
        {
            printf( "ImGui_ImplGlfw_InitForOpenGL failed\n" );
            assert( false );
        }

        success = ImGui_ImplOpenGL3_Init( glslVersion );
        if ( success == false )
        {
            printf( "ImGui_ImplOpenGL3_Init failed\n" );
            assert( false );
        }

        //const char* fontPath = "samples/data/droid_sans.ttf";

        // join the font directory with the font file
        std::string fontPath = std::string(font_dir) + "/droid_sans.ttf";

        FILE* file = fopen( fontPath.c_str(), "rb" );

        if ( file != NULL )
        {
            ImFontConfig fontConfig;
            fontConfig.RasterizerMultiply = s_windowScale * s_framebufferScale;
            g_draw.m_smallFont = ImGui::GetIO().Fonts->AddFontFromFileTTF( fontPath.c_str(), 14.0f, &fontConfig );
            g_draw.m_mediumFont = ImGui::GetIO().Fonts->AddFontFromFileTTF( fontPath.c_str(), 40.0f, &fontConfig );
            g_draw.m_largeFont = ImGui::GetIO().Fonts->AddFontFromFileTTF( fontPath.c_str(), 64.0f, &fontConfig );
        }
        else
        {
            printf( "\n\nERROR: the Box2D samples working directory must be the top level Box2D directory (same as README.md)\n\n" );
            exit( EXIT_FAILURE );
        }
    }






    OpenGlFrontend::OpenGlFrontend(
        Settings& settings//,
        //nanobind::object & sample_cls,
    )
    : FrontendBase(settings)
    {

        glfwSetErrorCallback( []( int error, const char* description ) {
                throw std::runtime_error( description );
        });


        if ( !glfwInit() )
        {
            const char* description;
            glfwGetError(&description); 
            throw std::runtime_error("GLFW initialization failed" + std::string(description));
        }   

        this->create_window();
        glfwSetWindowUserPointer( m_mainWindow, this );
        #if __APPLE__
            const char* glslVersion = "#version 150";
        #else
            const char* glslVersion = nullptr;
        #endif

        CreateUI( m_mainWindow, "#version 150", settings.data_dir.c_str() );

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


    OpenGlFrontend::~OpenGlFrontend()
    {
        DestroyUI();
        glfwTerminate();
    }

} // namespace pyb2d