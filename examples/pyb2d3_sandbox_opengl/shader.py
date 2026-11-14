# this code is a modified version of  https://github.com/giorgosg/box2d-py/blob/main/src/box2d_testbed/shader.py
# The code has been adapted to work with the pyb2d3 library and its frontend system.
# The original code is licensed under the MIT License with the following copyright:
#
# MIT License
# Copyright 2025 Giorgos Giagas
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”),
# to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from OpenGL.GL import *  # noqa: F403


def dump_gl_info():
    """Print OpenGL driver information."""
    print("-------------------------------------------------------------")
    print(f"GL Vendor    : {glGetString(GL_VENDOR).decode()}")
    print(f"GL Renderer  : {glGetString(GL_RENDERER).decode()}")
    print(f"GL Version   : {glGetString(GL_VERSION).decode()}")
    major = GLint()
    minor = GLint()
    glGetIntegerv(GL_MAJOR_VERSION, major)
    glGetIntegerv(GL_MINOR_VERSION, minor)
    print(f"GL Version   : {major.value}.{minor.value}")
    print(f"GLSL Version : {glGetString(GL_SHADING_LANGUAGE_VERSION).decode()}")
    print("-------------------------------------------------------------")


def check_gl_error():
    """Check for OpenGL errors."""
    err = glGetError()
    if err != GL_NO_ERROR:
        print(f"OpenGL error = {err}")
        assert False


def print_gl_log(obj):
    """Print shader or program info log."""
    if glIsShader(obj):
        length = GLint()
        glGetShaderiv(obj, GL_INFO_LOG_LENGTH, length)
        log = glGetShaderInfoLog(obj).decode()
    elif glIsProgram(obj):
        length = GLint()
        glGetProgramiv(obj, GL_INFO_LOG_LENGTH, length)
        log = glGetProgramInfoLog(obj).decode()
    else:
        print("PrintLogGL: Not a shader or a program")
        return

    if log:
        print(f"PrintLogGL: {log}")


def _create_shader_from_string(source, shader_type):
    """Create a shader from source string."""
    try:
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)

        # Check compilation status
        status = GLint()
        glGetShaderiv(shader, GL_COMPILE_STATUS, status)

        if status.value == GL_FALSE:
            print(f"Error compiling shader of type {shader_type}!")
            print_gl_log(shader)
            glDeleteShader(shader)
            return 0

        return shader
    except Exception as e:
        print(f"Error creating shader: {e}")
        return 0


def create_program_from_strings(vertex_string, fragment_string):
    """Create a shader program from vertex and fragment shader strings."""
    vertex = _create_shader_from_string(vertex_string, GL_VERTEX_SHADER)
    if vertex == 0:
        return 0

    fragment = _create_shader_from_string(fragment_string, GL_FRAGMENT_SHADER)
    if fragment == 0:
        return 0

    program = glCreateProgram()
    glAttachShader(program, vertex)
    glAttachShader(program, fragment)
    glLinkProgram(program)

    # Check link status
    status = GLint()
    glGetProgramiv(program, GL_LINK_STATUS, status)
    if status.value == GL_FALSE:
        print("glLinkProgram:")
        print_gl_log(program)
        return 0

    glDeleteShader(vertex)
    glDeleteShader(fragment)

    return program


def create_program_from_files(vertex_path, fragment_path):
    """Create a shader program from vertex and fragment shader files."""
    try:
        with open(vertex_path, "r") as f:
            vertex_source = f.read()

        with open(fragment_path, "r") as f:
            fragment_source = f.read()

        return create_program_from_strings(vertex_source, fragment_source)

    except Exception as e:
        print(f"Error reading shader files: {e}")
        return 0
