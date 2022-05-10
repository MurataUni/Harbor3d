from dataclasses import dataclass, field

import numpy as np

from typing import List

import struct

from harbor3d.util import calc_util

@dataclass
class Facet:
    vertex_1: np.array = field(default=None)
    vertex_2: np.array = field(default=None)
    vertex_3: np.array = field(default=None)
    normal: np.array = field(default=None)
    
    def translation(self, translation):
        self.vertex_1 = np.dot(self.vertex_1, translation)
        self.vertex_2 = np.dot(self.vertex_2, translation)
        self.vertex_3 = np.dot(self.vertex_3, translation)

    def calc_normal(self):
        cross_product = np.cross(\
            self.vertex_2[:-1] - self.vertex_1[:-1] ,\
            self.vertex_3[:-1] - self.vertex_1[:-1])
        l2_norm = np.linalg.norm(cross_product, ord=2)
        if l2_norm > 0.: #0除算が発生することがあるので暫定
            cross_product /= l2_norm
        self.normal = np.array([cross_product[0], cross_product[1], cross_product[2], 1.])

    def write(self, f):
        f.write(' facet normal {} {} {}\n'.format(self.normal[0], self.normal[1], self.normal[2]))
        f.write('  outer loop\n')
        f.write('   vertex {} {} {}\n'.format(self.vertex_1[0], self.vertex_1[1], self.vertex_1[2]))
        f.write('   vertex {} {} {}\n'.format(self.vertex_2[0], self.vertex_2[1], self.vertex_2[2]))
        f.write('   vertex {} {} {}\n'.format(self.vertex_3[0], self.vertex_3[1], self.vertex_3[2]))
        f.write('  endloop\n')
        f.write(' endfacet\n')
    
    def write_binary(self, f):
        f.write(struct.pack('<fff', self.normal[0], self.normal[1], self.normal[2]))
        f.write(struct.pack('<fff', self.vertex_1[0], self.vertex_1[1], self.vertex_1[2]))
        f.write(struct.pack('<fff', self.vertex_2[0], self.vertex_2[1], self.vertex_2[2]))
        f.write(struct.pack('<fff', self.vertex_3[0], self.vertex_3[1], self.vertex_3[2]))
        f.write(struct.pack('xx'))
 
