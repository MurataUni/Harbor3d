import os

def delete_separated_shell(sw, path, input_fname, output_fname, config_scan_start_taple):
    sw.clear_dock()
    ship = sw.load_huge_binary_stl(os.path.join(path, input_fname))
    triangles = set(ship.monocoque_shell.triangles)
    positions = set(ship.monocoque_shell.positions)
    print(len(triangles))
    print(len(positions))
    base_position = pick_base_position(ship.monocoque_shell.positions, config_scan_start_taple)

    print(base_position)

    new_positions = dict()
    new_positions[base_position.position[2]] = set([base_position])
    new_triangles = []
    count = 0
    while True:
        count = count + 1
        if 0 == count%10: print(count) 
        delete_triangles = set()
        for triangle in triangles:
            triangle_positions = set(triangle.get_positions())
            delete_flag = False
            for triangle_position in triangle_positions:
                if triangle_position.position[2] in new_positions and triangle_position in new_positions[triangle_position.position[2]]:
                    delete_flag = True
                    break
            if delete_flag:
                for triangle_position in triangle_positions:
                    if triangle_position.position[2] in new_positions:
                        new_positions[triangle_position.position[2]].add(triangle_position)
                    else:
                        new_positions[triangle_position.position[2]] = set([triangle_position])
                delete_triangles.add(triangle)
        if 0 != len(delete_triangles):
            new_triangles.extend(list(delete_triangles))
            triangles = triangles - delete_triangles
        else:
            break

    ship.monocoque_shell.triangles = new_triangles
    ship.monocoque_shell.positions = []
    for position_set in new_positions.values():
      ship.monocoque_shell.positions.extend(list(position_set))  

    sw.generate_stl_binary(path, output_fname, divided=False)

def pick_base_position(positions, config_scan_start_taple):
    return_position = positions[0]
    for position in positions:
        if config_scan_start_taple[0] < 0:
            if position.position[0] < return_position.position[0]:
                return_position = position
        elif 0 < config_scan_start_taple[0]:
            if return_position.position[0] < position.position[0]:
                return_position = position
        elif config_scan_start_taple[1] < 0:
            if position.position[1] < return_position.position[1]:
                return_position = position
        elif 0 < config_scan_start_taple[1]:
            if return_position.position[1] < position.position[1]:
                return_position = position
        elif config_scan_start_taple[2] < 0:
            if position.position[2] < return_position.position[2]:
                return_position = position
        elif 0 < config_scan_start_taple[2]:
            if return_position.position[2] < position.position[2]:
                return_position = position
    return return_position
