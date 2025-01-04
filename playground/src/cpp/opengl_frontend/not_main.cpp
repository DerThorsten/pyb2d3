//  ------------------------------------------------------------------
//  this is a heavy modification of the original sample code:
//  * the motivation is to use the high performance sample code but
//    with the python bindings
//  ------------------------------------------------------------------

// SPDX-FileCopyrightText: 2023 Erin Catto
// SPDX-License-Identifier: MIT

#define _CRT_SECURE_NO_WARNINGS
#define _CRTDBG_MAP_ALLOC
#define IMGUI_DISABLE_OBSOLETE_FUNCTIONS 1

#include <py_sample_base.hpp>
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

#include <iostream>

#include <imgui.h>
#include <imgui_impl_glfw.h>
#include <imgui_impl_opengl3.h>
#include <nanobind/nanobind.h>
#include <stdio.h>
#include <stdlib.h>

#include "opengl_frontend.hpp"

namespace pyb2d
{

    inline bool IsPowerOfTwo(int32_t x)
    {
        return (x != 0) && ((x & (x - 1)) == 0);
    }

    void* AllocFcn(uint32_t size, int32_t alignment)
    {
        // Allocation must be a multiple of alignment or risk a seg fault
        // https://en.cppreference.com/w/c/memory/aligned_alloc
        assert(IsPowerOfTwo(alignment));
        size_t sizeAligned = ((size - 1) | (alignment - 1)) + 1;
        assert((sizeAligned & (alignment - 1)) == 0);

#if defined(_WIN64) || defined(_WIN32)
        void* ptr = _aligned_malloc(sizeAligned, alignment);
#else
        void* ptr = aligned_alloc(alignment, sizeAligned);
#endif
        assert(ptr != nullptr);
        return ptr;
    }

    void FreeFcn(void* mem)
    {
#if defined(_WIN64) || defined(_WIN32)
        _aligned_free(mem);
#else
        free(mem);
#endif
    }

    static void ResizeWindowCallback(GLFWwindow* window, int width, int height)
    {
        auto ui = static_cast<OpenGlFrontend*>(glfwGetWindowUserPointer(window));
        g_camera.m_width = int(width / ui->window_scale);
        g_camera.m_height = int(height / ui->window_scale);
        ui->settings().windowWidth = int(width / ui->window_scale);
        ui->settings().windowHeight = int(height / ui->window_scale);
    }

    static void KeyCallback(GLFWwindow* window, int key, int scancode, int action, int mods)
    {
        // get user pointer from window
        auto ui = static_cast<OpenGlFrontend*>(glfwGetWindowUserPointer(window));


        ImGui_ImplGlfw_KeyCallback(window, key, scancode, action, mods);
        if (ImGui::GetIO().WantCaptureKeyboard)
        {
            return;
        }

        if (action == GLFW_PRESS)
        {
            switch (key)
            {
                case GLFW_KEY_ESCAPE:
                    // Quit
                    glfwSetWindowShouldClose(window, GL_TRUE);
                    break;

                case GLFW_KEY_LEFT:
                    // Pan left
                    if (mods == GLFW_MOD_CONTROL)
                    {
                        b2Vec2 newOrigin = {2.0f, 0.0f};
                        ui->sample()->ShiftOrigin(newOrigin);
                    }
                    else
                    {
                        g_camera.m_center.x -= 0.5f;
                    }
                    break;

                case GLFW_KEY_RIGHT:
                    // Pan right
                    if (mods == GLFW_MOD_CONTROL)
                    {
                        b2Vec2 newOrigin = {-2.0f, 0.0f};
                        ui->sample()->ShiftOrigin(newOrigin);
                    }
                    else
                    {
                        g_camera.m_center.x += 0.5f;
                    }
                    break;

                case GLFW_KEY_DOWN:
                    // Pan down
                    if (mods == GLFW_MOD_CONTROL)
                    {
                        b2Vec2 newOrigin = {0.0f, 2.0f};
                        ui->sample()->ShiftOrigin(newOrigin);
                    }
                    else
                    {
                        g_camera.m_center.y -= 0.5f;
                    }
                    break;

                case GLFW_KEY_UP:
                    // Pan up
                    if (mods == GLFW_MOD_CONTROL)
                    {
                        b2Vec2 newOrigin = {0.0f, -2.0f};
                        ui->sample()->ShiftOrigin(newOrigin);
                    }
                    else
                    {
                        g_camera.m_center.y += 0.5f;
                    }
                    break;

                case GLFW_KEY_HOME:
                    g_camera.ResetView();
                    break;

                case GLFW_KEY_R:
                    ui->restart_sample();
                    ui->sample()->p_debugDraw = &(g_draw.m_debugDraw);

                    break;

                case GLFW_KEY_O:
                    ui->settings().singleStep = true;
                    break;

                case GLFW_KEY_P:
                    ui->settings().pause = !ui->settings().pause;
                    break;

                case GLFW_KEY_TAB:
                    g_draw.m_showUI = !g_draw.m_showUI;

                default:
                    if (ui->sample())
                    {
                        ui->sample()->Keyboard(key);
                    }
            }
        }
    }

