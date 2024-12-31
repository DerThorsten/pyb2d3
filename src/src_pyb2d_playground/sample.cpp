// SPDX-FileCopyrightText: 2023 Erin Catto
// SPDX-License-Identifier: MIT

// #include "draw.h"
#include <iostream>

#include <GLFW/glfw3.h>
#include <sample.h>
#include <settings.h>
#include <stdio.h>
#include <string.h>

#include "box2d/box2d.h"
#include "box2d/math_functions.h"

namespace pyb2d
{


    static void*
    EnqueueTask(b2TaskCallback* task, int32_t itemCount, int32_t minRange, void* taskContext, void* userContext)
    {
        // std::cout<<"EnqueueTask"<<std::endl;
        Sample* sample = static_cast<Sample*>(userContext);
        if (sample->m_taskCount < maxTasks)
        {
            SampleTask& sampleTask = sample->m_tasks[sample->m_taskCount];
            sampleTask.m_SetSize = itemCount;
            sampleTask.m_MinRange = minRange;
            sampleTask.m_task = task;
            sampleTask.m_taskContext = taskContext;
            sample->m_scheduler.AddTaskSetToPipe(&sampleTask);
            ++sample->m_taskCount;
            return &sampleTask;
        }
        else
        {
            std::cout << "Max tasks reached" << std::endl;
            // This is not fatal but the maxTasks should be increased
            assert(false);
            task(0, itemCount, 0, taskContext);
            return nullptr;
        }
        // std::cout<<"EnqueueTask done"<<std::endl;
    }

    static void FinishTask(void* taskPtr, void* userContext)
    {
        if (taskPtr != nullptr)
        {
            SampleTask* sampleTask = static_cast<SampleTask*>(taskPtr);
            Sample* sample = static_cast<Sample*>(userContext);
            sample->m_scheduler.WaitforTask(sampleTask);
        }
    }

    Sample::Sample(Settings& settings)
    {
        m_scheduler.Initialize(settings.workerCount);
        m_taskCount = 0;

        m_threadCount = 1 + settings.workerCount;

        b2WorldDef worldDef = b2DefaultWorldDef();
        worldDef.workerCount = settings.workerCount;
        worldDef.enqueueTask = EnqueueTask;
        worldDef.finishTask = FinishTask;
        worldDef.userTaskContext = this;
        worldDef.enableSleep = settings.enableSleep;

        m_worldId = b2CreateWorld(&worldDef);
        m_textLine = 30;
        m_textIncrement = 18;
        m_mouseJointId = b2_nullJointId;

        m_stepCount = 0;

        m_groundBodyId = b2_nullBodyId;
    }

    Sample::~Sample()
    {
        // By deleting the world, we delete the bomb, mouse joint, etc.
        b2DestroyWorld(m_worldId);
    }

    struct QueryContext
    {
        b2Vec2 point;
        b2BodyId bodyId = b2_nullBodyId;
    };

    bool QueryCallback(b2ShapeId shapeId, void* context)
    {
        QueryContext* queryContext = static_cast<QueryContext*>(context);

        b2BodyId bodyId = b2Shape_GetBody(shapeId);
        b2BodyType bodyType = b2Body_GetType(bodyId);
        if (bodyType != b2_dynamicBody)
        {
            // continue query
            return true;
        }

        bool overlap = b2Shape_TestPoint(shapeId, queryContext->point);
        if (overlap)
        {
            // found shape
            queryContext->bodyId = bodyId;
            return false;
        }

        return true;
    }

