#pragma once

#include <iostream>

#include <nanobind/nanobind.h>
#include <nanobind/trampoline.h>
#include <settings.h>

#include "sample.h"

namespace pyb2d {

namespace py = nanobind;

struct PySampleTrampoline : Sample {
  NB_TRAMPOLINE(Sample, 6);

  virtual ~PySampleTrampoline() {}

  void Step(Settings &settings) override {
    NB_OVERRIDE_NAME("step", Step, settings);
  }

  void UpdateUI() override { NB_OVERRIDE_NAME("update_ui", UpdateUI); }

  void Keyboard(int k) override { NB_OVERRIDE_NAME("keyboard", Keyboard, k); }

  void MouseDown(b2Vec2 p, int button, int mod) override {
    NB_OVERRIDE_NAME("mouse_down", MouseDown, p, button, mod);
  }

  void MouseUp(b2Vec2 p, int button) override {
    NB_OVERRIDE_NAME("mouse_up", MouseUp, p, button);
  }

  void MouseMove(b2Vec2 p) override {
    NB_OVERRIDE_NAME("mouse_move", MouseMove, p);
  }
};

inline void decrement_reference_count(Sample *s) {
  auto py_object = py::cast(s);
  py_object.dec_ref();
}

} // namespace pyb2d