    static void CharCallback(GLFWwindow* window, unsigned int c)
    {
        ImGui_ImplGlfw_CharCallback(window, c);
    }

    static void MouseButtonCallback(GLFWwindow* window, int32_t button, int32_t action, int32_t mods)
    {
        auto ui = static_cast<OpenGlFrontend*>(glfwGetWindowUserPointer(window));
        auto sample = ui->sample();
        ImGui_ImplGlfw_MouseButtonCallback(window, button, action, mods);

        if (ImGui::GetIO().WantCaptureMouse)
        {
            return;
        }

        double xd, yd;
        glfwGetCursorPos(window, &xd, &yd);
        b2Vec2 ps = {float(xd) / ui->window_scale, float(yd) / ui->window_scale};

        // Use the mouse to move things around.
        if (button == GLFW_MOUSE_BUTTON_1)
        {
            b2Vec2 pw = g_camera.ConvertScreenToWorld(ps);
            if (action == GLFW_PRESS)
            {
                sample->MouseDown(pw, button, mods);
            }

            if (action == GLFW_RELEASE)
            {
                sample->MouseUp(pw, button);
            }
        }
        else if (button == GLFW_MOUSE_BUTTON_2)
        {
            if (action == GLFW_PRESS)
            {
                ui->s_click_point_ws = g_camera.ConvertScreenToWorld(ps);
                ui->right_mouse_down = true;
            }

            if (action == GLFW_RELEASE)
            {
                ui->right_mouse_down = false;
            }
        }
    }

    static void MouseMotionCallback(GLFWwindow* window, double xd, double yd)
    {
        auto ui = static_cast<OpenGlFrontend*>(glfwGetWindowUserPointer(window));
        auto sample = ui->sample();
        b2Vec2 ps = {float(xd) / ui->window_scale, float(yd) / ui->window_scale};

        ImGui_ImplGlfw_CursorPosCallback(window, ps.x, ps.y);

        b2Vec2 pw = g_camera.ConvertScreenToWorld(ps);
        sample->MouseMove(pw);

        if (ui->right_mouse_down)
        {
            b2Vec2 diff = b2Sub(pw, ui->s_click_point_ws);
            g_camera.m_center.x -= diff.x;
            g_camera.m_center.y -= diff.y;
            ui->s_click_point_ws = g_camera.ConvertScreenToWorld(ps);
        }
    }

    static void ScrollCallback(GLFWwindow* window, double dx, double dy)
    {
        ImGui_ImplGlfw_ScrollCallback(window, dx, dy);
        if (ImGui::GetIO().WantCaptureMouse)
        {
            return;
        }

        if (dy > 0)
        {
            g_camera.m_zoom /= 1.1f;
        }
        else
        {
            g_camera.m_zoom *= 1.1f;
        }
    }

