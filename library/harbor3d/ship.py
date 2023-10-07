from dataclasses import dataclass, field

import numpy as np

from .keel import Keel
from .rib import Rib
from .util import EndSurface, MonocoqueShell
from .util import calc_util, model_util, load_util, load_rib_from_bmp_util, edges_util

from typing import List, Any
from functools import reduce

@dataclass
class Ship:
    keel:Keel = field(default=None)
    ribs:List[Rib] = field(default_factory=list)
    parent:any = field(default=None)
    parents:List[Any] = field(default_factory=list)
    parents_dirty_flag:bool = field(default=False)
    translation_dirty_flag:bool = field(default=False)
    parent_keels_position:float =  field(default=1.)

    name: str = field(default=None)

    smoothing:bool = field(default=False)
    smoothing_from:any = field(default=None)
    smoothing_to:any = field(default=None)

    monocoque_shell:MonocoqueShell = field(default=None)
    monocoque_shell_max_z_position:float = field(default=0.)

    subtracts:List[Any] = field(default_factory=list)

    is_visible:bool = field(default=True)

    def length(self):
        return self.keel.length()

    def has_name(self):
        return self.name != None and len(self.name) != 0

    def set_parent(self, parent, position=1.):
        self.parent_keels_position = position
        self.parent = parent
        self.sanitize_keel()
        self.parents = []
        self.get_parents()
        return self

    def get_parents(self):
        self.parents_dirty_flag = False
        if self.parent == None:
            return []
        self.parents = []
        self.parents.extend(self.parent.get_parents())
        self.parents.append(self.parent)
        return self.parents
    
    def is_contains_in_parents(self, target_ship):
        for ship in self.parents:
            if ship is target_ship:
                return True
        return False

    def end(self, child):
        child.end = self
        return self

    def relative_vector(self):
        if self.keel is None:
            return None
        return self.keel.end - self.keel.start

    def write_stl(self, f):
        if not self.is_visible:
            return
        if self.keel is None:
            return
        if None != self.monocoque_shell:
            self.monocoque_shell.write_stl(self.keel, f)
            return
        if self.smoothing:
            if self.smoothing_from is None\
                or self.smoothing_from.ribs is None or len(self.smoothing_from.ribs) == 0\
                or self.smoothing_to is None\
                or self.smoothing_to.ribs is None or len(self.smoothing_to.ribs) == 0:
                return
            rib_from = self.get_rib_end(self.smoothing_from)
            translated_edges_from = []
            for edge in rib_from.edges:
                translated_edge_from = np.dot(np.array([edge[0], edge[1], 0., 1.]), self.smoothing_from.keel.translation(rib_from.position))
                translated_edges_from.append(translated_edge_from)

            rib_to = self.get_rib_start(self.smoothing_to)
            translated_edges_to = []
            for edge in rib_to.edges:
                translated_edge_to = np.dot(np.array([edge[0], edge[1], 0., 1.]), self.smoothing_to.keel.translation(rib_to.position))
                translated_edges_to.append(translated_edge_to)
            
            end_surface_from = EndSurface().rib_to_vectors(rib_from)
            end_surface_to = EndSurface().rib_to_vectors(rib_to)
            Rib.write_stl_inter_edges(translated_edges_from, end_surface_from.is_clockwise, translated_edges_to, end_surface_to.is_clockwise, f)
        else:
            if len(self.ribs) == 0:
                return
            rib_start = self.get_rib_start(self)
            rib_start.write_stl_start(self.keel, f)
            rib_end = self.get_rib_end(self)
            rib_end.write_stl_end(self.keel, f)
            former_rib_edges = None
            is_former_rib_clockwise = True
            for rib in self.ribs:
                former_rib_info = rib.write_stl_beam(self.keel, former_rib_edges, is_former_rib_clockwise, f)
                if former_rib_info != None:
                    former_rib_edges, is_former_rib_clockwise = former_rib_info

    def write_stl_binary(self, f):
        # possible to think only about the monocoque shell
        if not self.is_visible:
            return
        if self.keel is None:
            return
        if not self.is_monocoque():
            return
        self.monocoque_shell.write_stl_binary(self.keel, f)
    
    def init_keel(self):
        self.keel = Keel()
        return self.keel
    
    def sanitize_keel(self):
        self.keel.set_start(self.parent.keel.translation(self.parent_keels_position))

    def add_rib(self, position=0., edges=None):
        new_rib = Rib()
        new_rib.position = position
        new_rib.edges = edges
        self.ribs.append(new_rib)
    
    def add_ribs(self, positions=[0.,1.], edges=None):
        for position in positions:
            self.add_rib(position, edges)
    
    def add_rib_load_bmp(self, position, path, additional_vertex=0, scale = None, mirror_plane = None):
        new_rib = Rib()
        new_rib.position = position
        new_rib.edges = edges_util.mirror(edges_util.scale(load_rib_from_bmp_util.generate_edges_from_bmp(path, additional_vertex), scale), mirror_plane)
        self.ribs.append(new_rib)

    def order_ribs(self):
        self.ribs.sort(key=lambda rib: rib.position)
    
    def set_smoothing(self, ship_smoothing_from, ship_smoothing_to=None):
        self.smoothing = True
        self.smoothing_from = ship_smoothing_from
        self.smoothing_to = ship_smoothing_to
    
    def set_smoothing_to(self, ship_smoothing_to):
        self.smoothing = True
        self.smoothing_to = ship_smoothing_to

    def get_rib_end(self, ship):
        rib_end = ship.ribs[-1]
        for rib in ship.ribs:
            if rib.position > rib_end.position:
                rib_end = rib
        return rib_end

    def get_rib_start(self, ship):
        rib_start = ship.ribs[0]
        for rib in ship.ribs:
            if rib.position < rib_start.position:
                rib_start = rib
        return rib_start

    def load_stl(self, path, vertex_matching=False):
        self.monocoque_shell = load_util.load_binary_stl(path, vertex_matching)
    
    def load_huge_binary_stl(self, path):
        self.monocoque_shell = load_util.load_huge_binary_stl(path)

    def convert_to_monocoque(self):
        if self.keel is None:
            return
        # smoothingへは未対応
        if len(self.ribs) == 0:
            return
        self.order_ribs()

        self.monocoque_shell = MonocoqueShell()
        
        rib_start = self.ribs[0]
        rib_end = self.ribs[-1]
        
        former_rib_positions = None
        is_former_rib_clockwise = None
        for index, rib in enumerate(self.ribs):
            if index == 0:
                continue
            positions_end = None
            if index == 1:
                former_rib_positions, is_former_rib_clockwise = rib_start.generate_monocoque_shell_start(
                    self.monocoque_shell, self.keel.length * rib_start.position)
            if index == len(self.ribs) - 1:
                positions_end = rib_end.generate_monocoque_shell_end(
                    self.monocoque_shell, self.keel.length * rib_end.position)
            former_rib_info = rib.generate_monocoque_shells_beam(
                self.monocoque_shell, self.keel, former_rib_positions, is_former_rib_clockwise, positions_end)
            if former_rib_info != None:
                former_rib_positions, is_former_rib_clockwise = former_rib_info
    
    def is_monocoque(self):
        return None != self.monocoque_shell

    def align_keel_size_to_monocoque_shell(self):
        self.keel.length = self.monocoque_shell_max_z_position
        return self
    
    def apply_subtructions(self):
        if not self.is_monocoque():
            self.convert_to_monocoque()
        for subtract_ship in self.subtracts:
            subtract_ship.is_visible = False
            if not subtract_ship.is_monocoque():
                subtract_ship.convert_to_monocoque()
            relative_translation = subtract_ship.keel.relative_translation.copy()
            if not reduce(lambda x, y: x or y, map(lambda x: x is self, subtract_ship.parents)):
                relative_translation_to_self = self.keel.relative_translation.copy()
                common_ancestors = [x for x in self.parents if any(x is y for y in subtract_ship.parents)]
                if 0 == len(common_ancestors):
                    self.calc_relative_translation_to_ancestor(subtract_ship, None, relative_translation)
                    self.calc_relative_translation_to_ancestor(self, None, relative_translation_to_self)
                else:
                    common_ancestors.sort(key=lambda ship: len(ship.parents))
                    common_ancestor = common_ancestors[-1]
                    self.calc_relative_translation_to_ancestor(subtract_ship, common_ancestor, relative_translation)
                    self.calc_relative_translation_to_ancestor(self, common_ancestor, relative_translation_to_self)
                relative_translation = np.dot(relative_translation, np.linalg.inv(relative_translation_to_self))
            else:
                self.calc_relative_translation_to_ancestor(subtract_ship, self, relative_translation)
            self.subtract(subtract_ship, relative_translation)
        self.subtracts = [] 
    
    def calc_relative_translation_to_ancestor(self, ship, ship_ancestor, translation):
        if ship.parent is None:
                return
        translation[:] = np.dot(translation, np.dot(ship.parent.keel.translation_z(ship.parent_keels_position), ship.parent.keel.relative_translation))
        if ship.parent is ship_ancestor:
            return
        else:
            self.calc_relative_translation_to_ancestor(ship.parent, ship_ancestor, translation)

    def subtract(self, subtraction, translation, min_distance_limit=0.001, epsilon = 1e-11):
        subtraction.monocoque_shell.translate(translation)
        subtraction.monocoque_shell.copy_translated_to_default()

        self_line_segments = self.monocoque_shell.generate_line_segments()
        subtraction_line_segments = subtraction.monocoque_shell.generate_line_segments()

        model_util.check_line_segments_distance(self_line_segments, subtraction_line_segments, min_distance_limit, epsilon)

        penetrations_self = model_util.calc_penetration(self.monocoque_shell.triangles, subtraction_line_segments)
        penetrations_subtrantion =  model_util.calc_penetration(subtraction.monocoque_shell.triangles, self_line_segments)

        penetrating_triangles_self = model_util.fetch_penetrating_triangles(penetrations_subtrantion)
        penetrating_triangles_subtrantion = model_util.fetch_penetrating_triangles(penetrations_self)

        subdivided_self = model_util.subdivide_penetrated_faces(penetrations_self, penetrations_subtrantion, epsilon)
        subdivided_subtraction = model_util.subdivide_penetrated_faces(penetrations_subtrantion, penetrations_self, epsilon)

        self.monocoque_shell.triangles = list(x for x in self.monocoque_shell.triangles if not any(x is y for y in penetrating_triangles_self))
        subtraction.monocoque_shell.triangles = list(x for x in subtraction.monocoque_shell.triangles if not any(x is y for y in penetrating_triangles_subtrantion))
        
        self.monocoque_shell.triangles.extend(subdivided_self)
        subtraction.monocoque_shell.triangles.extend(subdivided_subtraction)

        self_triangles_subdivided = list(map(lambda x: (x, x.center_position()), iter(penetrating_triangles_self)))
        subtraction_triangles_subdivided = list(map(lambda x: (x, x.center_position()), iter(penetrating_triangles_subtrantion)))

        self_outer_triangles = []
        for self_triangle in self.monocoque_shell.triangles:
            subtraction_triangles_subdivided_with_distance = []
            for subtraction_triangle in subtraction_triangles_subdivided:
                distance = self_triangle.center_position().distance(subtraction_triangle[1])
                subtraction_triangles_subdivided_with_distance.append(\
                    (subtraction_triangle[0], subtraction_triangle[1], distance))
            
            subtraction_triangles_subdivided_with_distance.sort(key=lambda p: p[2])
            for near_triangle_with_distance in subtraction_triangles_subdivided_with_distance:
                near_triangle = near_triangle_with_distance[0]
                vector_vertex1_to_2 = calc_util.extract_vector_1by3(near_triangle.vertex_1.vector_to(near_triangle.vertex_2))
                vector_vertex1_to_3 = calc_util.extract_vector_1by3(near_triangle.vertex_1.vector_to(near_triangle.vertex_3))
                outer_product_near_triangle = np.cross(vector_vertex1_to_2, vector_vertex1_to_3)
                self_v1_to_near_triangle_v1 = calc_util.extract_vector_1by3(near_triangle.vertex_1.vector_to(self_triangle.center_position()))
                dot = np.dot(outer_product_near_triangle, self_v1_to_near_triangle_v1)
                if abs(dot) < epsilon:
                    continue
                elif dot > 0:
                    self_outer_triangles.append(self_triangle)
                    break
                
        self.monocoque_shell.triangles = self_outer_triangles

        subtraction_outer_triangles = []
        for subtraction_triangle in subtraction.monocoque_shell.triangles:
            self_triangles_subdivided_with_distance = []
            for self_triangle in self_triangles_subdivided:
                distance = subtraction_triangle.center_position().distance(self_triangle[1])
                self_triangles_subdivided_with_distance.append(\
                    (self_triangle[0], self_triangle[1], distance))
            
            self_triangles_subdivided_with_distance.sort(key=lambda p: p[2])
            for near_triangle_with_distance in self_triangles_subdivided_with_distance:
                near_triangle = near_triangle_with_distance[0]
                find_outer = False
                vector_vertex1_to_2 = calc_util.extract_vector_1by3(near_triangle.vertex_1.vector_to(near_triangle.vertex_2))
                vector_vertex1_to_3 = calc_util.extract_vector_1by3(near_triangle.vertex_1.vector_to(near_triangle.vertex_3))
                outer_product_near_triangle = np.cross(vector_vertex1_to_2, vector_vertex1_to_3)
                subtraction_v1_to_near_triangle_v1 = calc_util.extract_vector_1by3(near_triangle.vertex_1.vector_to(subtraction_triangle.center_position()))
                dot = np.dot(outer_product_near_triangle, subtraction_v1_to_near_triangle_v1)
                if abs(dot) < epsilon:
                    continue
                elif dot > 0:
                    subtraction_outer_triangles.append(subtraction_triangle)
                    find_outer = True
                    break
                if find_outer:
                    breakpoint
        
        subtraction.monocoque_shell.triangles = list(x for x in subtraction.monocoque_shell.triangles if not any(x is y for y in subtraction_outer_triangles))
        for subtraction_triangle in subtraction.monocoque_shell.triangles:
            subtraction_triangle.inverse()
        self.monocoque_shell.triangles.extend(subtraction.monocoque_shell.triangles)

        positions_set = set()
        for self_triangle in self.monocoque_shell.triangles:
            positions_set |= set(self_triangle.get_positions())
        self.monocoque_shell.positions = list(positions_set)

        triangles_set = set()
        for self_triangle in self.monocoque_shell.triangles:
            triangles_set.add(self_triangle)
        self.monocoque_shell.triangles = list(triangles_set)