@dataclass
class EndSurface:
    edges:List[np.array] = field(default_factory=list)
    vectors:List[np.array] = field(default_factory=list)
    exterior_angles:List[float] = field(default_factory=list)
    is_clockwise:bool = field(default=None)

    def rib_to_vectors(self, rib):
        for i in range(len(rib.edges)):
            self.edges.append(calc_util.extract_vector_1by2(rib.edges[i]))
        self.vectors = EndSurface.calc_vectors(rib.edges)
        self.exterior_angles = EndSurface.calc_exterior_angles(self.vectors)
        self.is_clockwise = (sum(self.exterior_angles) < 0)
        return self

    def generate_facets(self, is_start_side):
        is_need_inverse = is_start_side ^ self.is_clockwise
        
        facets = []
        edges = self.edges[:]
        vectors = self.vectors[:]
        exterior_angles = self.exterior_angles[:]
        sum_exterior_angles = sum(self.exterior_angles)

        is_concave = True
        while(is_concave):
            is_concave = False
            for i in range(len(exterior_angles)):
                if exterior_angles[i - 2] * sum_exterior_angles <= 0:
                    is_concave = True
                    if 0 < exterior_angles[i - 1] * sum_exterior_angles:
                        facet = Facet()
                        if is_need_inverse:
                            facet.vertex_1 = calc_util.extend_vector_1by4(edges[i-2])
                            facet.vertex_2 = calc_util.extend_vector_1by4(edges[i])
                            facet.vertex_3 = calc_util.extend_vector_1by4(edges[i-1])
                        else:
                            facet.vertex_1 = calc_util.extend_vector_1by4(edges[i-2])
                            facet.vertex_2 = calc_util.extend_vector_1by4(edges[i-1])
                            facet.vertex_3 = calc_util.extend_vector_1by4(edges[i])
                        facets.append(facet)
                        del edges[i-1]
                        vectors = EndSurface.calc_vectors(edges)
                        exterior_angles = EndSurface.calc_exterior_angles(vectors)
                        break
        
        for i in range(len(edges) - 2):
            facet = Facet()
            if is_need_inverse:
                facet.vertex_1 = calc_util.extend_vector_1by4(edges[0])
                facet.vertex_2 = calc_util.extend_vector_1by4(edges[i+2])
                facet.vertex_3 = calc_util.extend_vector_1by4(edges[i+1])
            else:
                facet.vertex_1 = calc_util.extend_vector_1by4(edges[0])
                facet.vertex_2 = calc_util.extend_vector_1by4(edges[i+1])
                facet.vertex_3 = calc_util.extend_vector_1by4(edges[i+2])
            facets.append(facet)
        return facets
    
    def generate_monocoque_shells(self, monocoque_shell, z_position, is_start_side):
        is_need_inverse = is_start_side ^ self.is_clockwise
        
        edges = self.edges[:]
        vectors = self.vectors[:]
        exterior_angles = self.exterior_angles[:]
        sum_exterior_angles = sum(self.exterior_angles)

        for edge in edges:
            monocoque_shell.positions.append(
                Position(calc_util.extend_vector_1by4(edge)))
            monocoque_shell.positions[-1].position[2] = z_position
        positions = monocoque_shell.positions[- len(self.edges):]
        if len(positions) <= 2:
            return positions

        is_concave = True
        while(is_concave):
            is_concave = False
            for i in range(len(exterior_angles)):
                if exterior_angles[i - 2] * sum_exterior_angles <= 0:
                    is_concave = True
                    if 0 < exterior_angles[i - 1] * sum_exterior_angles:
                        triangle = Triangle(positions[i-2], positions[i-1], positions[i])
                        is_position_contain_triangle = False
                        for pos in [i for i in positions if not triangle.is_contains(i)]:
                            if triangle.is_position_contain_triangle_xy_plane((pos.position[0], pos.position[1])):
                                is_position_contain_triangle = True
                                break
                        if not is_position_contain_triangle:
                            monocoque_shell.triangles.append(triangle)
                            if is_need_inverse:
                                monocoque_shell.triangles[-1].inverse()
                            del edges[i-1]
                            del positions[i-1]
                            vectors = EndSurface.calc_vectors(edges)
                            exterior_angles = EndSurface.calc_exterior_angles(vectors)
                            break
                    if 0 < exterior_angles[i - 3] * sum_exterior_angles:
                        triangle = Triangle(positions[i-2], positions[i-4], positions[i-3])
                        is_position_contain_triangle = False
                        for pos in [i for i in positions if not triangle.is_contains(i)]:
                            if triangle.is_position_contain_triangle_xy_plane((pos.position[0], pos.position[1])):
                                is_position_contain_triangle = True
                                break
                        if not is_position_contain_triangle:
                            monocoque_shell.triangles.append(triangle)
                            if is_need_inverse:
                                monocoque_shell.triangles[-1].inverse()
                            del edges[i-3]
                            del positions[i-3]
                            vectors = EndSurface.calc_vectors(edges)
                            exterior_angles = EndSurface.calc_exterior_angles(vectors)
                            break
        for i in range(len(edges) - 2):
            monocoque_shell.triangles.append(Triangle(
                positions[0],
                positions[i+1],
                positions[i+2]))
            if is_need_inverse:
                monocoque_shell.triangles[-1].inverse()
        return monocoque_shell.positions[- len(self.edges):]
        
    @staticmethod
    def calc_exterior_angles(vectors):
        exterior_angles = []
        for i in range(len(vectors) - 1):
            exterior_angles.append(
                calc_util.exterior_angle(vectors[i], vectors[i + 1]))
                
        exterior_angles.append(
            calc_util.exterior_angle(vectors[-1], vectors[0]))
        
        return exterior_angles
    
    @staticmethod
    def calc_vectors(edges):
        vectors = []
        for i in range(len(edges)):
            vectors.append(np.array(edges[i]) - np.array(edges[i-1]))
        return vectors

    
