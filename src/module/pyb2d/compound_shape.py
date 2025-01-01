class CompoundShape:
    def __init__(self):
        self.shapes = []

    def add_shape(self, shape, shape_def=None):
        self.shapes.append((shape, shape_def))
