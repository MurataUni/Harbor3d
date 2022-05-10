from dataclasses import dataclass, field

import numpy as np

@dataclass
class Keel():
    
    translation_unit = [\
            [1., 0., 0., 0.],\
            [0., 1., 0., 0.],\
            [0., 0., 1., 0.],\
            [0., 0., 0., 1.]]

    length: float = field(default=1.)
    relative_translation: np.ndarray = field(default=None)
    origin_translation: np.ndarray = field(default=None)

    def __post_init__(self):
        self.relative_translation = np.array(self.translation_unit)
        self.origin_translation = np.array(self.translation_unit)

    def set_length(self, length):
        self.length = length
        self.end = np.array([0., 0., length, 1.])

        return self

    def rotation(self, y_axis_rotate=0., z_axis_rotate=0.):
        y_rotate = np.array([\
            [np.cos(y_axis_rotate), 0., -np.sin(y_axis_rotate), 0.],\
            [0., 1., 0., 0.],\
            [np.sin(y_axis_rotate), 0., np.cos(y_axis_rotate), 0.],\
            [0., 0., 0., 1.]])
        z_rotate = np.array([\
            [np.cos(z_axis_rotate), np.sin(z_axis_rotate), 0., 0.],\
            [-np.sin(z_axis_rotate), np.cos(z_axis_rotate), 0., 0.],\
            [0., 0., 1., 0.],\
            [0., 0., 0., 1.]])

        self.relative_translation = np.dot(y_rotate, z_rotate)

        return self

    def translation(self, position):
        return np.dot(np.dot(self.translation_z(position), self.relative_translation), self.origin_translation)

    def set_start(self, translation):
        self.origin_translation = translation

        return self
    
    def set_position(self, position):
        self.position = position

    def set_edges(self, edges):
        self.edges = edges

    def translation_z(self, position):
        translation_z = [\
                [1., 0., 0., 0.],\
                [0., 1., 0., 0.],\
                [0., 0., 1., 0.],\
                [0., 0., self.length * position, 1.]]
        return np.array(translation_z)

