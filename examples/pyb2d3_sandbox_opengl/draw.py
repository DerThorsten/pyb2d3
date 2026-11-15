# this code is a modified version of  https://github.com/giorgosg/box2d-py/blob/main/src/box2d_testbed/draw.py
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


import numpy as np
from OpenGL.GL import *  # noqa: F403
import array
import math
import os
from pyb2d3 import Vec2, ensure_hex_color
from .shader import create_program_from_files, create_program_from_strings, IS_GLES
import ctypes

# (PyOpenGL's error checking is switched off in this package's __init__: it has to
# happen before the first OpenGL.GL import, setting it here is too late)


def make_rgba8(hex_color, alpha=255):
    """Convert hex color to RGBA8 in little-endian order (RGBA in memory)."""
    r = (hex_color >> 16) & 0xFF
    g = (hex_color >> 8) & 0xFF
    b = hex_color & 0xFF
    return (alpha << 24) | (b << 16) | (g << 8) | r


_RGBA8 = {}  # color -> make_rgba8 value: a frame has few distinct colors


def rgba8(color):
    """a color (0xRRGGBB int, HexColor member, (r, g, b)) as packed RGBA8, cached
    (it is converted once per shape and frame)"""
    try:
        return _RGBA8[color]
    except KeyError:
        if len(_RGBA8) > 65536:  # e.g. a sample with a new color per frame
            _RGBA8.clear()
        value = _RGBA8[color] = make_rgba8(ensure_hex_color(color))
        return value
    except TypeError:  # unhashable, e.g. an [r, g, b] list
        return make_rgba8(ensure_hex_color(color))


class Instances:
    """this frame's instances of one shape type: tuples appended by the add_* methods
    (a sample's own drawing, the python debug draw path) and blocks from a
    b2d.BatchDebugDraw (float32 (n, k) arrays with the same memory layout as `dtype`)"""

    def __init__(self, dtype):
        self.dtype = dtype
        self.tuples = []
        self.blocks = []

    def append(self, record):
        """one instance as a tuple in the field order of `dtype`"""
        self.tuples.append(record)

    def add_block(self, block):
        """instances collected in C++ (BatchDebugDraw), same layout as `dtype`;
        keeps the drawing order (what was added before stays below it)"""
        if len(block):
            self._flush()
            self.blocks.append(
                np.ascontiguousarray(block, dtype=np.float32).view(self.dtype).reshape(-1)
            )

    def _flush(self):
        """the tuples added so far as a block (keeps them in front of later blocks)"""
        if self.tuples:
            self.blocks.append(np.array(self.tuples, dtype=self.dtype))
            self.tuples.clear()

    def __bool__(self):
        return bool(self.tuples) or bool(self.blocks)

    def array(self):
        """all instances in drawing order as one `dtype` array (no copy for a single block)"""
        self._flush()
        return self.blocks[0] if len(self.blocks) == 1 else np.concatenate(self.blocks)

    def clear(self):
        self.tuples.clear()
        self.blocks.clear()


def upload_vertices(vbo_id, data, capacity):
    """upload `data` (bytes as a uint8 array) into the buffer `vbo_id`; the buffer
    only grows (doubling) and is filled with glBufferSubData: reallocating it every
    frame (glBufferData) is a GPU-CPU sync point. Returns the new capacity in bytes."""
    glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
    if data.nbytes > capacity:
        capacity = max(data.nbytes, 2 * capacity, 4096)
        glBufferData(GL_ARRAY_BUFFER, capacity, None, GL_DYNAMIC_DRAW)
    glBufferSubData(GL_ARRAY_BUFFER, 0, data.nbytes, data)
    return capacity


def upload_instances(instances, batch_size):
    """upload a structured instance array into the bound instance buffer and draw
    it, `batch_size` instances (the buffer's capacity) at a time"""
    for base in range(0, len(instances), batch_size):
        batch = instances[base : base + batch_size]
        glBufferSubData(GL_ARRAY_BUFFER, 0, batch.nbytes, batch)
        glDrawArraysInstanced(GL_TRIANGLES, 0, 6, len(batch))


