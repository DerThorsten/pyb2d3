import pyb2d as b2d
from pyb2d.extra_shapes import OpenBoxShape
import pyb2d_samples
import random


class MySample(pyb2d_samples.Sample):
    def __init__(self, settings, radius=0.1):
        super(MySample, self).__init__(settings)

        # make a open box
        box_dimensions= [10,10]
        wall_thickness = 0.1

        box_body_id = b2d.create_static_body(self.world_id, position=(0, 0))

        box_shape = OpenBoxShape(box_dimensions, wall_thickness)
        shape_def = b2d.shape_def(friction=0.3)
        b2d.create_shape(box_body_id, shape_def, box_shape)
        

        for i in range(1000):
            rx = random.uniform(-box_dimensions[0]/2, box_dimensions[0]/2)
            ry = random.uniform(-box_dimensions[1]/2, box_dimensions[1]/2) + box_dimensions[1]*5
            position = (rx, ry) 
            dynamic_body_id = b2d.create_dynamic_body(self.world_id, position=position, 
                angular_damping=0.01, linear_damping=0.01)

            b2d.create_shape(dynamic_body_id, 
                b2d.shape_def(density=1, friction=0.3, restitution=0.9), 
                b2d.circle(radius=radius)
            )

pyb2d_samples.run_sample(MySample)