    void Sample::MouseDown(b2Vec2 p, int button, int mod)
    {
        if (B2_IS_NON_NULL(m_mouseJointId))
        {
            return;
        }

        if (button == GLFW_MOUSE_BUTTON_1)
        {
            // Make a small box.
            b2AABB box;
            b2Vec2 d = {0.001f, 0.001f};
            box.lowerBound = b2Sub(p, d);
            box.upperBound = b2Add(p, d);

            // Query the world for overlapping shapes.
            QueryContext queryContext = {p, b2_nullBodyId};
            b2World_OverlapAABB(m_worldId, box, b2DefaultQueryFilter(), QueryCallback, &queryContext);

            if (B2_IS_NON_NULL(queryContext.bodyId))
            {
                b2BodyDef bodyDef = b2DefaultBodyDef();
                m_groundBodyId = b2CreateBody(m_worldId, &bodyDef);

                b2MouseJointDef mouseDef = b2DefaultMouseJointDef();
                mouseDef.bodyIdA = m_groundBodyId;
                mouseDef.bodyIdB = queryContext.bodyId;
                mouseDef.target = p;
                mouseDef.hertz = 5.0f;
                mouseDef.dampingRatio = 0.7f;
                mouseDef.maxForce = 1000.0f * b2Body_GetMass(queryContext.bodyId);
                m_mouseJointId = b2CreateMouseJoint(m_worldId, &mouseDef);

                b2Body_SetAwake(queryContext.bodyId, true);
            }
        }
    }

    void Sample::MouseUp(b2Vec2 p, int button)
    {
        if (b2Joint_IsValid(m_mouseJointId) == false)
        {
            // The world or attached body was destroyed.
            m_mouseJointId = b2_nullJointId;
        }

        if (B2_IS_NON_NULL(m_mouseJointId) && button == GLFW_MOUSE_BUTTON_1)
        {
            b2DestroyJoint(m_mouseJointId);
            m_mouseJointId = b2_nullJointId;

            b2DestroyBody(m_groundBodyId);
            m_groundBodyId = b2_nullBodyId;
        }
    }

    void Sample::MouseMove(b2Vec2 p)
    {
        if (b2Joint_IsValid(m_mouseJointId) == false)
        {
            // The world or attached body was destroyed.
            m_mouseJointId = b2_nullJointId;
        }

        if (B2_IS_NON_NULL(m_mouseJointId))
        {
            b2MouseJoint_SetTarget(m_mouseJointId, p);
            b2BodyId bodyIdB = b2Joint_GetBodyB(m_mouseJointId);
            b2Body_SetAwake(bodyIdB, true);
        }
    }

    void Sample::Step(Settings& settings)
    {
        float timeStep = settings.hertz > 0.0f ? 1.0f / settings.hertz : 0.0f;

        if (settings.pause)
        {
            if (settings.singleStep)
            {
                settings.singleStep = false;
            }
            else
            {
                timeStep = 0.0f;
            }

            // if (g_draw.m_showUI)
            // {
            // 	g_draw.DrawString( 5, m_textLine, "****PAUSED****" );
            // 	m_textLine += m_textIncrement;
            // }
        }

        //
        p_debugDraw->useDrawingBounds = settings.useCameraBounds;
        p_debugDraw->drawShapes = settings.drawShapes;
        p_debugDraw->drawJoints = settings.drawJoints;
        p_debugDraw->drawJointExtras = settings.drawJointExtras;
        p_debugDraw->drawAABBs = settings.drawAABBs;
        p_debugDraw->drawMass = settings.drawMass;
        p_debugDraw->drawContacts = settings.drawContactPoints;
        p_debugDraw->drawGraphColors = settings.drawGraphColors;
        p_debugDraw->drawContactNormals = settings.drawContactNormals;
        p_debugDraw->drawContactImpulses = settings.drawContactImpulses;
        p_debugDraw->drawFrictionImpulses = settings.drawFrictionImpulses;

        b2World_EnableSleeping(m_worldId, settings.enableSleep);
        b2World_EnableWarmStarting(m_worldId, settings.enableWarmStarting);
        b2World_EnableContinuous(m_worldId, settings.enableContinuous);

        for (int i = 0; i < 1; ++i)
        {
            b2World_Step(m_worldId, timeStep, settings.subStepCount);
            m_taskCount = 0;
        }

        b2World_Draw(m_worldId, p_debugDraw);

        if (timeStep > 0.0f)
        {
            ++m_stepCount;
        }
    }

    void Sample::ShiftOrigin(b2Vec2 newOrigin)
    {
        // m_world->ShiftOrigin(newOrigin);
    }

}
