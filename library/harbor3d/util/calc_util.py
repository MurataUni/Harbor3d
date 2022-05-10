import numpy as np

from functools import reduce

matrix_unit_dim_4 = [\
            [1., 0., 0., 0.],\
            [0., 1., 0., 0.],\
            [0., 0., 1., 0.],\
            [0., 0., 0., 1.]]

def extract_vector_1by2(vector):
    return vector[:2]

def extract_vector_1by3(vector):
    return vector[:3]

def extend_vector_1by4(vector):
    if 2 == len(vector):
        return np.append(vector, [0, 1])
    elif 3 == len(vector):
        return np.append(vector, 1)
    return vector

def normalize_vector(vector):
    return vector / np.linalg.norm(vector)

def exterior_angle(vector_from, vector_to):
    if not isinstance(vector_from, np.ndarray) \
        or not isinstance(vector_to, np.ndarray):
        return None
    
    vector_from_xy = extract_vector_1by2(vector_from)
    vector_to_xy = extract_vector_1by2(vector_to)
    
    outer_product = np.cross(vector_from_xy, vector_to_xy)

    if 0 < outer_product:
        return unsigined_exterior_angle(vector_from_xy, vector_to_xy)
    elif outer_product < 0:
        return - unsigined_exterior_angle(vector_from_xy, vector_to_xy)
    else: #outer_product = 0
        inner_product = np.dot(vector_from_xy, vector_to_xy)
        if inner_product < 0:
            return np.pi
        else: #0 < inner_product
            return 0

def unsigined_exterior_angle(vector_from, vector_to):
    vector_from_xy = extract_vector_1by2(vector_from)
    vector_to_xy = extract_vector_1by2(vector_to)

    inner_product = np.dot(vector_from_xy, vector_to_xy)
    len_vector_from = np.linalg.norm(vector_from_xy, ord=2)
    len_vector_to = np.linalg.norm(vector_to_xy, ord=2)
    return np.arccos(inner_product/(len_vector_from * len_vector_to))

def is_positions_overrap_on_plane(positions1, positions2, index):
    positions1_plane = list(map(lambda x: x.position[index], positions1))
    positions1_plane_min = reduce(lambda x, y: x if x < y else y, positions1_plane)
    positions1_plane_max = reduce(lambda x, y: x if x > y else y, positions1_plane)
    positions2_plane = list(map(lambda x: x.position[index], positions2))
    positions2_plane_min = reduce(lambda x, y: x if x < y else y, positions2_plane)
    positions2_plane_max = reduce(lambda x, y: x if x > y else y, positions2_plane)
    if positions1_plane_max < positions2_plane_min or positions2_plane_max < positions1_plane_min:
        return False
    return True

def is_positions_and_array_overrap_on_plane(positions, array, index):
    positions1_plane = list(map(lambda x: x.position[index], positions))
    positions1_plane_min = reduce(lambda x, y: x if x < y else y, positions1_plane)
    positions1_plane_max = reduce(lambda x, y: x if x > y else y, positions1_plane)
    positions2_plane = list(map(lambda x: x[index], array))
    positions2_plane_min = reduce(lambda x, y: x if x < y else y, positions2_plane)
    positions2_plane_max = reduce(lambda x, y: x if x > y else y, positions2_plane)
    if positions1_plane_max < positions2_plane_min or positions2_plane_max < positions1_plane_min:
        return False
    return True

def is_positions_overrap_all(positions1, positions2):
    return is_positions_overrap_on_plane(positions1, positions2, 0) \
        and is_positions_overrap_on_plane(positions1, positions2, 1) \
        and is_positions_overrap_on_plane(positions1, positions2, 2)

def is_positions_overrap_any(positions1, positions2):
    return is_positions_overrap_on_plane(positions1, positions2, 0) \
        or is_positions_overrap_on_plane(positions1, positions2, 1) \
        or is_positions_overrap_on_plane(positions1, positions2, 2)
