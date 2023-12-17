from dataclasses import dataclass, field
import struct
import numpy as np
import os
import shutil

from .ship import Ship
from .dock import Dock
from .specification import Spec

from .util import load_util
from .util.bone_json_util import PostureWrapper, BoneKeys, BoneAxisValue
from .util import edges_util

@dataclass
class Shipwright:
    dock:Dock
    cached_parent:Ship = field(default=None)
    cached_parent_position:float = field(default=1.)
    cached_rotate_y_axis:float = field(default=0.)
    cached_rotate_z_axis:float = field(default=0.)

    def clear_dock(self):
        self.dock.clear()

    def get_dock(self):
        return self.dock
    
    def start_display(self):
        self.dock.start_display()

    def parent(self, ship, position=1.):
        self.cached_parent = ship
        self.cached_parent_position = position
        return self
    
    def rotate(self, rotate_y_axis=0., rotate_z_axis=0.):
        self.cached_rotate_y_axis = rotate_y_axis
        self.cached_rotate_z_axis = rotate_z_axis
        return self

    def set_parent(self, ship, parent, position=1.):
        self.dock.set_parent(ship, parent, position)
    
    def set_cached_parameter(self, ship):
        if self.cached_parent != None:
            self.set_parent(ship, self.cached_parent, self.cached_parent_position)
            self.cached_parent_position = 1.
            self.cached_parent = None
        
        if self.cached_rotate_y_axis != 0. \
            or self.cached_rotate_z_axis != 0.:
            self.dock.rotate_keel(ship, \
                self.cached_rotate_y_axis, self.cached_rotate_z_axis)
            self.cached_rotate_y_axis = 0.
            self.cached_rotate_z_axis = 0.
        
        return ship

    def set_smoothing(self, smoothing, smoothing_from, smoothing_to=None):
        smoothing.set_smoothing(smoothing_from, smoothing_to)
    
    def set_smoothing_to(self, smoothing, smoothing_to):
        smoothing.set_smoothing_to(smoothing_to)
    
    def search_and_load_stl(self, path_list, file_name):
        for path in path_list:
            file = os.path.join(path, file_name)
            if os.path.isfile(file):
                return self.load_stl(file)
        return None

    def load_stl(self, path):
        ship = self.dock.generate_ship()
        ship.load_stl(path)
        return self.set_cached_parameter(ship)
    
    def load_huge_binary_stl(self, path):
        ship = self.dock.generate_ship()
        ship.load_huge_binary_stl(path)
        return self.set_cached_parameter(ship)

    def load_submodule(self, path, force_load_merged_stl=False, vertex_matching=True):
        obj_from_stl = self.dock.generate_ship()
        max_z_position = 0. # z_length_position
        submodule_sehlls = load_util.load_submodule(path, force_load_merged_stl, vertex_matching)
        if 1 == len(submodule_sehlls):
            obj_from_stl.monocoque_shell = submodule_sehlls[0]
            # z_position calc
            for position in obj_from_stl.monocoque_shell.positions:
                if max_z_position < position.position[2]:
                    max_z_position = position.position[2]
        else:
            for shell in submodule_sehlls:
                divided_module = self.dock.generate_ship()
                divided_module.set_parent(obj_from_stl, 0.)
                divided_module.monocoque_shell = shell
                # z_position calc
                for position in divided_module.monocoque_shell.positions:
                    if max_z_position < position.position[2]:
                        max_z_position = position.position[2]
        obj_from_stl.monocoque_shell_max_z_position = max_z_position

        return self.set_cached_parameter(obj_from_stl)
    
    def create_from_spec(self, spec: Spec, only_keel=False):
        if None != self.cached_parent:
            self.parent(self.void())
        if spec.wrap_offset != 0.:
            self.parent(self.move_z_back(spec.wrap_offset))
        if spec.needs_move():
            x,y,z = spec.move_xyz
            if x != 0. and y != 0.:
                self.parent(self.move_xy(x, y))
            elif x != 0.:
                self.parent(self.move_x(x))
            elif y != 0.:
                self.parent(self.move_y(y))
            if z < 0.:
                self.parent(self.move_z_back(z))
            elif z > 0.:
                self.parent(self.void(z))
        if spec.needs_rotation():
            for rotate_y,rotate_z in spec.list_rotation_yz:
                self.parent(self.rotate(rotate_y, rotate_z).void(0))
        ship = None
        if not only_keel:
            if spec.is_rectangle():
                ship = self.rectangular(spec.width(), spec.height(), spec.l)
                rib_root = ship.ribs[0]
                rib_tip = ship.ribs[1]
                if spec.needs_root_end_chamfered():
                    rib_root.position = spec.root_end_coner_length/spec.l
                    ship.add_rib(
                        0., 
                        edges_util.scale_xy(
                            rib_root.edges.copy(),
                            spec.root_end_chamfered_ratio_w(),
                            spec.root_end_chamfered_ratio_h()))
                if spec.needs_tip_end_chamfered():
                    rib_tip.position = 1.- spec.tip_end_coner_length/spec.l
                    ship.add_rib(
                        1., 
                        edges_util.scale_xy(
                            rib_tip.edges.copy(),
                            spec.tip_end_chamfered_ratio_w(),
                            spec.tip_end_chamfered_ratio_h()))
            elif spec.is_pole():
                ship = self.pole(spec.l, spec.radius(), 2*np.pi, spec.divid(), True)
                rib_root = ship.ribs[0]
                rib_tip = ship.ribs[1]
                if spec.needs_root_end_chamfered():
                    rib_root.position = spec.root_end_coner_length/spec.l
                    ship.add_rib(
                        0., 
                        edges_util.scale(
                            rib_root.edges.copy(),
                            spec.root_end_chamfered_ratio_r()))
                if spec.needs_tip_end_chamfered():
                    rib_tip.position = 1.- spec.tip_end_coner_length/spec.l
                    ship.add_rib(
                        1., 
                        edges_util.scale(
                            rib_tip.edges.copy(),
                            spec.tip_end_chamfered_ratio_r()))
            else:
                ship = self.void(spec.l)
            ship.order_ribs()
        else:
            ship = self.void(spec.l)
        return ship

    def void(self, length=0.):
        void = self.dock.generate_ship()
        self.dock.resize_keel(void, length)
        return self.set_cached_parameter(void)
    
    def cube(self, length):
        return self.rectangular(length, length, length)

    def rectangular(self, width, height, depth):
        ship = self.dock.generate_ship()
        ship.add_rib(0, self.rib_edges_rectangular(width, height))
        ship.add_rib(1, self.rib_edges_rectangular(width, height))
        self.dock.resize_keel(ship, depth)
        return self.set_cached_parameter(ship)
    
    def pillar(self, edges, depth):
        ship = self.dock.generate_ship()
        ship.add_rib(0, edges)
        ship.add_rib(1, edges)
        self.dock.resize_keel(ship, depth)
        return self.set_cached_parameter(ship)

    def chamfering(self, ship, length):
        ribs = ship.ribs
        ship.ribs = []
        for rib in ribs:
            new_edges = []
            for index, edge in enumerate(rib.edges):
                edge_current = np.array([edge[0], edge[1]])
                edge_previous = np.array([rib.edges[index - 1][0], rib.edges[index - 1][1]])
                edge_next = np.array([rib.edges[(index + 1) % len(rib.edges)][0], rib.edges[(index + 1) % len(rib.edges)][1]])
                vector_to_previous = edge_previous - edge_current
                vector_to_next = edge_next - edge_current

                if np.linalg.norm(vector_to_previous) < 3 * length:
                    new_edges.append(tuple(edge_current + vector_to_previous/3))
                else:
                    new_edges.append(tuple(edge_current + vector_to_previous * length / np.linalg.norm(vector_to_previous)))

                if np.linalg.norm(vector_to_next) < 3 * length:
                    new_edges.append(tuple(edge_current + vector_to_next/3))
                else:
                    new_edges.append(tuple(edge_current + vector_to_next * length / np.linalg.norm(vector_to_next)))
            ship.add_rib(rib.position, new_edges)

    def rib_edges_rectangular(self, width, height):
        return [(width/2, height/2), (width/2, -height/2), (-width/2, -height/2), (-width/2, height/2)]

    def rib_edges_rectangular_from_edges(self, x_tuple, y_tuple):
        return [(x_tuple[0], y_tuple[0]), (x_tuple[0], y_tuple[1]), (x_tuple[1], y_tuple[1]), (x_tuple[1], y_tuple[0])]
    
    def rib_edges_circular(self, radius, arc_central_angle, division, closed=False):
        division = division if closed else division - 1
        edges = []
        for i in range(division):
            theta = i * arc_central_angle / division
            edges.append((np.cos(theta) * radius, np.sin(theta) * radius))
        if closed:
            edges.append((np.cos(arc_central_angle) * radius, np.sin(arc_central_angle) * radius))
        return edges
    
    def pole(self, depth, radius, arc_central_angle, division, closed=False):
        ship = self.dock.generate_ship()
        rib_edges = self.rib_edges_circular(radius, arc_central_angle, division, closed)
        ship.add_rib(0., rib_edges)
        ship.add_rib(1., rib_edges)
        self.dock.resize_keel(ship, depth)
        return self.set_cached_parameter(ship)
    
    def sphere(self, radius, equatorial_division, step, pole_visibility=False):
        return self.spheroid(radius * 2, radius, equatorial_division, step, pole_visibility)

    def spheroid(self, depth, radius, equatorial_division, step, pole_visibility=False):
        ship = self.dock.generate_ship()
        if pole_visibility:
            ship.add_rib(0., [(0.,0.)])
        for i in range(step+1):
            z_position_ratio = i/step
            if i==0:
                z_position_ratio = 1/(step*4)
            elif i==step:
                z_position_ratio = 1-1/(step*4)
            ship.add_rib(\
                z_position_ratio , \
                self.rib_edges_circular(\
                    radius * np.sqrt(1 - np.square(2.*z_position_ratio-1.)), \
                    2 * np.pi, equatorial_division, True))
        if pole_visibility:
            ship.add_rib(1., [(0.,0.)])
        self.dock.resize_keel(ship, depth)
        return self.set_cached_parameter(ship)

    # todo: 1回転しない場合(半回転など)は未実装
    def spin(self, edges, radius, division):
        base = self.dock.generate_ship()
        self.dock.resize_keel(base, 0.)
        keel_length = 2* radius * np.sin(2. * np.pi / (division * 2) / 2.)

        rims = []
        for i in range(division):
            goto_rim = self.dock.generate_ship()
            self.dock.rotate_keel(goto_rim, np.pi/2, 2. * np.pi *  -i / division)
            self.dock.resize_keel(goto_rim, radius)
            self.dock.set_parent(goto_rim, base)

            rotate_z_axis_joint = self.dock.generate_ship()
            self.dock.rotate_keel(rotate_z_axis_joint, 0., np.pi/2)
            self.dock.resize_keel(rotate_z_axis_joint, 0.)
            self.dock.set_parent(rotate_z_axis_joint, goto_rim)
            
            rim = self.dock.generate_ship()
            rim.add_rib(0., edges)
            rim.add_rib(1., edges)
            self.dock.rotate_keel(rim, -np.pi * (1. + 1 / (division * 2)) / 2., 0.)
            self.dock.resize_keel(rim, keel_length)
            self.dock.set_parent(rim, rotate_z_axis_joint)
            rims.append(rim)
        
        for i in range(len(rims)):
            rim_smoothing = self.dock.generate_ship()
            rim_smoothing.set_smoothing(rims[i])
            self.dock.set_parent(rim_smoothing, rims[i])
            if i == len(rims) - 1:
                rim_smoothing.set_smoothing_to(rims[0])
            else:
                rim_smoothing.set_smoothing_to(rims[i+1])

        return self.set_cached_parameter(base)
    
    def scale(self, scale, target_root=None):
        for ship in self.dock.ships:
            if target_root == None or ship.is_contains_in_parents(target_root):
                ship.keel.length = scale*ship.keel.length
                for rib in ship.ribs:
                    rib.edges = [(e[0]*scale,e[1]*scale) for e in rib.edges]
                if ship.monocoque_shell != None:
                    self.deformation(ship, lambda x,y,z: (x*scale,y*scale,z*scale), False) 
    
    def deformation(self, ship, deformation_fanc, recursive_1_degree=True):
        if not ship.is_monocoque():
            ship.convert_to_monocoque()
        if not ship.is_monocoque():
            if recursive_1_degree:
                for child_ship in self.dock.get_child_ship(ship):
                    self.shell_positions_deform(child_ship, deformation_fanc)
            return
        self.shell_positions_deform(ship, deformation_fanc)
    
    def deformation_all(self, deformation_fanc):
        self.dock.count_triangles() # covert to monocoque_sehll
        for ship in self.dock.ships:
            if not ship.is_visible:
                continue
            if ship.keel is None:
                continue
            if not ship.is_monocoque():
                continue
            self.shell_positions_deform(ship, deformation_fanc)
        
    def shell_positions_deform(self, ship, deformation_fanc):
        for position in ship.monocoque_shell.positions:
            pos = position.position
            new_x_y_z = deformation_fanc(pos[0], pos[1], pos[2])
            if None != new_x_y_z:
                pos[0] = new_x_y_z[0]
                pos[1] = new_x_y_z[1]
                pos[2] = new_x_y_z[2]
    
    def move_x(self, x):
        if x > 0.:
            void_1 = self.rotate(np.pi/2.).void(x)
            return self.rotate(-np.pi/2.).parent(void_1).void()
        else:
            void_1 = self.rotate(-np.pi/2.).void(abs(x))
            return self.rotate(np.pi/2.).parent(void_1).void()
    
    def move_y(self, y):
        if y > 0.:
            void_1 = self.rotate(np.pi/2., np.pi/2.).void(y)
            void_2 = self.rotate(-np.pi/2.).parent(void_1).void()
            return self.rotate(0., -np.pi/2.).parent(void_2).void()
        else:
            void_1 = self.rotate(-np.pi/2., np.pi/2.).void(abs(y))
            void_2 = self.rotate(np.pi/2.).parent(void_1).void()
            return self.rotate(0., -np.pi/2.).parent(void_2).void()
    
    def move_xy(self, x, y):
        move_1 = self.move_x(x)
        return self.parent(move_1).move_y(y)
    
    def move_z(self, z):
        if (z < 0.):
            return self.move_z_back(abs(z))
        else:
            return self.void(z)

    def move_z_back(self, back_z):
        rotate_1 = self.parent(self.void()).rotate(np.pi).void(back_z)
        return self.rotate(np.pi).parent(rotate_1).void()
    
    def rotate_x(self, rad_x):
        rotate_1 = self.rotate(rad_x, -np.pi/2).void()
        return self.rotate(0., np.pi/2).parent(rotate_1).void()
    
    def fetch_by_name(self, name):
        fetched = []
        for ship in self.dock.ships:
            if ship.name == name:
                fetched.append(ship)
        return fetched
    
    def rotate_bone_xyz_euler(self, x, y, z):
        rotate_1 = self.rotate(-z).void()
        rotate_2 = self.parent(rotate_1).rotate(0., y).void()
        return self.parent(rotate_2).rotate_x(x)
    
    def rotate_bone(self, pw:PostureWrapper, bone_key:str):
        rotate_info = pw.fetch_bone_rotate_dict(bone_key)
        return self.rotate_bone_xyz_euler(rotate_info[BoneKeys.x],rotate_info[BoneKeys.y],rotate_info[BoneKeys.z])
    
    def load_bones(self, pw:PostureWrapper, root:str = None):
        root_obj_name = None
        objects = {}
        for name in pw.fetch_bone_names():
            if root == None:
                if pw.has_value(name,BoneKeys.parent):
                    root_obj_name = name
                    break
            else:
                if name == root:
                    root_obj_name = name
                    break
        if root_obj_name == None:
            raise Exception('root object name is invalid')
        root_obj_rotate = self.rotate_bone(pw, root_obj_name)
        objects[root_obj_name] = self.parent(root_obj_rotate).void(pw.fetch(root_obj_name, BoneKeys.length))
        
        while True:
            target_name = None
            for k,v in pw.postures.items():
                if not k in objects.keys() and v[BoneKeys.parent] in objects.keys():
                    target_name = k
                    break
            if target_name == None:
                break
            parent_name = pw.fetch(target_name, BoneKeys.parent)
            if pw.has_value(target_name, BoneKeys.location):
                offset = pw.fetch(target_name, BoneKeys.location)
                bone_axis_offset = BoneAxisValue(offset[BoneKeys.location_x], offset[BoneKeys.location_y], offset[BoneKeys.location_z])
                obj_geta_1 = self.parent(objects[parent_name], 0.).move_z(bone_axis_offset.global_z())
                obj_geta_2 = self.parent(obj_geta_1).move_xy(bone_axis_offset.global_x(), bone_axis_offset.global_y())
                obj_geta_3 = self.parent(obj_geta_2).rotate_bone(pw, target_name)
                objects[target_name] = self.parent(obj_geta_3).void(pw.fetch(target_name, BoneKeys.length))
            else:
                obj_geta_1 = self.parent(objects[parent_name], 0.).rotate_bone(pw, target_name)
                objects[target_name] = self.parent(obj_geta_1).void(pw.fetch(target_name, BoneKeys.length))
        return objects
    
    def load_submodules_name_match(self, bone_objects:dict, list_path:list, alias:dict = {}):
        submodules = {}
        for k,v in bone_objects.items():
            for path in list_path:
                submodule_path = os.path.join(path, k)
                if k in alias.keys():
                    submodule_path = os.path.join(path, alias[k])
                if os.path.exists(submodule_path) and os.path.isdir(submodule_path):
                    submodules[k] = self.parent(v,0.).load_submodule(submodule_path, True, False)
                    submodules[k].name = k
                    break
                if os.path.isfile(submodule_path + ".stl"):
                    submodules[k] = self.parent(v,0.).load_stl(submodule_path + ".stl")
                    submodules[k].name = k
                    break
        return submodules
    
    def load_parent_bone_inversely(self, pw:PostureWrapper, origin:str):
        origin_rotate = pw.fetch_bone_rotate_dict(origin)
        origin_bone_axis_offset = BoneAxisValue(0.,0.,0.,)
        if pw.has_value(origin, BoneKeys.location):
            origin_location = pw.fetch(origin, BoneKeys.location)
            origin_bone_axis_offset = BoneAxisValue(origin_location[BoneKeys.location_x], origin_location[BoneKeys.location_y], origin_location[BoneKeys.location_z])
        parent_object_base = self.rotate_x(-origin_rotate[BoneKeys.x])
        parent_object_base = self.parent(parent_object_base).rotate(0., -origin_rotate[BoneKeys.y]).void()
        parent_object_base = self.parent(parent_object_base).rotate(origin_rotate[BoneKeys.z]).move_z(-origin_bone_axis_offset.global_z())
        parent_object_base = self.parent(parent_object_base).move_xy(-origin_bone_axis_offset.global_x(), -origin_bone_axis_offset.global_y())
        return parent_object_base

    def generate_stl(self, path, fname):
        print("output stl file: ", fname)
        file_full_name = os.path.join(path, fname)
        f = open(file_full_name, "w", encoding="ascii")
        f.write("solid \n")
        self.dock.write_stl(f)
        f.write("endsolid ")
        f.close()

    def generate_stl_binary(self, path, fname, concatinated=True, divided=True):
        print("output stl file: ", fname)
        if concatinated:
            file_full_name = os.path.join(path, fname)
            f = open(file_full_name, "wb")
            # 80Byte padding
            for i in range(8):
                f.write(struct.pack("xxxxxxxxxx"))
            
            # count triangles
            count = self.dock.count_triangles()
            f.write(struct.pack("<L", count))

            # write triangles data
            self.dock.write_stl_binary(f)
            f.close()
        
        if divided:
            dir_full_name = os.path.join(path, 'divided')
            try:
                shutil.rmtree(dir_full_name)
            except FileNotFoundError:
                pass # ignore

            os.mkdir(dir_full_name)

            self.dock.write_stl_binary_divided(dir_full_name)