@dataclass
class Position:
    position: np.array
    translated_position: np.array = field(default=None)

    def __hash__(self):
        return hash(id(self))

    def translate(self, translation):
        self.translated_position = \
            np.dot(calc_util.extend_vector_1by4(self.position), translation)

    def copy_translated_to_default(self):
        self.position = self.translated_position
        self.translated_position = None
    
    def vector_to(self, position):
        vector = position.position - self.position
        vector[3] = 1.
        return vector
    
    def distance(self, other_position):
        vector = calc_util.extract_vector_1by3(self.vector_to(other_position))
        return np.linalg.norm(vector)
    
@dataclass
class Triangle:
    vertex_1: Position
    vertex_2: Position
    vertex_3: Position

    def __hash__(self):
        return hash(id(self))

    def inverse(self):
        temp = self.vertex_2
        self.vertex_2 = self.vertex_3
        self.vertex_3 = temp

    def is_contains(self, position):
        return self.vertex_1 is position or self.vertex_2 is position or self.vertex_3 is position

    def is_contains_two_position(self, positions):
        return 2 == sum([1 for x in positions if self.is_contains(x)])

    def is_touched_side(self, triangle):
        return 2 == sum([1 for x in [self.is_contains(triangle.vertex_1), self.is_contains(triangle.vertex_2), self.is_contains(triangle.vertex_3)] if x])
    
    def is_equal(self, triangle):
        return 3 == sum([1 for x in [self.is_contains(triangle.vertex_1), self.is_contains(triangle.vertex_2), self.is_contains(triangle.vertex_3)] if x])

    def center_position(self):
        position = (self.vertex_1.position + self.vertex_2.position + self.vertex_3.position)/3
        position[3] = 1.
        return Position(position)
    
    def is_position_contain_triangle_xy_plane(self, xy_taple):
        vector_target_to_v1 = np.array([self.vertex_1.position[0]-xy_taple[0], self.vertex_1.position[1]-xy_taple[1]])
        vector_target_to_v2 = np.array([self.vertex_2.position[0]-xy_taple[0], self.vertex_2.position[1]-xy_taple[1]])
        vector_target_to_v3 = np.array([self.vertex_3.position[0]-xy_taple[0], self.vertex_3.position[1]-xy_taple[1]])
        outer_product_v1_v2 = np.cross(vector_target_to_v1, vector_target_to_v2)
        outer_product_v2_v3 = np.cross(vector_target_to_v2, vector_target_to_v3)
        outer_product_v3_v1 = np.cross(vector_target_to_v3, vector_target_to_v1)
        return 0. < (outer_product_v1_v2 * outer_product_v2_v3) and 0. < (outer_product_v2_v3 * outer_product_v3_v1)
    
    def get_positions(self):
        return [self.vertex_1, self.vertex_2, self.vertex_3]
    
    def write_stl(self, keel, f):
        if self.vertex_1 is None or self.vertex_2 is None or self.vertex_3 is None:
            return
        facet = Facet(self.vertex_1.position, self.vertex_2.position, self.vertex_3.position)
        facet.translation(np.dot(keel.relative_translation, keel.origin_translation))
        facet.calc_normal()
        facet.write(f)
    
    def write_stl_binary(self, keel, f):
        if self.vertex_1 is None or self.vertex_2 is None or self.vertex_3 is None:
            return
        facet = Facet(self.vertex_1.position, self.vertex_2.position, self.vertex_3.position)
        facet.translation(np.dot(keel.relative_translation, keel.origin_translation))
        facet.calc_normal()
        facet.write_binary(f)

