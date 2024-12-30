from .compound_shape import CompoundShape
from ._pyb2d import make_offset_box


class OpenBoxShape(CompoundShape):
    def __init__(self, dimensions, wall_thickness):
        super(OpenBoxShape, self).__init__()
        self.dimensions = dimensions
        self.wall_thickness = wall_thickness

        shape = self.dimensions
        self.add_shape(make_offset_box(shape[0] / 2, wall_thickness / 2, (0, 0), 0))
        self.add_shape(
            make_offset_box(
                wall_thickness / 2, shape[1] / 2, (-shape[0] / 2, shape[1] / 2), 0
            )
        )
        self.add_shape(
            make_offset_box(
                wall_thickness / 2, shape[1] / 2, (shape[0] / 2, shape[1] / 2), 0
            )
        )
