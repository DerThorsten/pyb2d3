import bb2d as b2d
import bb2d_samples
import random


from PIL import Image, ImageDraw, ImageFont
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import triangulate

def text_to_box2d_shapes(text, font_path, font_size, box2d_world, position=(0, 0)):
    # Render text to an image
    font = ImageFont.truetype(font_path, font_size)
    img_size = (512, 128)  # Adjust size as needed
    image = Image.new('L', img_size, 0)
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), text, fill=255, font=font)
    
    # Convert image to array
    img_array = np.array(image)
    contours = np.argwhere(img_array > 0)  # Get white pixel coordinates
    
    # Create polygons (convex decomposition for Box2D)
    poly = Polygon(contours)
    if not poly.is_valid:
        poly = poly.buffer(0)  # Fix invalid polygons
    shapes = triangulate(poly)  # Break into convex pieces

    # Add to Box2D world
    for shape in shapes:
        vertices = [(x + position[0], y + position[1]) for x, y in shape.exterior.coords[:-1]]
        box2d_shape = Box2D.b2PolygonShape(vertices=vertices)
        body = box2d_world.CreateStaticBody(position=position, shapes=box2d_shape)
    
    return shapes





class MySample(bb2d_samples.Sample):
    def __init__(self, settings):
        super(MySample, self).__init__(settings)

        # self.world_id = self.get_world_id()
        world_id = self.world_id

        body_def = b2d.body_def(position=(0, 20), type=b2d.BodyType.STATIC)
        groud_body_id= b2d.create_body(world_id, body_def) 
        box = b2d.make_box(100, 1)
        shape_def = b2d.shape_def(density=0, friction=0.3, restitution=0.5, user_data=100)
        shape_id = b2d.create_polygon_shape(groud_body_id, shape_def, box)

        for i in range(1000):
            body_def = b2d.body_def(position=(i%10 + random.random()*10, 30 + random.random() * 10), type=b2d.BodyType.DYNAMIC, angular_damping=0.01, linear_damping=0.01)
            dynamic_body_id = b2d.create_body(world_id, body_def)
            circle = b2d.circle(radius=0.1)
            shape_def = b2d.shape_def(density=1, friction=0.3, restitution=0.9)
            shape_id = b2d.create_circle_shape(dynamic_body_id, shape_def, circle)



    
    def step(self, settings):
        super(MySample, self).step(settings)


bb2d_samples.register_sample(MySample,"MySample", "MySample description")

bb2d_samples.start_everything()