@dataclass
class MonocoqueShell:
    positions:List[Position] = field(default_factory=list)
    triangles:List[Triangle] = field(default_factory=list)

    def translate(self, translation):
        for position in self.positions:
            position.translate(translation)
    
    def copy_translated_to_default(self):
        for position in self.positions:
            position.copy_translated_to_default()
    
    def write_stl(self, keel, f):
        for triangle in self.triangles:
            triangle.write_stl(keel, f)
    
    def write_stl_binary(self, keel, f):
        for triangle in self.triangles:
            triangle.write_stl_binary(keel, f)

    def generate_line_segments(self):
        if 0 == len(self.triangles):
            return None
        line_segments = []
        for triangle in self.triangles:
            if 0 == len(line_segments):
                line_segments.extend([
                    LineSegment(triangle.vertex_1, triangle.vertex_2), 
                    LineSegment(triangle.vertex_2, triangle.vertex_3), 
                    LineSegment(triangle.vertex_3, triangle.vertex_1)
                ])
                for line_segment in line_segments:
                    line_segment.belong_to.append(triangle)
                continue

            v1_v2 = False
            v2_v3 = False
            v3_v1 = False
            for line_segment in line_segments:
                if line_segment.check_triangle(triangle):
                    is_contains_v1 = line_segment.is_contains(triangle.vertex_1)
                    is_contains_v2 = line_segment.is_contains(triangle.vertex_2)
                    is_contains_v3 = line_segment.is_contains(triangle.vertex_3)
                    v1_v2 = v1_v2 or (is_contains_v1 and is_contains_v2)
                    v2_v3 = v2_v3 or (is_contains_v2 and is_contains_v3)
                    v3_v1 = v3_v1 or (is_contains_v3 and is_contains_v1)

            if not v1_v2:
                line_segments.append(LineSegment(triangle.vertex_1, triangle.vertex_2))
                line_segments[-1].belong_to.append(triangle)
            if not v2_v3:
                line_segments.append(LineSegment(triangle.vertex_2, triangle.vertex_3))
                line_segments[-1].belong_to.append(triangle)
            if not v3_v1:
                line_segments.append(LineSegment(triangle.vertex_3, triangle.vertex_1))
                line_segments[-1].belong_to.append(triangle)
        return line_segments

@dataclass
class LineSegment:
    end1:Position = field(default=None)
    end2:Position = field(default=None)
    belong_to:List[Triangle] = field(default_factory=list)

    def check_triangle(self, triangle):
        if triangle.is_contains(self.end1) and triangle.is_contains(self.end2):
            self.belong_to.append(triangle)
            return True
        return False

    def is_contains(self, position):
        return self.end1 is position or self.end2 is position

    def is_equal(self, position1, position2):
        return self.is_contains(position1) and self.is_contains(position2)

    def get_positions(self):
        return [self.end1, self.end2]
    
@dataclass
class Penetration:
    line_segment:LineSegment
    position_on_lines_segment:float
    penetrated_triangle:Triangle
    position:Position

    def position_on_lines_segment_from(self, position):
        return self.position_on_lines_segment if self.line_segment.end1 is position else (1. - self.position_on_lines_segment)

def check_line_segments_distance(self_line_segments, other_line_segments, min_distance_limit, epsilon):
    for self_line_segment in self_line_segments:
        for other_line_segment in other_line_segments:
            if not calc_util.is_positions_overrap_any(self_line_segment.get_positions(), other_line_segment.get_positions()):
                continue
            
            vector_self_line_segment = calc_util.extract_vector_1by3(self_line_segment.end1.vector_to(self_line_segment.end2))
            vector_other_line_segment = calc_util.extract_vector_1by3(other_line_segment.end1.vector_to(other_line_segment.end2))
            vector_inter_start_positions = calc_util.extract_vector_1by3(self_line_segment.end1.vector_to(other_line_segment.end1))

            outer_product = np.cross(vector_self_line_segment, vector_other_line_segment)
            outer_product_size = np.linalg.norm(outer_product)

            distance = 0
            if (outer_product_size < epsilon):
                distance = np.dot(vector_self_line_segment, vector_inter_start_positions)/np.linalg.norm(vector_self_line_segment)
                if abs(distance) < min_distance_limit:
                    vector_self_to_other_end1 = calc_util.extract_vector_1by3(self_line_segment.end1.vector_to(other_line_segment.end1))
                    vector_self_to_other_end2 = calc_util.extract_vector_1by3(self_line_segment.end1.vector_to(other_line_segment.end2))
                    dot1 = np.dot(vector_self_line_segment, vector_self_to_other_end1)
                    dot2 = np.dot(vector_self_line_segment, vector_self_to_other_end2)
                    if dot1 * dot2 < 0:
                        continue
                    elif 0 < dot1 * dot2:
                        length_self = np.linalg.norm(vector_self_line_segment)
                        if np.linalg.norm(vector_self_to_other_end1) < length_self \
                            or np.linalg.norm(vector_self_to_other_end2) < length_self:
                            raise Exception
                        continue
                    elif 0 == dot1 and dot2 < 0:
                        continue
                    elif 0 == dot2 and dot1 < 0:
                        continue
                    else:
                        continue
            else:
                distance = np.dot(outer_product, vector_inter_start_positions)/outer_product_size
                if (abs(distance) < min_distance_limit):
                    dot1 = np.dot(vector_inter_start_positions, vector_self_line_segment/np.linalg.norm(vector_self_line_segment))
                    dot2 = np.dot(vector_inter_start_positions, vector_other_line_segment/np.linalg.norm(vector_other_line_segment))
                    dot3 = np.dot(vector_self_line_segment/np.linalg.norm(vector_self_line_segment), \
                        vector_other_line_segment/np.linalg.norm(vector_other_line_segment))
                    position_on_self_vector = (dot1 - dot2*dot3)/(1 - dot3*dot3) / np.linalg.norm(vector_self_line_segment)
                    position_on_other_vector = (dot2 - dot1*dot3)/(dot3*dot3 - 1) / np.linalg.norm(vector_other_line_segment)
                    if (0 <= position_on_self_vector and position_on_self_vector <= 1) \
                        and (0 <= position_on_other_vector and position_on_other_vector <= 1):
                        raise Exception