    static void UpdateUI(OpenGlFrontend* ui)
    {
        int maxWorkers = enki::GetNumHardwareThreads();
        auto sample = ui->sample();
        auto& settings = ui->settings();
        auto main_window = ui->main_window();

        float menuWidth = 180.0f;
        if (g_draw.m_showUI)
        {
            ImGui::SetNextWindowPos({g_camera.m_width - menuWidth - 10.0f, 10.0f});
            ImGui::SetNextWindowSize({menuWidth, g_camera.m_height - 20.0f});

            ImGui::Begin(
                "Tools",
                &g_draw.m_showUI,
                ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoCollapse
            );

            if (ImGui::BeginTabBar("ControlTabs", ImGuiTabBarFlags_None))
            {
                if (ImGui::BeginTabItem("Controls"))
                {
                    ImGui::PushItemWidth(100.0f);
                    ImGui::SliderInt("Sub-steps", &settings.subStepCount, 1, 50);
                    ImGui::SliderFloat("Hertz", &settings.hertz, 5.0f, 120.0f, "%.0f hz");

                    if (ImGui::SliderInt("Workers", &settings.workerCount, 1, maxWorkers))
                    {
                        settings.workerCount = b2ClampInt(settings.workerCount, 1, maxWorkers);
                        ui->restart_sample();
                        ui->sample()->p_debugDraw = &(g_draw.m_debugDraw);
                        sample = ui->sample();
                    }
                    ImGui::PopItemWidth();

                    ImGui::Separator();

                    ImGui::Checkbox("Sleep", &settings.enableSleep);
                    ImGui::Checkbox("Warm Starting", &settings.enableWarmStarting);
                    ImGui::Checkbox("Continuous", &settings.enableContinuous);

                    ImGui::Separator();

                    ImGui::Checkbox("Shapes", &settings.drawShapes);
                    ImGui::Checkbox("Joints", &settings.drawJoints);
                    ImGui::Checkbox("Joint Extras", &settings.drawJointExtras);
                    ImGui::Checkbox("AABBs", &settings.drawAABBs);
                    ImGui::Checkbox("Contact Points", &settings.drawContactPoints);
                    ImGui::Checkbox("Contact Normals", &settings.drawContactNormals);
                    ImGui::Checkbox("Contact Impulses", &settings.drawContactImpulses);
                    ImGui::Checkbox("Friction Impulses", &settings.drawFrictionImpulses);
                    ImGui::Checkbox("Center of Masses", &settings.drawMass);
                    ImGui::Checkbox("Graph Colors", &settings.drawGraphColors);

                    ImVec2 button_sz = ImVec2(-1, 0);
                    if (ImGui::Button("Pause (P)", button_sz))
                    {
                        settings.pause = !settings.pause;
                    }

                    if (ImGui::Button("Single Step (O)", button_sz))
                    {
                        settings.singleStep = !settings.singleStep;
                    }

                    if (ImGui::Button("Restart (R)", button_sz))
                    {
                        ui->restart_sample();
                        ui->sample()->p_debugDraw = &(g_draw.m_debugDraw);
                        sample = ui->sample();
                    }

                    if (ImGui::Button("Quit", button_sz))
                    {
                        glfwSetWindowShouldClose(main_window, GL_TRUE);
                    }

                    ImGui::EndTabItem();
                }

                ImGuiTreeNodeFlags leafNodeFlags = ImGuiTreeNodeFlags_OpenOnArrow
                                                   | ImGuiTreeNodeFlags_OpenOnDoubleClick;
                leafNodeFlags |= ImGuiTreeNodeFlags_Leaf | ImGuiTreeNodeFlags_NoTreePushOnOpen;

                ImGuiTreeNodeFlags nodeFlags = ImGuiTreeNodeFlags_OpenOnArrow
                                               | ImGuiTreeNodeFlags_OpenOnDoubleClick;

                ImGui::EndTabBar();
            }

            ImGui::End();

            sample->UpdateUI();
        }
    }

