#include <nanobind/nanobind.h>
#include <nanobind/trampoline.h>

#include <iostream>

namespace py = nanobind;

#include "settings.h"
#include "sample.h"
#include "py_sample_base.hpp"

int start_everything();





void export_settings(py::module_ & m)
{
    py::class_<Settings>(m, "Settings")
        .def_rw("drawShapes", &Settings::drawShapes)
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
    ;



    m.def("start_everything", &start_everything);

    m.def("register_sample",[](py::object py_factory, const char* category, const char* name) {
        SampleEntry entry;
        entry.category = category;
        entry.name = name;


        entry.createFcn = [py_factory](Settings& settings) {
            std::cout<<"py_factory"<<std::endl;
            py::object py_instance = py_factory(settings);
            
            // increment reference count
            py_instance.inc_ref();

            std::cout<<"py cast"<<std::endl;
            Sample* sample = py::cast<Sample*>(std::move(py_instance));
            return sample;
        };
        //return RegisterSample(entry);
        int index = g_sampleCount;
        std::cout<<"index: "<<index<<std::endl;
        if (index < MAX_SAMPLES)
        {
            std::cout<<"adding entry"<<std::endl;
            g_sampleEntries[index] = entry;
            ++g_sampleCount;
        }
    });
}

NB_MODULE(_bb2d_samples, m) {
    export_settings(m);   
    export_core(m);
}