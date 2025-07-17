from .._pyb2d3 import (
    DebugDrawBase,
    DebugDrawColorFormat,
    TransformDebugDrawBaseHexaColorFormat,
    TransformDebugDrawBaseRgbFloatFormat,
    TransformDebugDrawBaseRgbUInt8Format,
)


class DebugDraw(DebugDrawBase):
    def __init__(self):
        super().__init__(self)

    def draw_polygon(self, vertices, color):
        pass

    def draw_solid_polygon(self, transform, vertices, radius, color):
        pass

    def draw_circle(self, center, radius, color):
        pass

    def draw_solid_circle(self, transform, radius, color):
        pass

    def draw_solid_capsule(self, p1, p2, radius, color):
        pass

    def draw_segment(self, p1, p2, color):
        pass

    def draw_transform(self, transform):
        pass

    def draw_point(self, p, size, color):
        pass

    def draw_string(self, x, y, string):
        pass

    def draw_aabb(self, aabb, color):
        pass


def _make_transform_debug_draw_base(color_format):

    if color_format == DebugDrawColorFormat.HexaColorFormat:
        BaseClass = TransformDebugDrawBaseHexaColorFormat
    elif color_format == DebugDrawColorFormat.RgbFloatFormat:
        BaseClass = TransformDebugDrawBaseRgbFloatFormat
    elif color_format == DebugDrawColorFormat.RgbUInt8Format:
        BaseClass = TransformDebugDrawBaseRgbUInt8Format
    else:
        raise ValueError(f"Unsupported color format {color_format}")

    class TransformDebugDraw(BaseClass):
        def __init__(self, transform):
            super().__init__(transform=transform, py_object=self)

        def draw_polygon(self, vertices, color):
            pass

        def draw_solid_polygon(self, vertices, radius, color):
            pass

        def draw_circle(self, center, radius, color):
            pass

        def draw_solid_circle(self, center, radius, color):
            pass

        def draw_solid_capsule(self, p1, p2, radius, color):
            pass

        def draw_segment(self, p1, p2, color):
            pass

        def draw_transform(self, transform):
            pass

        def draw_point(self, p, size, color):
            pass

        def draw_string(self, x, y, string):
            pass

        def draw_aabb(self, aabb, color):
            pass

    return TransformDebugDraw


TransformDebugDrawHexaColorFormat = _make_transform_debug_draw_base(
    DebugDrawColorFormat.HexaColorFormat
)
TransformDebugDrawRgbFloatFormat = _make_transform_debug_draw_base(
    DebugDrawColorFormat.RgbFloatFormat
)
TransformDebugDrawRgbUInt8Format = _make_transform_debug_draw_base(
    DebugDrawColorFormat.RgbUInt8Format
)
del _make_transform_debug_draw_base