class GLBackground:
    def __init__(self, camera):
        """Initialize OpenGL resources for background rendering"""
        self.camera = camera  # Store camera reference
        self.vao_id = None
        self.vbo_id = None
        self.program_id = None
        self.time_uniform = None
        self.resolution_uniform = None
        self.base_color_uniform = None

        # Get the directory containing this file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Create shader paths relative to this file
        vertex_shader = os.path.join(current_dir, "shaders", "background.vs")
        fragment_shader = os.path.join(current_dir, "shaders", "background.fs")

        # Create and compile shaders
        self.program_id = create_program_from_files(vertex_shader, fragment_shader)

        # Get uniform locations
        self.time_uniform = glGetUniformLocation(self.program_id, "time")
        self.resolution_uniform = glGetUniformLocation(self.program_id, "resolution")
        self.base_color_uniform = glGetUniformLocation(self.program_id, "baseColor")

        # Generate vertex array and buffer
        self.vao_id = glGenVertexArrays(1)
        self.vbo_id = glGenBuffers(1)

        # Setup vertex attributes
        glBindVertexArray(self.vao_id)
        vertex_attribute = 0
        glEnableVertexAttribArray(vertex_attribute)

        # Define vertices using Vec2
        vertices = [
            Vec2(-1.0, 1.0),  # Top left
            Vec2(-1.0, -1.0),  # Bottom left
            Vec2(1.0, 1.0),  # Top right
            Vec2(1.0, -1.0),  # Bottom right
        ]

        # Convert Vec2 list to flat numpy array
        vertex_data = np.array([(v[0], v[1]) for v in vertices], dtype=np.float32).flatten()

        # Upload vertex data
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_id)
        glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)
        glVertexAttribPointer(vertex_attribute, 2, GL_FLOAT, GL_FALSE, 0, None)

        # Cleanup
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def destroy(self):
        """Clean up OpenGL resources"""
        if self.vao_id:
            glDeleteVertexArrays(1, [self.vao_id])
            glDeleteBuffers(1, [self.vbo_id])
            self.vao_id = None
            self.vbo_id = None

        if self.program_id:
            glDeleteProgram(self.program_id)
            self.program_id = None

    # True: a plain clear in the base color instead of the full-screen noise shader.
    # The noise is static and barely visible (intensity 0.01), but costs a shader
    # run per pixel, every frame: a lot of fill rate on phones / tablets (millions of
    # pixels). Only for a frontend that owns the whole framebuffer (glClear ignores
    # the viewport), e.g. the browser canvas, not the imgui window of the desktop one.
    use_clear = False
    base_color = (0.2, 0.2, 0.2)

    def draw(self):
        """Draw the background"""
        if self.use_clear:
            glClearColor(*self.base_color, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
            return
        glUseProgram(self.program_id)

        # # Update uniforms
        # import glfw

        # time = glfw.get_time() % 100.0

        glUniform1f(self.time_uniform, 0)
        # Use camera instance for resolution
        glUniform2f(self.resolution_uniform, float(self.camera.width), float(self.camera.height))
        glUniform3f(self.base_color_uniform, *self.base_color)  # Gray background

        # Draw quad
        glBindVertexArray(self.vao_id)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_id)
        glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        # (no reset of the GL state after each draw: GLDebugDraw.end_draw resets it
        # once per frame; every GL call costs, especially python -> wasm -> JS)


# Instance layouts of the shapes (one record per shape, uploaded as they are). The
# add_* methods append plain tuples, draw() turns them into one array per frame:
# no numpy object per shape (that dominated the frame time with many bodies).
# Colors are RGBA8 packed into a uint32 (make_rgba8: r in the lowest byte).
CIRCLE_DTYPE = np.dtype(
    [("x", np.float32), ("y", np.float32), ("radius", np.float32), ("color", np.uint32)]
)
SOLID_CIRCLE_DTYPE = np.dtype(
    [
        ("x", np.float32),
        ("y", np.float32),
        ("c", np.float32),
        ("s", np.float32),
        ("radius", np.float32),
        ("color", np.uint32),
    ]
)
CAPSULE_DTYPE = np.dtype(
    [
        ("x", np.float32),
        ("y", np.float32),
        ("axis_x", np.float32),
        ("axis_y", np.float32),
        ("radius", np.float32),
        ("length", np.float32),
        ("color", np.uint32),
    ]
)
POINT_DTYPE = np.dtype(
    [("x", np.float32), ("y", np.float32), ("size", np.float32), ("color", np.uint32)]
)
LINE_VERTEX_DTYPE = np.dtype([("x", np.float32), ("y", np.float32), ("color", np.uint32)])
_NO_POINTS = (0.0,) * 16  # padding of the 8 polygon vertices