    int start_everything(const char* data_dir, nanobind::object sample_cls)
    {
        Settings settings;
        settings.data_dir = data_dir;

        nanobind::object py_instance;

        // // Install memory hooks
        b2SetAllocator(AllocFcn, FreeFcn);

        char buffer[128];

        settings.workerCount = b2MinInt(8, (int) enki::GetNumHardwareThreads() / 2);

        g_camera.m_width = settings.windowWidth;
        g_camera.m_height = settings.windowHeight;

        OpenGlFrontend ui(sample_cls, settings);
        auto ui_address = &ui;

        auto main_window = ui.main_window();

        glfwSetWindowSizeCallback(main_window, ResizeWindowCallback);
        glfwSetKeyCallback(main_window, KeyCallback);
        glfwSetCharCallback(main_window, CharCallback);
        glfwSetMouseButtonCallback(main_window, MouseButtonCallback);
        glfwSetCursorPosCallback(main_window, MouseMotionCallback);
        glfwSetScrollCallback(main_window, ScrollCallback);

        g_draw.Create(data_dir);

        glClearColor(0.2f, 0.2f, 0.2f, 1.0f);

        float frameTime = 0.0;

        int32_t frame = 0;

        g_camera.m_zoom = 20.0f;
        while (!glfwWindowShouldClose(main_window))
        {
            double time1 = glfwGetTime();

            if (glfwGetKey(main_window, GLFW_KEY_Z) == GLFW_PRESS)
            {
                // Zoom out
                g_camera.m_zoom = b2MinFloat(1.005f * g_camera.m_zoom, 100.0f);
            }
            else if (glfwGetKey(main_window, GLFW_KEY_X) == GLFW_PRESS)
            {
                // Zoom in
                g_camera.m_zoom = b2MaxFloat(0.995f * g_camera.m_zoom, 0.5f);
            }

            glfwGetWindowSize(main_window, &g_camera.m_width, &g_camera.m_height);
            g_camera.m_width = int(g_camera.m_width / ui.window_scale);
            g_camera.m_height = int(g_camera.m_height / ui.window_scale);

            int bufferWidth, bufferHeight;
            glfwGetFramebufferSize(main_window, &bufferWidth, &bufferHeight);
            glViewport(0, 0, bufferWidth, bufferHeight);

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

            g_draw.DrawBackground();

            double cursorPosX = 0, cursorPosY = 0;
            glfwGetCursorPos(main_window, &cursorPosX, &cursorPosY);
            ImGui_ImplGlfw_CursorPosCallback(
                main_window,
                cursorPosX / ui.window_scale,
                cursorPosY / ui.window_scale
            );
            ImGui_ImplOpenGL3_NewFrame();
            ImGui_ImplGlfw_NewFrame();
            ImGui_ImplGlfw_CursorPosCallback(
                main_window,
                cursorPosX / ui.window_scale,
                cursorPosY / ui.window_scale
            );
            ImGuiIO& io = ImGui::GetIO();
            io.DisplaySize.x = float(g_camera.m_width);
            io.DisplaySize.y = float(g_camera.m_height);
            io.DisplayFramebufferScale.x = bufferWidth / float(g_camera.m_width);
            io.DisplayFramebufferScale.y = bufferHeight / float(g_camera.m_height);
            ImGui::NewFrame();
            ImGui::SetNextWindowPos(ImVec2(0.0f, 0.0f));
            ImGui::SetNextWindowSize(ImVec2(float(g_camera.m_width), float(g_camera.m_height)));
            ImGui::SetNextWindowBgAlpha(0.0f);
            ImGui::Begin(
                "Overlay",
                nullptr,
                ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoInputs | ImGuiWindowFlags_AlwaysAutoResize
                    | ImGuiWindowFlags_NoScrollbar
            );
            ImGui::End();
            if (ui.sample() == nullptr)
            {
                ui.restart_sample();
                ui.sample()->p_debugDraw = &(g_draw.m_debugDraw);
            }

            ui.sample()->p_debugDraw->drawingBounds = g_camera.GetViewBounds();
            ui.sample()->Step(ui.settings());
            g_draw.Flush();

            UpdateUI(ui_address);

            if (g_draw.m_showUI)
            {
                snprintf(
                    buffer,
                    128,
                    "%.1f ms - step %d - camera (%g, %g, %g)",
                    1000.0f * frameTime,
                    ui.sample()->m_stepCount,
                    g_camera.m_center.x,
                    g_camera.m_center.y,
                    g_camera.m_zoom
                );
                // snprintf( buffer, 128, "%.1f ms", 1000.0f * frameTime );

                ImGui::Begin(
                    "Overlay",
                    nullptr,
                    ImGuiWindowFlags_NoTitleBar | ImGuiWindowFlags_NoInputs
                        | ImGuiWindowFlags_AlwaysAutoResize | ImGuiWindowFlags_NoScrollbar
                );
                ImGui::SetCursorPos(ImVec2(5.0f, g_camera.m_height - 20.0f));
                ImGui::TextColored(ImColor(153, 230, 153, 255), "%s", buffer);
                ImGui::End();
            }


            ImGui::Render();
            ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());

            glfwSwapBuffers(main_window);

            glfwPollEvents();

            // Limit frame rate to 60Hz
            double time2 = glfwGetTime();
            double targetTime = time1 + 1.0f / 60.0f;
            int loopCount = 0;
            while (time2 < targetTime)
            {
                b2Yield();
                time2 = glfwGetTime();
                ++loopCount;
            }

            frameTime = (float) (time2 - time1);
            ++frame;
        }

        g_draw.Destroy();

#if defined(_WIN32)
        _CrtDumpMemoryLeaks();
#endif

        return 0;
    }

}  // namespace pyb2d
