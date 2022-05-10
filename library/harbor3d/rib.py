from dataclasses import dataclass, field

import numpy as np

from typing import List

from .util import EndSurface, Facet, Position, Triangle

@dataclass
class Rib:

    edges: list = field(default_factory=list)
    position: float = field(default=0.)
    
    def write_stl_beam(self, keel, former_rib_edges, is_former_rib_clockwise, f):
        edges_count = len(self.edges)
        if self.edges is None:
            return None
        return_edges = []
        for edge in self.edges:
            translated_edge = np.dot(np.array([edge[0], edge[1], 0., 1.]), keel.translation(self.position))
            return_edges.append(translated_edge)
        is_rib_clockwise = EndSurface().rib_to_vectors(self).is_clockwise
        if former_rib_edges is not None \
            and len(former_rib_edges) != 0 \
            and len(return_edges) != 0:
            Rib.write_stl_inter_edges(former_rib_edges, is_former_rib_clockwise, return_edges, is_rib_clockwise, f)
        return return_edges, is_rib_clockwise

    def write_stl_start(self, keel, f):
        edges_count = len(self.edges)
        if edges_count <= 2:
            return
        else:
            facets = EndSurface().rib_to_vectors(self).generate_facets(is_start_side=True)
            for facet in facets:
                facet.translation(keel.translation(self.position))
                facet.calc_normal()
                facet.write(f)

    def write_stl_end(self, keel, f):
        edges_count = len(self.edges)
        if edges_count <= 2:
            return
        else:
            facets = EndSurface().rib_to_vectors(self).generate_facets(is_start_side=False)
            for facet in facets:
                facet.translation(keel.translation(self.position))
                facet.calc_normal()
                facet.write(f)
    
    def generate_monocoque_shells_beam(
        self, monocoque_shell, keel, former_rib_positions, is_former_rib_clockwise, end_rib_positions):
        if self.edges is None:
            return former_rib_positions, is_former_rib_clockwise

        return_positions = []
        if None == end_rib_positions:
            for edge in self.edges:
                translated_edge = np.array([edge[0], edge[1], keel.length * self.position, 1.])
                return_positions.append(Position(translated_edge))
            monocoque_shell.positions.extend(return_positions)
        else:
            return_positions = end_rib_positions
        is_rib_clockwise = EndSurface().rib_to_vectors(self).is_clockwise
        if former_rib_positions is not None \
            and len(former_rib_positions) != 0 \
            and len(return_positions) != 0:
            monocoque_shell.triangles.extend(
                Rib.generate_monocoque_inter_positions(
                    former_rib_positions, is_former_rib_clockwise, return_positions, is_rib_clockwise))
        return return_positions, is_rib_clockwise

    def generate_monocoque_shell_start(self, monocoque_shell, z_position):
        endSurface = EndSurface().rib_to_vectors(self)
        return endSurface.generate_monocoque_shells(monocoque_shell, z_position, is_start_side=True), endSurface.is_clockwise

    def generate_monocoque_shell_end(self, monocoque_shell, z_position):
        edges_count = len(self.edges)
        if edges_count <= 2:
            return None
        else:
            return EndSurface().rib_to_vectors(self).generate_monocoque_shells(
                monocoque_shell, z_position, is_start_side=False)
    
    @staticmethod
    def write_stl_inter_edges(former_rib_edges, is_former_rib_clockwise, edges, is_rib_clockwise, f):
        if len(edges) == 1 and len(former_rib_edges) == 1:
            return
        edges_count = len(edges) if len(edges) >= len(former_rib_edges) else len(former_rib_edges)
        is_clockwise = is_rib_clockwise if len(edges) != 1 else is_former_rib_clockwise
        if is_clockwise:
            for i in range(edges_count):
                if len(edges) != 1:
                    facet = Facet()
                    facet.vertex_1 = edges[i]
                    facet.vertex_2 = former_rib_edges[(i-1)//(edges_count//len(former_rib_edges))]#i==0の時も成立
                    facet.vertex_3 = edges[i-1]
                    facet.calc_normal()
                    facet.write(f)

                if len(former_rib_edges) != 1:
                    facet = Facet()
                    facet.vertex_1 = edges[i//(edges_count//len(edges))]
                    facet.vertex_2 = former_rib_edges[i]
                    facet.vertex_3 = former_rib_edges[i-1]
                    facet.calc_normal()
                    facet.write(f)
        else:
            for i in range(edges_count):
                if len(former_rib_edges) != 1:
                    facet = Facet()
                    facet.vertex_1 = edges[i]
                    facet.vertex_2 = edges[i-1]
                    facet.vertex_3 = former_rib_edges[(i-1)//(edges_count//len(former_rib_edges))]#i==0の時も成立
                    facet.calc_normal()
                    facet.write(f)

                if len(edges) != 1:
                    facet = Facet()
                    facet.vertex_1 = edges[i//(edges_count//len(edges))]
                    facet.vertex_2 = former_rib_edges[i-1]
                    facet.vertex_3 = former_rib_edges[i]
                    facet.calc_normal()
                    facet.write(f)
    
    @staticmethod
    def generate_monocoque_inter_positions(former_rib_positions, is_former_rib_clockwise, positions, is_rib_clockwise):
        triangles = []
        positions_count = len(positions) if len(positions) >= len(former_rib_positions) else len(former_rib_positions)
        is_clockwise = is_rib_clockwise if len(positions) != 1 else is_former_rib_clockwise
        for i in range(positions_count):
            if len(positions) != 1:
                triangle_1 = Triangle(positions[i], positions[i-1], former_rib_positions[(i-1)//(positions_count//len(former_rib_positions))])
                if is_clockwise:
                    triangle_1.inverse()
                triangles.append(triangle_1)
            if len(former_rib_positions) != 1:
                triangle_2 = Triangle(positions[i//(positions_count//len(positions))], former_rib_positions[i-1], former_rib_positions[i])
                if is_clockwise:
                    triangle_2.inverse()
                triangles.append(triangle_2)
        return triangles
