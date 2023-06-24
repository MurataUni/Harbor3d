from dataclasses import dataclass, field

import os
import struct

import numpy as np

from .ship import Ship
from .util import display_util

from typing import List

@dataclass
class Dock:
    ships:List[Ship] = field(default_factory=list)

    def clear(self):
        self.ships = []

    def generate_ship(self):
        ship = Ship()

        self.ships.append(ship)
        ship.init_keel()
        return ship

    def get_child_ship(self, parent_ship):
        childs = []
        for ship in self.ships:
            if ship.parent is parent_ship:
                childs.append(ship)
        return childs

    def rotate_keel(self, ship, y_axis_rotate=0., z_axis_rotate=0.):
        ship.keel.rotation(y_axis_rotate, z_axis_rotate)
        self.make_translation_dirty_recursively(ship)
    
    def resize_keel(self, ship, keel_length):
        ship.keel.length = keel_length
        self.make_translation_dirty_recursively(ship)
    
    def set_parent(self, ship ,parent, position=1.):
        ship.set_parent(parent, position)
        self.make_parents_dirty_recursively(ship)
        self.make_translation_dirty_recursively(ship)

    def set_parents_position(self, ship, position=1.):
        ship.set_parent(ship.parent, position)
        self.make_translation_dirty_recursively(ship)

    def make_parents_dirty_recursively(self, ship):
        for target_ship in self.ships:
            for parent in target_ship.parents:
                if ship is parent:
                    target_ship.parents_dirty_flag = True

    def make_translation_dirty_recursively(self, ship):
        for target_ship in self.ships:
            for parent in target_ship.parents:
                if ship is parent:
                    target_ship.translation_dirty_flag = True

    def sanitize_dock(self, force=False):
        for target_ship in reversed(self.ships):
            if force or target_ship.parents_dirty_flag:
                target_ship.get_parents()
        self.ships.sort(key=lambda ship: len(ship.parents))

        for target_ship in self.ships:
            if target_ship.parent != None and (force or target_ship.translation_dirty_flag):
                target_ship.sanitize_keel()
        
        for target_ship in self.ships:
            if 0 != len(target_ship.subtracts):
                target_ship.apply_subtructions()

    def start_display(self):
        self.sanitize_dock()

        translate_vel, translate_matlix = self.generate_translate_vel_and_matrix()
        display_util.start_display(self, translate_vel, translate_matlix)
    
    def generate_translate_vel_and_matrix(self):
        jack_up_ratio = 2.

        object_areas = self.get_object_areas()
        max_area_length = object_areas[0]-object_areas[1]
        if (max_area_length < object_areas[2]-object_areas[3]):
            max_area_length = object_areas[2]-object_areas[3]
        if (max_area_length < object_areas[4]-object_areas[5]):
            max_area_length = object_areas[4]-object_areas[5]
        x = -(object_areas[0]+object_areas[1])/2
        y = -(object_areas[2]+object_areas[3])/2
        z = -((object_areas[4]+object_areas[5])/2 + max_area_length * jack_up_ratio)
        translate_matlix = np.array([\
            [1., 0., 0., 0.],\
            [0., 1., 0., 0.],\
            [0., 0., 1., 0.],\
            [x, y, z, 1.]])
        return max_area_length/20, translate_matlix

    def get_object_areas(self):
        right_max = 0.
        left_max = 0.
        top_max = 0.
        bottom_max = 0.
        front_max = 0.
        back_max = 0.
        for target_ship in self.ships:
            keel_translation = target_ship.keel.translation(1.)
            if (keel_translation[3][0] < 0.):
                if keel_translation[3][0] < left_max:
                    left_max = keel_translation[3][0]
            else:
                if keel_translation[3][0] > right_max:
                    right_max = keel_translation[3][0]

            if (keel_translation[3][1] < 0.):
                if keel_translation[3][1] < bottom_max:
                    bottom_max = keel_translation[3][1]
            else:
                if keel_translation[3][1] > top_max:
                    top_max = keel_translation[3][1]
            
            if (keel_translation[3][2] < 0.):
                if keel_translation[3][2] < back_max:
                    back_max = keel_translation[3][2]
            else:
                if keel_translation[3][2] > front_max:
                    front_max = keel_translation[3][2]
            
        return (right_max, left_max, top_max, bottom_max, front_max, back_max)

    def write_stl(self, f):
        self.sanitize_dock()
        if self.ships is None or len(self.ships) == 0:
            return
        for ship in self.ships:
            ship.write_stl(f)
    
    def count_triangles(self):
        count = 0
        self.sanitize_dock()
        for ship in self.ships:
            if not ship.is_monocoque():
                ship.convert_to_monocoque()
            if ship.is_monocoque():
                count += len(ship.monocoque_shell.triangles)
        return count
    
    def write_stl_binary(self, f):
        # already sanitized and converted to monocoque in method: count_triangles
        for ship in self.ships:
            ship.write_stl_binary(f)
    
    def write_stl_binary_divided(self, dir_full_name):
        divided_stl_files_count = 0
        for ship in self.ships:
            if not ship.is_monocoque():
                ship.convert_to_monocoque()
            if ship.is_monocoque():
                fname = format(divided_stl_files_count, '0>6') + ".stl"
                if ship.has_name():
                    fname = ship.name + ".stl"
                file_full_name = os.path.join(dir_full_name, fname)
                f = open(file_full_name, "wb")
                # 80Byte padding
                for i in range(8):
                    f.write(struct.pack("xxxxxxxxxx"))
                
                # count triangles
                count = len(ship.monocoque_shell.triangles)
                f.write(struct.pack("<L", count))

                ship.write_stl_binary(f)
                f.close()
                divided_stl_files_count += 1