class GLCircles:
    def __init__(self, camera):
        self.camera = camera
        self.vao_id = None
        self.vbo_ids = [None, None]  # Need two buffers: vertices and instance data
        self.program_id = None
        self.projection_uniform = None
        self.pixel_scale_uniform = None
        self.circles = Instances(CIRCLE_DTYPE)

        # Get the directory containing this file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Create shader paths relative to this file
        vertex_shader = os.path.join(current_dir, "shaders", "circle.vs")
        fragment_shader = os.path.join(current_dir, "shaders", "circle.fs")

        self.program_id = create_program_from_files(vertex_shader, fragment_shader)
        self.projection_uniform = glGetUniformLocation(self.program_id, "projectionMatrix")
        self.pixel_scale_uniform = glGetUniformLocation(self.program_id, "pixelScale")

        # Generate vertex array and buffers
        self.vao_id = glGenVertexArrays(1)
        self.vbo_ids = glGenBuffers(2)

        # Setup vertex attributes
        glBindVertexArray(self.vao_id)

        # Attribute locations
        vertex_attribute = 0
        position_instance = 1
        radius_instance = 2
        color_instance = 3

        glEnableVertexAttribArray(vertex_attribute)
        glEnableVertexAttribArray(position_instance)
        glEnableVertexAttribArray(radius_instance)
        glEnableVertexAttribArray(color_instance)

        # Vertex buffer for single quad
        a = 1.1
        vertices = np.array(
            [
                -a,
                -a,  # Bottom left
                a,
                -a,  # Bottom right
                -a,
                a,  # Top left
                a,
                -a,  # Bottom right
                a,
                a,  # Top right
                -a,
                a,  # Top left
            ],
            dtype=np.float32,
        )

        # Upload quad vertices
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ids[0])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(vertex_attribute, 2, GL_FLOAT, GL_FALSE, 0, None)

        # Circle instance buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ids[1])
        glBufferData(
            GL_ARRAY_BUFFER, self.BATCH_SIZE * 16, None, GL_DYNAMIC_DRAW
        )  # 16 bytes per instance

        # Setup instance attributes
        stride = 16  # 4 floats * 4 bytes
        offset = 0
        glVertexAttribPointer(
            position_instance, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 8  # 2 floats * 4 bytes
        glVertexAttribPointer(
            radius_instance, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 4  # 1 float * 4 bytes
        glVertexAttribPointer(
            color_instance,
            4,
            GL_UNSIGNED_BYTE,
            GL_TRUE,
            stride,
            ctypes.c_void_p(offset),
        )

        # Set attribute divisors for instancing
        glVertexAttribDivisor(position_instance, 1)
        glVertexAttribDivisor(radius_instance, 1)
        glVertexAttribDivisor(color_instance, 1)

        # Cleanup
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def destroy(self):
        """Clean up OpenGL resources"""
        if self.vao_id:
            glDeleteVertexArrays(1, [self.vao_id])
            glDeleteBuffers(2, self.vbo_ids)
            self.vao_id = None
            self.vbo_ids = [None, None]

        if self.program_id:
            glDeleteProgram(self.program_id)
            self.program_id = None

    def add_circle(self, center, radius, color):
        """Add circle for batch rendering"""
        self.circles.append((center[0], center[1], radius, rgba8(color)))

    def draw(self):
        """Render all circles in batch"""
        if not self.circles:
            return

        glUseProgram(self.program_id)

        # Update uniforms
        proj_matrix = self.camera.build_projection_matrix(0.2)
        glUniformMatrix4fv(self.projection_uniform, 1, GL_FALSE, proj_matrix)
        glUniform1f(self.pixel_scale_uniform, self.camera.height / self.camera.zoom)

        glBindVertexArray(self.vao_id)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ids[1])

        upload_instances(self.circles.array(), self.BATCH_SIZE)

        self.circles.clear()

    BATCH_SIZE = 2048  # Maximum number of circles per batch


class GLSolidCircles:
    def __init__(self, camera):
        self.camera = camera
        self.vao_id = None
        self.vbo_ids = [None, None]  # Need two buffers: vertices and instance data
        self.program_id = None
        self.projection_uniform = None
        self.pixel_scale_uniform = None
        self.circles = Instances(SOLID_CIRCLE_DTYPE)

        # Get the directory containing this file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Create shader paths relative to this file
        vertex_shader = os.path.join(current_dir, "shaders", "solid_circle.vs")
        fragment_shader = os.path.join(current_dir, "shaders", "solid_circle.fs")

        self.program_id = create_program_from_files(vertex_shader, fragment_shader)
        self.projection_uniform = glGetUniformLocation(self.program_id, "projectionMatrix")
        self.pixel_scale_uniform = glGetUniformLocation(self.program_id, "pixelScale")

        # Generate vertex array and buffers
        self.vao_id = glGenVertexArrays(1)
        self.vbo_ids = glGenBuffers(2)

        # Setup vertex attributes
        glBindVertexArray(self.vao_id)

        # Attribute locations
        vertex_attribute = 0
        transform_instance = 1
        radius_instance = 2
        color_instance = 3

        glEnableVertexAttribArray(vertex_attribute)
        glEnableVertexAttribArray(transform_instance)
        glEnableVertexAttribArray(radius_instance)
        glEnableVertexAttribArray(color_instance)

        # Vertex buffer for single quad
        a = 1.1
        vertices = np.array(
            [
                -a,
                -a,  # Bottom left
                a,
                -a,  # Bottom right
                -a,
                a,  # Top left
                a,
                -a,  # Bottom right
                a,
                a,  # Top right
                -a,
                a,  # Top left
            ],
            dtype=np.float32,
        )

        # Upload quad vertices
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ids[0])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(vertex_attribute, 2, GL_FLOAT, GL_FALSE, 0, None)

        # Circle instance buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ids[1])
        glBufferData(
            GL_ARRAY_BUFFER, self.BATCH_SIZE * 24, None, GL_DYNAMIC_DRAW
        )  # 24 bytes per instance

        # Setup instance attributes
        stride = 24  # 6 floats * 4 bytes
        offset = 0
        glVertexAttribPointer(
            transform_instance, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 16  # 4 floats * 4 bytes
        glVertexAttribPointer(
            radius_instance, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 4  # 1 float * 4 bytes
        glVertexAttribPointer(
            color_instance,
            4,
            GL_UNSIGNED_BYTE,
            GL_TRUE,
            stride,
            ctypes.c_void_p(offset),
        )

        # Set attribute divisors for instancing
        glVertexAttribDivisor(transform_instance, 1)
        glVertexAttribDivisor(radius_instance, 1)
        glVertexAttribDivisor(color_instance, 1)

        # Cleanup
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def destroy(self):
        """Clean up OpenGL resources"""
        if self.vao_id:
            glDeleteVertexArrays(1, [self.vao_id])
            glDeleteBuffers(2, self.vbo_ids)
            self.vao_id = None
            self.vbo_ids = [None, None]

        if self.program_id:
            glDeleteProgram(self.program_id)
            self.program_id = None

    def add_circle(self, transform, radius, color):
        """Add solid circle for batch rendering"""
        p, q = transform.p, transform.q
        self.circles.append((p[0], p[1], q.c, q.s, radius, rgba8(color)))

    def draw(self):
        """Render all solid circles in batch"""
        if not self.circles:
            return

        glUseProgram(self.program_id)

        # Update uniforms
        proj_matrix = self.camera.build_projection_matrix(0.2)
        glUniformMatrix4fv(self.projection_uniform, 1, GL_FALSE, proj_matrix)
        glUniform1f(self.pixel_scale_uniform, self.camera.height / self.camera.zoom)

        glBindVertexArray(self.vao_id)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ids[1])

        upload_instances(self.circles.array(), self.BATCH_SIZE)

        self.circles.clear()

    BATCH_SIZE = 2048  # Maximum number of circles per batch


class GLSolidCapsules:
    def __init__(self, camera):
        self.camera = camera
        self.vao_id = None
        self.vbo_ids = [None, None]
        self.program_id = None
        self.projection_uniform = None
        self.pixel_scale_uniform = None
        self.capsules = Instances(CAPSULE_DTYPE)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        vertex_shader = os.path.join(current_dir, "shaders", "solid_capsule.vs")
        fragment_shader = os.path.join(current_dir, "shaders", "solid_capsule.fs")

        self.program_id = create_program_from_files(vertex_shader, fragment_shader)
        self.projection_uniform = glGetUniformLocation(self.program_id, "projectionMatrix")
        self.pixel_scale_uniform = glGetUniformLocation(self.program_id, "pixelScale")

        self.vao_id = glGenVertexArrays(1)
        self.vbo_ids = glGenBuffers(2)

        glBindVertexArray(self.vao_id)

        vertex_attribute = 0
        transform_instance = 1
        radius_instance = 2
        length_instance = 3
        color_instance = 4

        glEnableVertexAttribArray(vertex_attribute)
        glEnableVertexAttribArray(transform_instance)
        glEnableVertexAttribArray(radius_instance)
        glEnableVertexAttribArray(length_instance)
        glEnableVertexAttribArray(color_instance)

        # Vertex buffer for single quad
        a = 1.1
        vertices = np.array(
            [
                -a,
                -a,  # Bottom left
                a,
                -a,  # Bottom right
                -a,
                a,  # Top left
                a,
                -a,  # Bottom right
                a,
                a,  # Top right
                -a,
                a,  # Top left
            ],
            dtype=np.float32,
        )

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ids[0])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(vertex_attribute, 2, GL_FLOAT, GL_FALSE, 0, None)

        # Capsule instance buffer
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ids[1])
        glBufferData(
            GL_ARRAY_BUFFER, self.BATCH_SIZE * 28, None, GL_DYNAMIC_DRAW
        )  # 28 bytes per instance

        # Setup instance attributes
        stride = 28  # 7 floats * 4 bytes
        offset = 0
        glVertexAttribPointer(
            transform_instance, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 16  # 4 floats * 4 bytes
        glVertexAttribPointer(
            radius_instance, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 4  # 1 float * 4 bytes
        glVertexAttribPointer(
            length_instance, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 4  # 1 float * 4 bytes
        glVertexAttribPointer(
            color_instance,
            4,
            GL_UNSIGNED_BYTE,
            GL_TRUE,
            stride,
            ctypes.c_void_p(offset),
        )

        # Set attribute divisors for instancing
        glVertexAttribDivisor(transform_instance, 1)
        glVertexAttribDivisor(radius_instance, 1)
        glVertexAttribDivisor(length_instance, 1)
        glVertexAttribDivisor(color_instance, 1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def destroy(self):
        """Clean up OpenGL resources"""
        if self.vao_id:
            glDeleteVertexArrays(1, [self.vao_id])
            glDeleteBuffers(2, self.vbo_ids)
            self.vao_id = None
            self.vbo_ids = [None, None]

        if self.program_id:
            glDeleteProgram(self.program_id)
            self.program_id = None

    def add_capsule(self, p1, p2, radius, color):
        """Add capsule for batch rendering (center, axis, radius, length)"""
        x1, y1, x2, y2 = p1[0], p1[1], p2[0], p2[1]
        dx, dy = x2 - x1, y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        if length < 0.001:
            print("WARNING: sample app: capsule too short!")
            return
        self.capsules.append(
            (
                0.5 * (x1 + x2),
                0.5 * (y1 + y2),
                dx / length,
                dy / length,
                radius,
                length,
                rgba8(color),
            )
        )

    def draw(self):
        """Render all capsules in batch"""
        if not self.capsules:
            return

        glUseProgram(self.program_id)

        # Update uniforms
        proj_matrix = self.camera.build_projection_matrix(0.2)
        glUniformMatrix4fv(self.projection_uniform, 1, GL_FALSE, proj_matrix)
        glUniform1f(self.pixel_scale_uniform, self.camera.height / self.camera.zoom)

        glBindVertexArray(self.vao_id)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ids[1])

        upload_instances(self.capsules.array(), self.BATCH_SIZE)

        self.capsules.clear()

    BATCH_SIZE = 2048  # Maximum number of capsules per batch


# Define a structured dtype for the instance data.
# Total size = 4*4 (transform) + 16*4 (points) + 4 (count) + 4 (radius) + 4 (color) = 92 bytes.
polygon_dtype = np.dtype(
    [
        ("transform", np.float32, 4),  # transform: p[0], p[1], q.c, q.s
        ("points", np.float32, 16),  # 8 points * 2 components each
        ("count", np.int32),  # integer count
        ("radius", np.float32),
        ("color", np.uint32),
    ]
)


class GLSolidPolygons:
    BATCH_SIZE = 512  # Maximum number of polygons per batch

    def __init__(self, camera):
        self.camera = camera
        # this frame's polygons as flat C arrays (array.array takes python floats at C
        # speed and numpy reads its buffer without a copy; converting nested tuples /
        # python lists to polygon_dtype is several times slower)
        self.floats = array.array("f")  # per polygon 21: transform (4), points (16), radius
        self.counts = array.array("i")
        self.colors = array.array("I")
        self.blocks = []  # from BatchDebugDraw (add_block)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        vertex_shader = os.path.join(current_dir, "shaders", "solid_polygon.vs")
        fragment_shader = os.path.join(current_dir, "shaders", "solid_polygon.fs")

        self.program_id = create_program_from_files(vertex_shader, fragment_shader)
        self.projection_uniform = glGetUniformLocation(self.program_id, "projectionMatrix")
        self.pixel_scale_uniform = glGetUniformLocation(self.program_id, "pixelScale")

        self.vao_id = glGenVertexArrays(1)
        self.vbo_ids = glGenBuffers(2)

        glBindVertexArray(self.vao_id)
        vertex_attribute = 0
        instance_transform = 1
        instance_point12 = 2
        instance_point34 = 3
        instance_point56 = 4
        instance_point78 = 5
        instance_point_count = 6
        instance_radius = 7
        instance_color = 8

        for attr in range(9):
            glEnableVertexAttribArray(attr)

        a = 1.1
        vertices = np.array(
            [
                -a,
                -a,
                a,
                -a,
                -a,
                a,
                a,
                -a,
                a,
                a,
                -a,
                a,
            ],
            dtype=np.float32,
        )
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ids[0])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(vertex_attribute, 2, GL_FLOAT, GL_FALSE, 0, None)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ids[1])
        glBufferData(
            GL_ARRAY_BUFFER,
            self.BATCH_SIZE * polygon_dtype.itemsize,
            None,
            GL_DYNAMIC_DRAW,
        )
        stride = polygon_dtype.itemsize
        offset = 0
        glVertexAttribPointer(
            instance_transform, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 16
        glVertexAttribPointer(
            instance_point12, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 16
        glVertexAttribPointer(
            instance_point34, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 16
        glVertexAttribPointer(
            instance_point56, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 16
        glVertexAttribPointer(
            instance_point78, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 16
        glVertexAttribIPointer(instance_point_count, 1, GL_INT, stride, ctypes.c_void_p(offset))
        offset += 4
        glVertexAttribPointer(
            instance_radius, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset)
        )
        offset += 4
        glVertexAttribPointer(
            instance_color,
            4,
            GL_UNSIGNED_BYTE,
            GL_TRUE,
            stride,
            ctypes.c_void_p(offset),
        )
        for attr in range(1, 9):
            glVertexAttribDivisor(attr, 1)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def add_polygon(self, transform, points, count, radius, color):
        """Pack polygon data into the current instance buffer using the structured dtype.
        Format:
            transform: [p[0], p[1], q.c, q.s]
            points: 8 pairs of (x, y) (fill remaining with 0.0)
            count: integer
            radius: float
            color: uint32 bit pattern
        """
        p, q = transform.p, transform.q
        # (n, 2) local vertices, n <= 8: a numpy array from box2d, any sequence of
        # points from a sample's own drawing code
        if isinstance(points, np.ndarray):
            pts = points.ravel().tolist()
        else:
            pts = [c for point in points for c in (float(point[0]), float(point[1]))]
        floats = self.floats
        floats.extend((p[0], p[1], q.c, q.s))
        floats.extend(pts)
        floats.extend(_NO_POINTS[len(pts) :])
        floats.append(radius)
        self.counts.append(count)
        self.colors.append(rgba8(color))

    def add_block(self, block):
        """polygons collected in C++ (BatchDebugDraw.polygons: float32 (n, 23), the
        polygon_dtype layout); keeps the drawing order"""
        if len(block):
            self._flush()
            self.blocks.append(
                np.ascontiguousarray(block, dtype=np.float32).view(polygon_dtype).reshape(-1)
            )

    def _flush(self):
        """the polygons added in python so far as a polygon_dtype block"""
        if not self.counts:
            return
        f = np.frombuffer(self.floats, dtype=np.float32).reshape(-1, 21)
        added = np.empty(len(f), dtype=polygon_dtype)
        added["transform"] = f[:, :4]
        added["points"] = f[:, 4:20]
        added["radius"] = f[:, 20]
        added["count"] = np.frombuffer(self.counts, dtype=np.int32)
        added["color"] = np.frombuffer(self.colors, dtype=np.uint32)
        self.blocks.append(added)
        del f  # a live view of self.floats would block resizing it (BufferError)
        del self.floats[:]
        del self.counts[:]
        del self.colors[:]

    def instances(self):
        """this frame's polygons in drawing order as a polygon_dtype array"""
        self._flush()
        return self.blocks[0] if len(self.blocks) == 1 else np.concatenate(self.blocks)

    def draw(self):
        """Render all polygons in batch"""
        if not self.counts and not self.blocks:
            return

        glUseProgram(self.program_id)
        proj_matrix = self.camera.build_projection_matrix(0.2)
        glUniformMatrix4fv(self.projection_uniform, 1, GL_FALSE, proj_matrix)
        glUniform1f(self.pixel_scale_uniform, self.camera.height / self.camera.zoom)

        glBindVertexArray(self.vao_id)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_ids[1])

        upload_instances(self.instances(), self.BATCH_SIZE)

        # (array.array has no clear(); deleting the items keeps the allocation)
        self.blocks.clear()
        del self.floats[:]
        del self.counts[:]
        del self.colors[:]


class GLPoints:
    def __init__(self, camera):
        self.camera = camera
        self.points = Instances(POINT_DTYPE)
        vertex_shader = (
            "#version 330\n"
            "uniform mat4 projectionMatrix;\n"
            "layout(location = 0) in vec2 v_position;\n"
            "layout(location = 1) in float v_size;\n"
            "layout(location = 2) in vec4 v_color;\n"
            "out vec4 f_color;\n"
            "void main(void){\n"
            "  f_color = v_color;\n"
            "  gl_Position = projectionMatrix * vec4(v_position, 0.0, 1.0);\n"
            "  gl_PointSize = v_size;\n"
            "}\n"
        )
        fragment_shader = (
            "#version 330\n"
            "in vec4 f_color;\n"
            "out vec4 color;\n"
            "void main(void){\n"
            "  color = f_color;\n"
            "}\n"
        )
        self.program_id = create_program_from_strings(vertex_shader, fragment_shader)
        self.projection_uniform = glGetUniformLocation(self.program_id, "projectionMatrix")
        self.vao_id = glGenVertexArrays(1)
        self.vbo_id = glGenBuffers(1)
        glBindVertexArray(self.vao_id)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_id)
        # Allocate an empty dynamic buffer
        glBufferData(GL_ARRAY_BUFFER, 0, None, GL_DYNAMIC_DRAW)
        self.capacity = 0  # bytes of the vertex buffer (grows, see upload_vertices)
        stride = 2 * 4 + 4 + 4  # 2 floats (8 bytes) + 1 float (4 bytes) + 4 bytes for color
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 1, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 4, GL_UNSIGNED_BYTE, GL_TRUE, stride, ctypes.c_void_p(12))
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def add_point(self, pos, size, color):
        """a point (x, y, size, rgba8) for this frame"""
        self.points.append((pos[0], pos[1], size, rgba8(color)))

    def draw(self):
        if not self.points:
            return
        # rgba8 as a little endian uint32 = the r, g, b, a bytes the shader reads
        points = self.points.array()
        self.capacity = upload_vertices(self.vbo_id, points.view(np.uint8), self.capacity)
        glUseProgram(self.program_id)
        proj = self.camera.build_projection_matrix(0.0)
        glUniformMatrix4fv(self.projection_uniform, 1, GL_FALSE, proj)
        glBindVertexArray(self.vao_id)
        # GLES (WebGL2) always uses gl_PointSize and has no GL_PROGRAM_POINT_SIZE
        if not IS_GLES:
            glEnable(GL_PROGRAM_POINT_SIZE)
        glDrawArrays(GL_POINTS, 0, len(points))
        if not IS_GLES:
            glDisable(GL_PROGRAM_POINT_SIZE)
        self.points.clear()

    def destroy(self):
        if self.vao_id:
            glDeleteVertexArrays(1, [self.vao_id])
            self.vao_id = None
        if self.vbo_id:
            glDeleteBuffers(1, [self.vbo_id])
            self.vbo_id = None
        if self.program_id:
            glDeleteProgram(self.program_id)
            self.program_id = None


class GLLines:
    def __init__(self, camera):
        self.camera = camera
        self.lines = Instances(LINE_VERTEX_DTYPE)  # two vertices per line
        vertex_shader = (
            "#version 330\n"
            "uniform mat4 projectionMatrix;\n"
            "layout(location = 0) in vec2 v_position;\n"
            "layout(location = 1) in vec4 v_color;\n"
            "out vec4 f_color;\n"
            "void main(void){\n"
            "  f_color = v_color;\n"
            "  gl_Position = projectionMatrix * vec4(v_position, 0.0, 1.0);\n"
            "}\n"
        )
        fragment_shader = (
            "#version 330\n"
            "in vec4 f_color;\n"
            "out vec4 color;\n"
            "void main(void){\n"
            "  color = f_color;\n"
            "}\n"
        )
        self.program_id = create_program_from_strings(vertex_shader, fragment_shader)
        self.projection_uniform = glGetUniformLocation(self.program_id, "projectionMatrix")
        self.vao_id = glGenVertexArrays(1)
        self.vbo_id = glGenBuffers(1)
        glBindVertexArray(self.vao_id)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_id)
        glBufferData(GL_ARRAY_BUFFER, 0, None, GL_DYNAMIC_DRAW)
        self.capacity = 0  # bytes of the vertex buffer (grows, see upload_vertices)
        stride = 2 * 4 + 4  # 2 floats (8 bytes) + 4 bytes for color
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 4, GL_UNSIGNED_BYTE, GL_TRUE, stride, ctypes.c_void_p(8))
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def add_line(self, p1, p2, color):
        """a line: two vertices (x, y, rgba8) for this frame"""
        rgba = rgba8(color)
        self.lines.append((p1[0], p1[1], rgba))
        self.lines.append((p2[0], p2[1], rgba))

    def draw(self):
        if not self.lines:
            return
        # rgba8 as a little endian uint32 = the r, g, b, a bytes the shader reads
        vertices = self.lines.array()
        self.capacity = upload_vertices(self.vbo_id, vertices.view(np.uint8), self.capacity)
        glUseProgram(self.program_id)
        proj = self.camera.build_projection_matrix(0.0)
        glUniformMatrix4fv(self.projection_uniform, 1, GL_FALSE, proj)
        glBindVertexArray(self.vao_id)
        glDrawArrays(GL_LINES, 0, len(vertices))
        self.lines.clear()

    def destroy(self):
        if self.vao_id:
            glDeleteVertexArrays(1, [self.vao_id])
            self.vao_id = None
        if self.vbo_id:
            glDeleteBuffers(1, [self.vbo_id])
            self.vbo_id = None
        if self.program_id:
            glDeleteProgram(self.program_id)
            self.program_id = None
