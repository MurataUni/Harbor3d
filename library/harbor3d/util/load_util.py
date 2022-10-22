import numpy as np
import struct
import os
import glob
import subprocess

from harbor3d.util import model_util

def load_binary_stl(path, vertex_matching=True):
    with open(path, "rb") as f:
        read_block = f.read(80) # discard
        read_block = f.read(4) # discard

        format = "<ffffffffffffxx" # 32bit-float(4byte) * 3 * 4 + padding(1byte) * 2 = 50byte, little endian
        size = struct.calcsize(format)

        triangles = []
        positions = []
        unpacked = tuple()
        while True:
            read_block = f.read(size)
            if len(read_block) != size:
                break
            unpacked = struct.unpack(format, read_block)
            vertex1 = np.array([unpacked[3], unpacked[4], unpacked[5], 1.])
            vertex2 = np.array([unpacked[6], unpacked[7], unpacked[8], 1.])
            vertex3 = np.array([unpacked[9], unpacked[10], unpacked[11], 1.])
            vertexes = [vertex1, vertex2, vertex3]

            triangle = []
            for vertex in vertexes:
                if vertex_matching:
                    # finally, (number of positions) < 3 * (number of triangles)
                    vertex_esists = [x for x in positions if x.position[0] == vertex[0] and x.position[1] == vertex[1] and x.position[2] == vertex[2]]
                    if (0 == len (vertex_esists)):
                        position = model_util.Position(vertex)
                        positions.append(position)
                        triangle.append(position)
                    else:
                        triangle.append(vertex_esists[0])
                else:
                    # finally, (number of positions) == 3 * (number of triangles)
                    position = model_util.Position(vertex)
                    positions.append(position)
                    triangle.append(position)
            triangles.append(model_util.Triangle(triangle[0], triangle[1], triangle[2]))
            
        return model_util.MonocoqueShell(positions, triangles)

def load_huge_binary_stl(path):
    with open(path, "rb") as f:
        read_block = f.read(80) # discard
        read_block = f.read(4) # discard

        format = "<ffffffffffffxx" # 32bit-float(4byte) * 3 * 4 + padding(1byte) * 2 = 50byte, little endian
        size = struct.calcsize(format)

        triangles = []
        positions_dict = dict()
        unpacked = tuple()
        count = 0
        while True:
            count = count + 1
            if 0 == count%100:
                print(count)
            read_block = f.read(size)
            if len(read_block) != size:
                break
            unpacked = struct.unpack(format, read_block)
            vertex1 = np.array([unpacked[3], unpacked[4], unpacked[5], 1.])
            vertex2 = np.array([unpacked[6], unpacked[7], unpacked[8], 1.])
            vertex3 = np.array([unpacked[9], unpacked[10], unpacked[11], 1.])
            vertexes = [vertex1, vertex2, vertex3]

            triangle = []
            for vertex in vertexes:
                if not vertex[2] in positions_dict:
                    positions_dict[vertex[2]] = []
                
                vertex_esists = [x for x in positions_dict[vertex[2]] if x.position[0] == vertex[0] and x.position[1] == vertex[1] and x.position[2] == vertex[2]]
                if (0 == len (vertex_esists)):
                    position = model_util.Position(vertex)
                    positions_dict[vertex[2]].append(position)
                    triangle.append(position)
                else:
                    triangle.append(vertex_esists[0])
            triangles.append(model_util.Triangle(triangle[0], triangle[1], triangle[2]))
        positions = []
        for positions_value in positions_dict.values():
            positions.extend(positions_value)
        return model_util.MonocoqueShell(positions, triangles)

def load_submodule(path, force_load_merged_stl, vertex_matching=True):
    if not os.path.isdir(path):
        raise Exception("submodule is not a path")
    # load stl(case: already exists)
    if not force_load_merged_stl:
        stl_divided_folder_full_path_name = os.path.join(path, "divided")
        stl_divided_files_full_path_names = []
        if os.path.exists(stl_divided_folder_full_path_name):
            stl_divided_files_full_path_names = glob.glob(os.path.join(stl_divided_folder_full_path_name, "*.stl"))
        if 0 != len(stl_divided_files_full_path_names):
            divided_shells = []
            for stl_divided_files_full_path_name in stl_divided_files_full_path_names:
                divided_shells.append(load_binary_stl(stl_divided_files_full_path_name, vertex_matching))
            return divided_shells

    file_name = path.split(os.sep)[-1]
    stl_file_full_path_name = os.path.join(path, file_name + ".stl")
    if os.path.exists(stl_file_full_path_name):
        return [load_binary_stl(stl_file_full_path_name, vertex_matching)]

    # generating stl
    py_file_full_path_name = os.path.join(path, file_name + ".py")
    if os.path.exists(py_file_full_path_name):
        subprocess.call('python %s' % py_file_full_path_name, shell=True)
    
    # load stl(case: generated now)
    if not force_load_merged_stl:
        stl_divided_files_full_path_names = []
        if os.path.exists(stl_divided_folder_full_path_name):
            stl_divided_files_full_path_names = glob.glob(os.path.join(stl_divided_folder_full_path_name, "*.stl"))
        if 0 != len(stl_divided_files_full_path_names):
            divided_shells = []
            for stl_divided_files_full_path_name in stl_divided_files_full_path_names:
                divided_shells.append(load_binary_stl(stl_divided_files_full_path_name, vertex_matching))
            return divided_shells

    if os.path.exists(stl_file_full_path_name):
        return [load_binary_stl(stl_file_full_path_name, vertex_matching)]

    raise Exception("failed to create stl")

def load_vertexes(path):
    with open(path, "rb") as f:
        read_block = f.read(80) # discard
        read_block = f.read(4) # discard

        format = "<ffffffffffffxx" # 32bit-float(4byte) * 3 * 4 + padding(1byte) * 2 = 50byte, little endian
        size = struct.calcsize(format)

        vertexes = []
        unpacked = tuple()
        while True:
            read_block = f.read(size)
            if len(read_block) != size:
                break
            unpacked = struct.unpack(format, read_block)
            vertexes_loaded = [\
                np.array([unpacked[3], unpacked[4], unpacked[5], 1.]),\
                np.array([unpacked[6], unpacked[7], unpacked[8], 1.]),\
                np.array([unpacked[9], unpacked[10], unpacked[11], 1.])]

            for vertex in vertexes_loaded:
                vertex_esists = [x for x in vertexes if x[0] == vertex[0] and x[1] == vertex[1] and x[2] == vertex[2]]
                if (0 == len (vertex_esists)):
                    vertexes.append(vertex)
            
        return vertexes