def calc_penetration(triangles, line_segments):
    penetrations = [] 
    for triangle in triangles:
        for line_segment in line_segments:
            if not calc_util.is_positions_overrap_all(triangle.get_positions(), line_segment.get_positions()):
                continue
            vector_ray = calc_util.extract_vector_1by3(line_segment.end1.vector_to(line_segment.end2))
            
            vector_ray_to_v1 = calc_util.extract_vector_1by3(line_segment.end1.vector_to(triangle.vertex_1))
            vector_ray_to_v2 = calc_util.extract_vector_1by3(line_segment.end1.vector_to(triangle.vertex_2))
            vector_ray_to_v3 = calc_util.extract_vector_1by3(line_segment.end1.vector_to(triangle.vertex_3))

            outer1_2 = np.cross(vector_ray_to_v1, vector_ray_to_v2)
            outer2_3 = np.cross(vector_ray_to_v2, vector_ray_to_v3)
            outer3_1 = np.cross(vector_ray_to_v3, vector_ray_to_v1)

            inner_product_with_side1_2 = np.dot(outer1_2, vector_ray)
            inner_product_with_side2_3 = np.dot(outer2_3, vector_ray)
            inner_product_with_side3_1 = np.dot(outer3_1, vector_ray)
            
            if 0 > inner_product_with_side1_2 * inner_product_with_side2_3 \
                or 0 > inner_product_with_side1_2 * inner_product_with_side3_1:
                continue

            vector_side1_2 = calc_util.extract_vector_1by3(triangle.vertex_1.vector_to(triangle.vertex_2))
            vector_side1_3 = calc_util.extract_vector_1by3(triangle.vertex_1.vector_to(triangle.vertex_3))
            vector_ray_origin_to_vertex1 = calc_util.extract_vector_1by3(triangle.vertex_1.vector_to(line_segment.end1))
            
            solved = np.dot(vector_ray_origin_to_vertex1, np.linalg.inv(np.array([-vector_ray, vector_side1_2, vector_side1_3])))
            
            if solved[0] < 0 or 1 < solved[0] :
                continue

            penetrated_positiron = Position(calc_util.extend_vector_1by4(
                calc_util.extract_vector_1by3(triangle.vertex_1.position) + vector_side1_2 * solved[1] + vector_side1_3 * solved[2]))
            penetrations.append(Penetration(line_segment, solved[0], triangle, penetrated_positiron))
    return penetrations

def fetch_penetrated_triangles(penetrations):
    triangles = []
    for penetration in penetrations:
        if any(penetration.penetrated_triangle is x for x in triangles):
            continue
        triangles.append(penetration.penetrated_triangle)
    return triangles

