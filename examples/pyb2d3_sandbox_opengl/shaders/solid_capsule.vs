// SPDX-FileCopyrightText: 2024 Erin Catto
// SPDX-License-Identifier: MIT

#version 330

uniform mat4 projectionMatrix;
uniform float pixelScale;

layout(location=0) in vec2 v_localPosition;
layout(location=1) in vec4 v_instanceTransform;
layout(location=2) in float v_instanceRadius;
layout(location=3) in float v_instanceLength;
layout(location=4) in vec4 v_instanceColor;

out vec2 f_position;
out vec4 f_color;
out float f_length;
out float f_thickness;
out float f_coarse;

void main()
{
    f_position = v_localPosition;
    f_color = v_instanceColor;

    float radius = v_instanceRadius;
    float length = v_instanceLength;

    // scale quad large enough to hold capsule
    float scale = radius + 0.5 * length;

    // quad range of [-1, 1] implies normalize radius and length
    f_length = length / scale;

    // resolution.y = pixelScale * scale; the border: 3 pixels, but at most a quarter of
    // the radius and 0.09 (the quad reaches 1.1: a wider border would be cut off square);
    // coarse (0..1): how much smaller than that the shape is on screen (zoomed out, small
    // shapes become solid instead of all border)
    float pixels = 3.0f / (pixelScale * scale);
    float cap = min(0.25f * radius / scale, 0.09f);
    f_thickness = min(pixels, cap);
    f_coarse = clamp(pixels / cap - 1.0f, 0.0f, 1.0f);

    float x = v_instanceTransform.x;
    float y = v_instanceTransform.y;
    float c = v_instanceTransform.z;
    float s = v_instanceTransform.w;
    vec2 p = vec2(scale * v_localPosition.x, scale * v_localPosition.y);
    p = vec2((c * p.x - s * p.y) + x, (s * p.x + c * p.y) + y);
    gl_Position = projectionMatrix * vec4(p, 0.0, 1.0);
}
