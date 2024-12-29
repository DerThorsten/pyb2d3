
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import triangulate
import shapely
import matplotlib.pyplot as plt
from skimage.measure import find_contours
from skimage.measure import find_contours
import math

from ._pyb2d import compute_hull, make_polygon, make_offset_polygon
from .compound_shape import CompoundShape


def triangulate_within(polygon):
    return [triangle for triangle in triangulate(polygon) if triangle.within(polygon)]





class PolygonFontAlphabet(object):
    def __init__(self, font, font_path=None, debug=False):
        self.font = font
        self.font_path = font_path
        self.debug = debug
        self.font_size = 200
        self.font = ImageFont.truetype(self.font_path, self.font_size)

        self.img_size = (512, 512)

        # all chars
        self.chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        # self.chars = "H"
        # build the chars themself
        self.char_to_triangles = {}
        for char in self.chars:
            self._init_char(char)

        # normalize all triangles
        self._normalize()

        # to box2d shapes
        self._char_to_box2d_shapes = {}
        self._to_box2d_shapes()

       

    def _is_hole(self, contour, binary_image):
        # check if contour is a hole
        x, y = contour[0]
        print("contour[0]: ", contour[0])
        # return binary_image[x, y] == 0

    def _init_char(self, char):
        image = Image.new('L', self.img_size, 0)

        draw = ImageDraw.Draw(image)

        mid = self.img_size[0] // 2 - self.font_size//2 , self.img_size[1] // 2 - self.font_size//2
        draw.text(mid, char, fill=255, font=self.font)

        # Convert image to array
        img_array = np.array(image)
        binary_image = img_array > 0

        # marching squares to get contours
        contours = find_contours(binary_image, level=0.5)



        polygons = [Polygon(contour) for contour in contours]
        is_hole  = [False] * len(polygons)
        is_hole_of = [None] * len(polygons)
        
        # check for each polyon if its inside any other polygon
        for i, poly in enumerate(polygons):
            for j, other_poly in enumerate(polygons):
                if i == j:
                    continue
                if poly.within(other_poly):
                    is_hole[i] = True
                    is_hole_of[i] = j

        cleaned = [None] * len(polygons)

        # pass 1 add all non holes
        for i, poly in enumerate(polygons):
            if not is_hole[i]:
                cleaned[i] = [contours[i], []]
        # pass 2 add all holes to their parent
        for i, poly in enumerate(polygons):
            if is_hole[i]:
                cleaned[is_hole_of[i]][1].append(contours[i])
        # remove holes
        cleaned = [c for c in cleaned if c is not None]



        triangulated_all = []
        for contour, holes in cleaned:
            # swap x and y 
            polygon = Polygon(contour, holes=holes)
            polygon_simple = shapely.simplify(polygon, tolerance=0, preserve_topology=True)
            triangulated = triangulate_within(polygon_simple)
            for triangle in triangulated:
                arr = np.array(triangle.exterior.xy)
                arr = arr.T
                arr = np.require(arr, requirements=['C'])
                triangulated_all.append(arr)
        self.char_to_triangles[char] = triangulated_all


        if self.debug:
            print(f"char: {char}, # of triangles: {len(triangulated_all)} #contours: {len(contours)}")
            # plot triangulated
            fig, ax = plt.subplots()
            ax.imshow(img_array)
            for triangle in triangulated_all:
                print(triangle.shape)
                ax.plot(triangle[:,0], triangle[:,1], linewidth=1)
            plt.show()



        
    def _normalize(self):
        min_x = np.inf
        min_y = np.inf
        max_x = -np.inf
        max_y = -np.inf

        for char in self.chars:
            for triangle in self.char_to_triangles[char]:
                min_x = min(min_x, np.min(triangle[:,0]))
                min_y = min(min_y, np.min(triangle[:,1]))
                max_x = max(max_x, np.max(triangle[:,0]))
                max_y = max(max_y, np.max(triangle[:,1]))

        self.max_width = max_x - min_x
        self.max_height = max_y - min_y

        for char in self.chars:
            for triangle in self.char_to_triangles[char]:
                triangle[:,0] -= min_x
                triangle[:,1] -= min_y

                triangle[:] /= self.max_width
                triangle[:] *= 10.0

    
    def _to_box2d_shapes(self):
        for char in self.chars:
            box_shapes = []
            for triangle in self.char_to_triangles[char]:
                hull = compute_hull(triangle)
                polygon = make_offset_polygon(hull, (0,0), -math.pi/2)
                box_shapes.append(polygon)
            self._char_to_box2d_shapes[char] = box_shapes


class LetterShape(CompoundShape):
    def __init__(self, polygon_font, char, position=(0,0), angle=0):
        super(LetterShape, self).__init__()
        self.polygon_font = polygon_font
        self.char = char
        self.position = position
        self.angle = angle
        
        shapes = self.polygon_font._char_to_box2d_shapes[self.char]
  

        for shape in shapes:
            self.add_shape(shape)