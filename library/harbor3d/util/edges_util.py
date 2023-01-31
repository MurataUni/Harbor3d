import numpy as np

def center(edges):
    size_info = size(edges)
    return ((size_info[0][1]+size_info[0][0])/2, (size_info[1][1]+size_info[1][0])/2)

def size(edges):
    x_min = edges[0][0]
    x_max = edges[0][0]
    y_min = edges[0][1]
    y_max = edges[0][1]
    for edge in edges:
        if edge[0] < x_min:
            x_min = edge[0]
        if edge[0] > x_max:
            x_max = edge[0]
        if edge[1] < y_min:
            y_min = edge[1]
        if edge[1] > y_max:
            y_max = edge[1]
    return ((x_min, x_max),(y_min, y_max))

def length(edges):
    ((x_min, x_max),(y_min, y_max)) = size(edges)
    return (x_max-x_min, y_max-y_min)

def scale(edges, scale):
    if scale is None:
        return edges
    return list(map(lambda t: tuple([t[0]*scale, t[1]*scale]), edges))

def translate(edges, x=0., y=0.):
    return list(map(lambda t: tuple([t[0] + x, t[1] + y]), edges))

def mirror(edges, plane):
    if plane is None:
        return edges
    if len(edges)%4 != 0:
        raise Exception("edges format error: count")
    count_per_quadrant = len(edges)//4
    first_edge = edges[count_per_quadrant*0]
    second_edge = edges[count_per_quadrant*1]
    third_edge = edges[count_per_quadrant*2]
    fourth_edge = edges[count_per_quadrant*3]

    first_path = edges[count_per_quadrant*0+1:count_per_quadrant*1]
    second_path = edges[count_per_quadrant*1+1:count_per_quadrant*2]
    third_path = edges[count_per_quadrant*2+1:count_per_quadrant*3]
    fourth_path = edges[count_per_quadrant*3+1:count_per_quadrant*4]

    mirrored_edges = []
    # first quadrant
    if plane == 2:
        mirrored_edges.append(tuple([third_edge[0]*-1, third_edge[1]]))
        mirrored_edges.extend(reversed(inversion(second_path, x=True)))
    elif plane == 3:
        mirrored_edges.append(first_edge)
        mirrored_edges.extend(reversed(inversion(fourth_path, y=True)))
    else:
        mirrored_edges.append(first_edge)
        mirrored_edges.extend(first_path)
    
    # second quadrant
    if plane == 3:
        mirrored_edges.append(tuple([fourth_edge[0], fourth_edge[1]*-1]))
        mirrored_edges.extend(reversed(inversion(third_path, y=True)))
    elif plane == 0:
        mirrored_edges.append(second_edge)
        mirrored_edges.extend(reversed(inversion(first_path, x=True)))
    else:
        mirrored_edges.append(second_edge)
        mirrored_edges.extend(second_path)
    
    # third quadrant
    if plane == 0:
        mirrored_edges.append(tuple([first_edge[0]*-1, first_edge[1]]))
        mirrored_edges.extend(reversed(inversion(fourth_path, x=True)))
    elif plane == 1:
        mirrored_edges.append(third_edge)
        mirrored_edges.extend(reversed(inversion(second_path, y=True)))
    else:
        mirrored_edges.append(third_edge)
        mirrored_edges.extend(third_path)
    
    # fourth quadrant
    if plane == 1:
        mirrored_edges.append(tuple([second_edge[0], second_edge[1]*-1]))
        mirrored_edges.extend(reversed(inversion(first_path, y=True)))
    elif plane == 2:
        mirrored_edges.append(fourth_edge)
        mirrored_edges.extend(reversed(inversion(third_path, x=True)))
    else:
        mirrored_edges.append(fourth_edge)
        mirrored_edges.extend(fourth_path)
    
    return mirrored_edges

def inversion(edges, x=False, y=False):
    return list(map(lambda t: tuple([t[0]*-1 if x else t[0], t[1]*-1 if y else t[1]]), edges))

