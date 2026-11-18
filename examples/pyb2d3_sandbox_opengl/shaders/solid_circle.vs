// SPDX-FileCopyrightText: 2024 Erin Catto
// SPDX-License-Identifier: MIT

#version 330

uniform mat4 projectionMatrix;
uniform float pixelScale;

layout(location = 0) in vec2 v_localPosition;
layout(location = 1) in vec4 v_instanceTransform;
layout(location = 2) in float v_instanceRadius;
layout(location = 3) in vec4 v_instanceColor;

out vec2 f_position;
out vec4 f_color;
out float f_thickness;
out float f_coarse;

void main()
{
    f_position = v_localPosition;
    f_color = v_instanceColor;
    float radius = v_instanceRadius;

    // resolution.y = pixelScale * radius; the border: 3 pixels, but at most 0.09 (the quad
    // reaches 1.1: a wider border would be cut off square); coarse: see solid_capsule.vs
    float pixels = 3.0f / (pixelScale * radius);
    f_thickness = min(pixels, 0.09f);
    f_coarse = clamp(pixels / 0.09f - 1.0f, 0.0f, 1.0f);

    float x = v_instanceTransform.x;
    float y = v_instanceTransform.y;
    float c = v_instanceTransform.z;
    float s = v_instanceTransform.w;
    vec2 p = vec2(radius * v_localPosition.x, radius * v_localPosition.y);
    p = vec2((c * p.x - s * p.y) + x, (s * p.x + c * p.y) + y);
    gl_Position = projectionMatrix * vec4(p, 0.0f, 1.0f);
}