def fetch_penetrating_triangles(penetrations):
    triangles = []
    for penetration in penetrations:
        for triangle in penetration.line_segment.belong_to:
            if any(triangle is x for x in triangles):
                continue
            triangles.append(triangle)
    return triangles

def fetch_penetrations_related_positions(penetrations, position1, position2):
    related_penetrations = list(x for x in penetrations if x.line_segment.is_equal(position1, position2))
    related_penetrations.sort(key=lambda p: p.position_on_lines_segment_from(position1))
    return related_penetrations

def fetch_pair_side_penetration(target_side_penetration, side_penetrations, exclude=[]):
    for side_penetration in side_penetrations:
        if any(x is side_penetration for x in exclude):
            continue
        if side_penetration is target_side_penetration:
            continue
        if side_penetration.penetrated_triangle is target_side_penetration.penetrated_triangle:
            return side_penetration
    return None 

def fetch_indirect_pair_side_penetration(triangle, side_penetrations, exclude=[]):
    for side_penetration in side_penetrations:
        if any(x is side_penetration for x in exclude):
            continue
        if side_penetration.penetrated_triangle.is_equal(triangle):
            return side_penetration
    return None

def fetch_pair_penetration(triangle, penetrations, exclude=[]):
    for penetration in penetrations:
        if any(x is penetration for x in exclude):
            continue
        if any(triangle.is_equal(x) for x in penetration.line_segment.belong_to):
            return penetration
    return None

def fetch_penetrations_related_triangle(triangle, penetrations):
    return list(x for x in penetrations if x.penetrated_triangle is triangle)

def subdivide_penetrated_faces(penetrations1, penetrations2, epsilon):
    penetrating_triangles1 = fetch_penetrating_triangles(penetrations2)

    triangles = []

    for penetrated_triangle in penetrating_triangles1:
        side1_2_penetratings = fetch_penetrations_related_positions(penetrations2, penetrated_triangle.vertex_1, penetrated_triangle.vertex_2)
        side2_3_penetratings = fetch_penetrations_related_positions(penetrations2, penetrated_triangle.vertex_2, penetrated_triangle.vertex_3)
        side3_1_penetratings = fetch_penetrations_related_positions(penetrations2, penetrated_triangle.vertex_3, penetrated_triangle.vertex_1)
        
        penetrations = fetch_penetrations_related_triangle(penetrated_triangle, penetrations1)

        side_penetrations = side1_2_penetratings.copy()
        side_penetrations.extend(side2_3_penetratings)
        side_penetrations.extend(side3_1_penetratings)

        checked_side_penetrations = []
        
        current = None
        loop_start_side_penetration = None
        is_last_path_along_side = False
        path_penetrations = []

        poligon = []
        poligons = []
        while None != current or len(checked_side_penetrations) != len(side_penetrations):
            if None == current:
                for side_penetration in side_penetrations:
                    if any(side_penetration is x for x in checked_side_penetrations):
                       continue
                    current = side_penetration
                    loop_start_side_penetration = side_penetration
                    is_last_path_along_side = False
                    break
            
            if current is penetrated_triangle.vertex_1:
                if 0 == len(side1_2_penetratings):
                    current = penetrated_triangle.vertex_2
                    poligon.append(current)
                else:
                    current = side1_2_penetratings[0]
                    poligon.append(current.position)
                is_last_path_along_side = True

            elif current is penetrated_triangle.vertex_2:
                if 0 == len(side2_3_penetratings):
                    current = penetrated_triangle.vertex_3
                    poligon.append(current)
                else:
                    current = side2_3_penetratings[0]
                    poligon.append(current.position)
                is_last_path_along_side = True

            elif current is penetrated_triangle.vertex_3:
                if 0 == len(side3_1_penetratings):
                    current = penetrated_triangle.vertex_1
                    poligon.append(current)
                else:
                    current = side3_1_penetratings[0]
                    poligon.append(current.position)
                is_last_path_along_side = True

            elif 0 != len(side1_2_penetratings) and current is side1_2_penetratings[-1] and not is_last_path_along_side:
                checked_side_penetrations.append(current)
                current = penetrated_triangle.vertex_2
                poligon.append(current)
                is_last_path_along_side = True
            elif 0 != len(side2_3_penetratings) and current is side2_3_penetratings[-1] and not is_last_path_along_side:
                checked_side_penetrations.append(current)
                current = penetrated_triangle.vertex_3
                poligon.append(current)
                is_last_path_along_side = True
            elif 0 != len(side3_1_penetratings) and current is side3_1_penetratings[-1] and not is_last_path_along_side:
                checked_side_penetrations.append(current)
                current = penetrated_triangle.vertex_1
                poligon.append(current)
                is_last_path_along_side = True
            else:
                if is_last_path_along_side:
                    path_penetrations = [current]
                    pair_side_penetration = fetch_pair_side_penetration(current, side_penetrations, exclude=path_penetrations)
                    if None != pair_side_penetration:
                        current = pair_side_penetration
                    else:
                        current_triangle = current.penetrated_triangle
                        indirect_pair_side_penetration = None
                        while None == indirect_pair_side_penetration:
                            pair_penetration = fetch_pair_penetration(current_triangle, penetrations, exclude=path_penetrations)
                            current_triangle = next(x for x in pair_penetration.line_segment.belong_to if not current_triangle is x)
                            poligon.append(pair_penetration.position)
                            path_penetrations.append(pair_penetration)
                            indirect_pair_side_penetration = fetch_indirect_pair_side_penetration(current_triangle, side_penetrations, exclude=path_penetrations)
                        current = indirect_pair_side_penetration
                    poligon.append(current.position)
                    is_last_path_along_side = False
                else:
                    checked_side_penetrations.append(current)
                    index_current_penetration = None
                    for index, side_penetration in enumerate(side_penetrations):
                        if current is side_penetration:
                            index_current_penetration = index
                            break
                    current = side_penetrations[index_current_penetration + 1]
                    poligon.append(current.position)
                    is_last_path_along_side = True
                
            if loop_start_side_penetration is current:
                current = None
                poligons.append(poligon.copy())
                poligon = []
                path_penetrations = []
        triangles.extend(generate_subdivide_triangles(poligons, penetrated_triangle, epsilon))
    return triangles

        

