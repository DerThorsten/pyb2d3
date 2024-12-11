#include <nanobind/nanobind.h>
#include <nanobind/trampoline.h>
#include <nanobind/stl/string.h>
#include <iostream>

namespace py = nanobind;

#include <pyb2d_playground/settings.h>
#include "sample.h"
#include "draw.h"

#include "py_sample_base.hpp"

#include <imgui.h>
#include <pyb2d/py_converter.hpp>


// C
extern "C" {
#include <box2d/math_functions.h>
#include <box2d/types.h>
}




namespace pyb2d
{

int start_everything(const char * data_dir);


void export_settings(py::module_ & m)
{
    py::class_<Settings>(m, "Settings")
        .def_rw("drawShapes", &Settings::drawShapes)
    ;
}

void export_draw(py::module_ &m)
{
    py::class_<Draw>(m,"Draw")
        .def("draw_polygon", [](
            Draw &d, ArrayVec2 value, int c
        ) {

            b2HexColor color = b2HexColor(c);

            b2Vec2* vertices = reinterpret_cast<b2Vec2*>(value.data());

            d.DrawPolygon(vertices, value.shape(0), color);
        })
    ;

    
}

void export_core(py::module_ &m)
{


    py::class_<Sample, PySampleTrampoline>(m,"Sample")
        .def(py::init<Settings &>())
        .def("step", &Sample::Step)
        .def("update_ui", &Sample::UpdateUI)
        .def("keyboard", &Sample::Keyboard)
        .def("mouse_down", &Sample::MouseDown)
        .def("mouse_up", &Sample::MouseUp)
        .def("mouse_move", &Sample::MouseMove)

        .def_ro("world_id", &Sample::m_worldId)
        .def_ro("step_count", &Sample::m_stepCount)
        .def_ro("thread_count", &Sample::m_threadCount)
        .def_ro("task_count", &Sample::m_taskCount)
        .def("get_draw", [](Sample &s) {
            return g_draw;
        }, py::rv_policy::reference_internal)
    ;


    m.def("start_everything", [](const char * data_dir) {
        try {
            return start_everything(data_dir);
        } catch (const std::exception &e) {
            std::cout << "Error: " << e.what() << std::endl;
            
            for( int i = 0; i < g_sampleCount; ++i )
            {
                g_sampleEntries[i].py_instance.dec_ref();
                g_sampleEntries[i].py_factory.dec_ref();
            }
            throw std::runtime_error(e.what());
        }
    });

    m.def("register_sample",[](
        
        py::object py_factory, 
        std::string category, 
        std::string name
    ){ 
        SampleEntry entry;
        entry.category = category.c_str();
        entry.name = name.c_str();

        entry.py_factory = py_factory;


        int index = g_sampleCount;

        entry.createFcn = [index](Settings& settings) {
            SampleEntry& entry = g_sampleEntries[index];
            entry.py_instance = entry.py_factory(settings);
            Sample* sample = py::cast<Sample*>(entry.py_instance);
            return sample;
        };

        if (index < MAX_SAMPLES)
        {
            g_sampleEntries[index] = std::move(entry);
            ++g_sampleCount;
        }
    });
}

} // namespace pyb2d

NB_MODULE(_pyb2d_samples, m) {

    pyb2d::export_settings(m);   
    pyb2d::export_core(m);
    pyb2d::export_draw(m);
}