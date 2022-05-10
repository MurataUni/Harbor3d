from typing import Text
import math
import numpy as np
import struct

def generate_edges_from_bmp(path, additional_vertex=0):
    pixels = load_pixels(path)
    height = pixels.shape[0]
    width = pixels.shape[1]
    shorter_edge = height if height <= width else width

    edges = []
    #y=0, x正側から反時計回り
    for i in range(width//2):
        if pixels[0 + height//2][i + width//2] or pixels[-1 + height//2][i + width//2]:
            edges.append((i, 0))
            break
    
    #y=0, y=xの間
    pick_first_quadrant_small_tilt(pixels, additional_vertex, edges)

    #y=x, x正 y正
    for i in range(shorter_edge//2):
        if pixels[i + height//2][i + width//2]:
            edges.append((i, i))
            break
    
    #y=x, x=0の間
    pick_first_quadrant_large_tilt(pixels, additional_vertex, edges)
    
    #x=0, y正側
    for i in range(height//2):
        if pixels[i + height//2][width//2] or pixels[i + height//2][-1 + width//2]:
            edges.append((0, i))
            break
    
    #x=0, y=-xの間
    pick_second_quadrant_large_tilt(pixels, additional_vertex, edges)

    #y=-x, x負 y正
    for i in range(shorter_edge//2 - 1):
        if pixels[i + height//2][-(i+1) + width//2]:
            edges.append((-i, i))
            break

    #y=-x, y=0の間
    pick_second_quadrant_small_tilt(pixels, additional_vertex, edges)

    #y=0, x負側
    for i in range(width//2 - 1):
        if pixels[0 + height//2][-(i+1) + width//2] or pixels[-1 + height//2][-(i+1) + width//2]:
            edges.append((-i, 0))
            break
    
    #y=0, y=xの間
    pick_third_quadrant_small_tilt(pixels, additional_vertex, edges)

    #y=x, x負 y負
    for i in range(shorter_edge//2 -1):
        if pixels[-(i+1) + height//2][-(i+1) + width//2]:
            edges.append((-i, -i))
            break
    
    #y=x, x=0の間
    pick_third_quadrant_large_tilt(pixels, additional_vertex, edges)
    
    #x=0, y負側
    for i in range(height//2 - 1):
        if pixels[-(i+1) + height//2][width//2] or pixels[-(i+1) + height//2][-1 + width//2]:
            edges.append((0, -i))
            break
    
    #x=0, y=-xの間
    pick_fourth_quadrant_large_tilt(pixels, additional_vertex, edges)

    #y=-x, x正 y負
    for i in range(shorter_edge//2 - 1):
        if pixels[-(i+1) + height//2][i + width//2]:
            edges.append((i, -i))
            break
    
    #y=-x, y=0の間
    pick_fourth_quadrant_small_tilt(pixels, additional_vertex, edges)
    
    return edges

def pick_first_quadrant_small_tilt(pixels, vertex_count, edges):
    if vertex_count < 1:
        return
    for i in range(1, vertex_count + 1):
        tilt = np.tan((np.pi/4)*i/(vertex_count + 1))
        height = pixels.shape[0]
        width = pixels.shape[1]
        for x in range(width//2):
            y = x*tilt
            if pixels[math.floor(y) + height//2][x + width//2]:
                edges.append((x, y))
                break

def pick_first_quadrant_large_tilt(pixels, vertex_count, edges):
    if vertex_count < 1:
        return
    for i in range(1, vertex_count + 1):
        tilt = np.tan((np.pi/4)*(i/(vertex_count + 1) + 1))
        height = pixels.shape[0]
        width = pixels.shape[1]
        for y in range(height//2):
            x = y/tilt
            if pixels[y + height//2][math.floor(x) + width//2]:
                edges.append((x, y))
                break

def pick_second_quadrant_large_tilt(pixels, vertex_count, edges):
    if vertex_count < 1:
        return
    for i in reversed(range(1, vertex_count + 1)):
        tilt = np.tan(-(np.pi/4)*(i/(vertex_count + 1) + 1))
        height = pixels.shape[0]
        width = pixels.shape[1]
        for y in range(height//2 - 1):
            x = y/tilt
            if pixels[y + height//2][math.floor(x) + width//2 - 1]:
                edges.append((x, y))
                break

def pick_second_quadrant_small_tilt(pixels, vertex_count, edges):
    if vertex_count < 1:
        return
    for i in reversed(range(1, vertex_count + 1)):
        tilt = np.tan(-(np.pi/4)*i/(vertex_count + 1))
        height = pixels.shape[0]
        width = pixels.shape[1]
        for x in range(width//2 - 1):
            y = -x*tilt
            if pixels[math.floor(y) + height//2][-x + width//2 - 1]:
                edges.append((-x, y))
                break

def pick_third_quadrant_small_tilt(pixels, vertex_count, edges):
    if vertex_count < 1:
        return
    for i in range(1, vertex_count + 1):
        tilt = np.tan((np.pi/4)*i/(vertex_count + 1))
        height = pixels.shape[0]
        width = pixels.shape[1]
        for x in range(width//2 - 1):
            y = -x*tilt
            if pixels[math.floor(y) + height//2 - 1][-x + width//2 - 1]:
                edges.append((-x, y))
                break

def pick_third_quadrant_large_tilt(pixels, vertex_count, edges):
    if vertex_count < 1:
        return
    for i in range(1, vertex_count + 1):
        tilt = np.tan((np.pi/4)*(i/(vertex_count + 1) + 1))
        height = pixels.shape[0]
        width = pixels.shape[1]
        for y in range(height//2 - 1):
            x = -y/tilt
            if pixels[-y + height//2 - 1][math.floor(x) + width//2 - 1]:
                edges.append((x, -y))
                break

def pick_fourth_quadrant_large_tilt(pixels, vertex_count, edges):
    if vertex_count < 1:
        return
    for i in reversed(range(1, vertex_count + 1)):
        tilt = np.tan(-(np.pi/4)*(i/(vertex_count + 1) + 1))
        height = pixels.shape[0]
        width = pixels.shape[1]
        for y in range(height//2 - 1):
            x = -y/tilt
            if pixels[-y + height//2 - 1][math.floor(x) + width//2]:
                edges.append((x, -y))
                break

def pick_fourth_quadrant_small_tilt(pixels, vertex_count, edges):
    if vertex_count < 1:
        return
    for i in reversed(range(1, vertex_count + 1)):
        tilt = np.tan(-(np.pi/4)*i/(vertex_count + 1))
        height = pixels.shape[0]
        width = pixels.shape[1]
        for x in range(width//2 - 1):
            y = x*tilt
            if pixels[math.floor(y) + height//2 - 1][x + width//2]:
                edges.append((x, y))
                break

def load_pixels(path):
    with open(path, "rb") as f:
        read_block = f.read(14) # file header
        unpacked = struct.unpack("<xxxxxxxxxxI", read_block) # 10byte(discard) + Unsigned Int(4byte)
        bytes_pixel_start_from_top = unpacked[0]

        read_block = f.read(40) # imfomation header
        # index 0: Unsigned Int(4byte) info header size
        # index 1: Unsigned Int(4byte) width
        # index 2: Unsigned Int(4byte) height
        # discard 2byte
        # index 3: Unsigned Short(2byte) pixel data size(bit)
        # index 4: Unsigned Int(4byte) compression type
        # discard 20byte
        unpacked = struct.unpack("<IIIxxHIxxxxxxxxxxxxxxxxxxxx", read_block) 
        
        header_size = unpacked[0]
        image_width = unpacked[1]
        image_height = unpacked[2]
        pixel_data_size = unpacked[3]
        type_compression = unpacked[4]

        # 想定通りのBitmapではない時に異常終了する
        if(40 != header_size):
            raise Exception("Bitmap format error: header size")
        if(0 != image_width%32):
            raise Exception("Bitmap format error: image width")
        if(image_width != image_height):
            raise Exception("Bitmap format error: aspect ratio")
        if(1 != pixel_data_size):
            raise Exception("Bitmap format error: pixel data size, allow only 1bit")
        if(0 != type_compression):
            raise Exception("Bitmap format error: compression type, allow only no compression")
        if(14 + 40 + 8 != bytes_pixel_start_from_top):
            raise Exception("Bitmap format error: palette count, allow only 2 color")
        
        palette_white_index = None

        read_block = f.read(4) # palette 0
        unpacked = struct.unpack("<BBBx", read_block) 
        if (unpacked[0] == 255 and unpacked[1] == 255 and unpacked[2] == 255):
            palette_white_index = 0
            pass

        read_block = f.read(4) # palette 1
        unpacked = struct.unpack("<BBBx", read_block) 
        if (unpacked[0] == 255 and unpacked[1] == 255 and unpacked[2] == 255):
            palette_white_index = 1

        if (None == palette_white_index):
            raise Exception("Bitmap format error: palette doesn't contains any white")

        pixels = np.zeros((image_height, image_width), dtype = 'bool')

        for y in range(image_height):
            read_block = f.read(image_width//8)
            for x_block in range(len(read_block)):
                for bit in range(8):
                    pixels[y][x_block * 8 + bit] = ((read_block[x_block] >> (7 - bit)) & 1) != palette_white_index
        return pixels