def calc_concave_3d(positions, default_outer_product, epsilon):
    vectors = []
    for i in range(len(positions)):
        vectors.append(calc_util.extract_vector_1by3(positions[i-1].vector_to(positions[i])))
    
    list_is_concave = []
    for i in range(len(vectors)):
        outer_product = None
        if i == len(vectors) - 1:
            outer_product = np.cross(vectors[i], vectors[0])
        else:
            outer_product = np.cross(vectors[i], vectors[i + 1])
        dot_outer_products = np.dot(outer_product, default_outer_product)

        if -epsilon > dot_outer_products:
            list_is_concave.append(True)
        elif epsilon < dot_outer_products:
            list_is_concave.append(False)
        else: # -epsilon < dot_outer_products < epsilon
            list_is_concave.append(False)
    return list_is_concave

def generate_subdivide_triangles(poligons, triangle, epsilon):
    triangles = []
    for poligon in poligons:
        if 3 == len(poligon):
            triangles.append(Triangle(poligon[0], poligon[1], poligon[2]))
            continue

        default_outer_product = calc_util.normalize_vector(np.cross(
            calc_util.extract_vector_1by3(triangle.vertex_1.vector_to(triangle.vertex_2)), 
            calc_util.extract_vector_1by3(triangle.vertex_1.vector_to(triangle.vertex_3))))

        list_is_concave = calc_concave_3d(poligon, default_outer_product, epsilon)
        while(any(list_is_concave)):
            for i in range(len(list_is_concave)):
                if list_is_concave[i - 2]:
                    if not list_is_concave[i - 1]:
                        triangles.append(Triangle(
                            poligon[i-2],
                            poligon[i-1],
                            poligon[i]))
                        del poligon[i-1]
                        list_is_concave = calc_concave_3d(poligon, default_outer_product, epsilon)
                        break
        
        for i in range(len(poligon) - 2):
            triangles.append(Triangle(
                poligon[0],
                poligon[i+1],
                poligon[i+2]))
    return triangles
