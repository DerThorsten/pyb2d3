#pragma once

#include <stdexcept>
#include <string>

#include <box2d/box2d.h>

// Owning wrappers around box2d's opaque recording / replay pointers.
// The pointer member is called `id` (like the handle types) so that the generic
// pyb2d3::Binder can bind `b2Replay_*` / `b2Recording_*` functions directly.

struct PyRecording
{
    explicit PyRecording(int byte_capacity = 0)
        : id(b2CreateRecording(byte_capacity))
    {
    }

    explicit PyRecording(b2Recording* p)
        : id(p)
    {
        if (!id)
        {
            throw std::runtime_error("could not create recording");
        }
    }

    static PyRecording* from_file(const std::string& path)
    {
        return new PyRecording(b2CreateRecordingFromFile(path.c_str()));
    }

    PyRecording(const PyRecording&) = delete;
    PyRecording& operator=(const PyRecording&) = delete;

    ~PyRecording()
    {
        if (id)
        {
            b2DestroyRecording(id);
        }
    }

    b2Recording* id = nullptr;
};

struct PyReplay
{
    PyReplay(const void* data, int size, int worker_count)
        : id(b2CreateReplay(data, size, worker_count))
    {
        if (!id)
        {
            throw std::runtime_error("malformed recording");
        }
    }

    PyReplay(const PyReplay&) = delete;
    PyReplay& operator=(const PyReplay&) = delete;

    ~PyReplay()
    {
        if (id)
        {
            b2DestroyReplay(id);
        }
    }

    b2Replay* id = nullptr;
};
