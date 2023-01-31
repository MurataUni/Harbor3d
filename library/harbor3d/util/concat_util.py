from dataclasses import dataclass, field

import numpy as np
import sys, struct
from typing import List, Dict, Any

from harbor3d import Shipwright
from harbor3d.util import load_util, calc_util
from harbor3d.util.model_util import Facet

@dataclass
class ConcatConfig:
    xy_plane_interval:float
    stage_pitch:float
    x_offset:float = 0.
    y_offset:float = 0.
    stage_pitch_offset:float = 0.
    merge_consecutive_face:bool = True
    recalc_z_bias:float = 0.
    recalc_x_bias:float = 0.

    def __post_init__(self):
        if self.recalc_z_bias == 0.:
            self.recalc_z_bias = self.stage_pitch/100.
        if self.recalc_x_bias == 0.:
            self.recalc_x_bias = self.xy_plane_interval/100.
    
    def stage_position(self, index):
        return self.stage_pitch_offset + self.stage_pitch*index
    
    def x_position(self, index):
        return self.x_offset + self.xy_plane_interval*index
    
    def y_position(self, index):
        return self.y_offset + self.xy_plane_interval*index
    
    def stage_index_range(self, z_min, z_max):
        z_min_float = z_min-self.stage_pitch_offset
        z_max_float = z_max-self.stage_pitch_offset
        return float_to_int_range_included(z_min_float, z_max_float, self.stage_pitch)

@dataclass
class ShellData:
    catConfig:ConcatConfig
    sw:Shipwright
    path:str
    area_info:tuple = None
    triangles:List[Any] = field(default_factory=list)
    penetrate_dict_key_stage:dict = field(default_factory=dict)

    def __post_init__(self):
        self.fetch_area(self.path)

    def fetch_triangles(self):
        self.sw.clear_dock()
        ship = self.sw.load_stl(self.path)
        self.triangles = ship.monocoque_shell.triangles
    
    def fetch_area(self, stl_full_path):
        vertexes = load_util.load_vertexes(stl_full_path)

        x_min = sys.float_info.max
        x_max = -sys.float_info.max
        y_min = sys.float_info.max
        y_max = -sys.float_info.max
        z_min = sys.float_info.max
        z_max = -sys.float_info.max

        for vertex in vertexes:
            if x_min > vertex[0]:
                x_min = vertex[0]
            if x_max < vertex[0]:
                x_max = vertex[0]

            if y_min > vertex[1]:
                y_min = vertex[1]
            if y_max < vertex[1]:
                y_max = vertex[1]

            if z_min > vertex[2]:
                z_min = vertex[2]
            if z_max < vertex[2]:
                z_max = vertex[2]
        
        self.area_info = ((x_min, x_max), (y_min, y_max), (z_min, z_max))
        
    def x_min(self):
        return self.area_info[0][0]
    
    def x_max(self):
        return self.area_info[0][1]

    def y_min(self):
        return self.area_info[1][0]
    
    def y_max(self):
        return self.area_info[1][1]

    def z_min(self):
        return self.area_info[2][0]
    
    def z_max(self):
        return self.area_info[2][1]

    def is_included_in_z_area(self, z):
        return self.z_min() <= z and z <= self.z_max()
    
    def is_included_in_x_area(self, x):
        return self.x_min() <= x and x <= self.x_max()
    
    def scan_x_index_range(self):
        x_min_float = self.x_min()-self.catConfig.x_offset
        x_max_float = self.x_max()-self.catConfig.x_offset
        scale = self.catConfig.xy_plane_interval
        return float_to_int_range_included(x_min_float, x_max_float, scale)

@dataclass
class Concatinator:
    catConfig:ConcatConfig
    sw:Shipwright
    shells_path:List[str] = field(default_factory=list)
    shells:List[ShellData] = field(default_factory=list)
    z_range:tuple = None
    dict_stage_array:Dict = field(default_factory=dict)
    dict_array_xp_union:Dict = field(default_factory=dict)
    dict_array_xm_union:Dict = field(default_factory=dict)
    dict_array_yp_union:Dict = field(default_factory=dict)
    dict_array_ym_union:Dict = field(default_factory=dict)
    default_stage_array:np.ndarray = np.array([])
    stage_array_offset_x_index:int = 0
    stage_array_offset_y_index:int = 0
    x_max:float = field(default=-sys.float_info.max)
    x_min:float = field(default=sys.float_info.max)
    y_max:float = field(default=-sys.float_info.max)
    y_min:float = field(default=sys.float_info.max)
    triangle_count:int = 0

    def x_position(self, stage_array_index):
        scale = self.catConfig.xy_plane_interval
        return (stage_array_index + self.stage_array_offset_x_index) * scale + self.catConfig.x_offset

    def y_position(self, stage_array_index):
        scale = self.catConfig.xy_plane_interval
        return (stage_array_index + self.stage_array_offset_y_index) * scale + self.catConfig.y_offset
    
    def init_shells_data(self, list_path):
        self.shells_path = list_path
        for path in list_path:
            shell = ShellData(self.catConfig, self.sw, path)
            self.shells.append(shell)
            print(path)
        self.z_range = self.fetch_z_range()
    
    def stage_index_range(self):
        return self.catConfig.stage_index_range(self.z_range[0], self.z_range[1])
    
    def generate_stage_array(self, x_range_max_index, y_ragne_max_index):
        return np.zeros((x_range_max_index, y_ragne_max_index), dtype='u1')

    def set_stage_default_array(self):
        scale = self.catConfig.xy_plane_interval
        x_min_float = self.x_min-self.catConfig.x_offset
        x_max_float = self.x_max-self.catConfig.x_offset
        x_min_index, x_max_index = float_to_int_range_included(x_min_float, x_max_float, scale)
        x_range = x_max_index - x_min_index + 1 + 2

        y_min_float = self.y_min-self.catConfig.y_offset
        y_max_float = self.y_max-self.catConfig.y_offset
        y_min_index, y_max_index = float_to_int_range_included(y_min_float, y_max_float, scale)
        y_range = y_max_index - y_min_index + 1 + 2

        self.stage_array_offset_x_index = x_min_index - 1
        self.stage_array_offset_y_index = y_min_index - 1
        self.default_stage_array = self.generate_stage_array(x_range, y_range)
        print("x_range:", x_range, ", y_range:", y_range)
    
    def set_stage_dict(self, target_stage_index):
        # notice: this function expected to be called incrementally
        delete_target_keys = []
        for key in self.dict_stage_array:
            if key < target_stage_index-1:
                delete_target_keys.append(key)
        for taeget_key in delete_target_keys:
            del self.dict_stage_array[taeget_key]
        
        if not target_stage_index-1 in self.dict_stage_array:
            self.dict_stage_array[target_stage_index-1] = np.copy(self.default_stage_array)
        if not target_stage_index in self.dict_stage_array:
            self.dict_stage_array[target_stage_index] = np.copy(self.default_stage_array)
        for i in range(1,10):
            if not target_stage_index+i in self.dict_stage_array:
                self.dict_stage_array[target_stage_index+i] = np.copy(self.default_stage_array)
                self.load_penetration_data_to_stage_array(target_stage_index+i)
    
    def load_penetration_data_to_stage_array(self, target_stage_index):
        if not target_stage_index in self.dict_stage_array:
            return
        stage_array = self.dict_stage_array[target_stage_index]
        for shell in self.shells:
            if not target_stage_index in shell.penetrate_dict_key_stage:
                continue
            penetrate_data = shell.penetrate_dict_key_stage[target_stage_index]
            for stage_array_x_index in range(1,stage_array.shape[0]-1):
                penetration_dict_x_index = stage_array_x_index + self.stage_array_offset_x_index
                if not penetration_dict_x_index in penetrate_data:
                    continue
                list_penetration = sorted(penetrate_data[penetration_dict_x_index])
                for list_penetration_index in range(0,len(list_penetration),2):
                    start = list_penetration[list_penetration_index]-self.catConfig.xy_plane_interval/2
                    end = list_penetration[list_penetration_index+1]+self.catConfig.xy_plane_interval/2
                    # print("start:", start, ", end:", end)
                    for stage_array_y_index in range(1,stage_array.shape[1]-1):
                        y_pos = self.y_position(stage_array_y_index)
                        if start <= y_pos and y_pos <= end:
                            OutputFlag.set_exist(stage_array, stage_array_x_index, stage_array_y_index)
    
    def border_data_load(self):
        stage_min_index, stage_max_index = self.catConfig.stage_index_range(self.z_range[0], self.z_range[1])
        print("stage_min_i:", stage_min_index)
        print("stage_max_i:", stage_max_index)

        for stage_index in range(stage_min_index, stage_max_index + 1):
            stage = self.catConfig.stage_position(stage_index)
            for shellData in self.shells:
                if not shellData.is_included_in_z_area(stage):
                    if shellData.z_max() < stage and 0 != len(shellData.triangles):
                        shellData.triangles = []
                    continue
                if 0 == len(shellData.triangles):
                    shellData.fetch_triangles()
                    # memorize range min, max
                    if self.x_max < shellData.x_max() : self.x_max = shellData.x_max()
                    if shellData.x_min() < self.x_min : self.x_min = shellData.x_min()
                    if self.y_max < shellData.y_max() : self.y_max = shellData.y_max()
                    if shellData.y_min() < self.y_min : self.y_min = shellData.y_min()
                x_scan_min_index, x_scan_max_index = shellData.scan_x_index_range()
                y_shell_length = shellData.y_max() - shellData.y_min()
                y_start = shellData.y_min() - y_shell_length/10.
                y_vector = np.array([0., y_shell_length*1.2, 0.])
                for x_scan_index in range(x_scan_min_index, x_scan_max_index + 1):
                    x_scan = self.catConfig.x_position(x_scan_index)
                    y_start_pos = np.array([x_scan, y_start, stage])
                    list_penetration = calc_penetration_y_axis_pararell(shellData.triangles, y_start_pos, y_vector)

                    if len(list_penetration)%2 != 0:
                        y_start_pos[2] = y_start_pos[2] + self.catConfig.recalc_z_bias
                        list_penetration = calc_penetration_y_axis_pararell(shellData.triangles, y_start_pos, y_vector)
                    
                    if len(list_penetration)%2 != 0:
                        y_start_pos[0] = y_start_pos[0] + self.catConfig.recalc_x_bias
                        list_penetration = calc_penetration_y_axis_pararell(shellData.triangles, y_start_pos, y_vector)
                    
                    if len(list_penetration)%2 != 0:
                        raise Exception()

                    if None == list_penetration or 0 == len(list_penetration):
                        continue
                    if stage_index in shellData.penetrate_dict_key_stage:
                        dict_key_stage = shellData.penetrate_dict_key_stage[stage_index]
                        if x_scan_index in dict_key_stage:
                            dict_key_stage[x_scan_index].extend(list_penetration)
                        else:
                            dict_key_stage[x_scan_index] = list_penetration
                    else:
                        shellData.penetrate_dict_key_stage[stage_index] = {x_scan_index: list_penetration}
        self.set_stage_default_array()
    
    def output(self, outfile_fullpath):
        # write temp data
        with open(outfile_fullpath + "_temp", "wb") as f:
            # write triangles data
            stage_min_index, stage_max_index = self.stage_index_range()
            for stage_index in range(stage_min_index-10, stage_max_index+1):
                print("stage index:", stage_index)
                self.write_concat(stage_index, f)

        # write full data
        with open(outfile_fullpath, "wb") as f:
            # 80Byte padding
            for i in range(8):
                f.write(struct.pack("xxxxxxxxxx"))
            
            # count triangles
            f.write(struct.pack("<L", self.triangle_count))

            # write triangles data
            with open(outfile_fullpath + "_temp", "rb") as f_read:
                while True:
                    read_block = f_read.read(50)
                    if len(read_block) != 50:
                        break
                    f.write(read_block)
    
    def write_concat(self, stage_index, f):
        self.set_stage_dict(stage_index)
        self.calc_stage(stage_index)
        self.union_panel_xy(stage_index, self.catConfig)
        self.write_stage_xy(stage_index, f)
        self.write_stage_z(stage_index, f, self.catConfig)

    def calc_stage(self, stage_index):
        upper9_s = self.dict_stage_array[stage_index+9]
        upper8_s = self.dict_stage_array[stage_index+8]
        upper7_s = self.dict_stage_array[stage_index+7]
        upper6_s = self.dict_stage_array[stage_index+6]
        upper5_s = self.dict_stage_array[stage_index+5]
        upper4_s = self.dict_stage_array[stage_index+4]
        
        while self.modify_stage_corner_inter_plane(upper8_s, upper9_s)\
            or self.modify_stage_blank_corner_inter_plane(upper8_s, upper9_s)\
            or self.modify_stage_side_inter_plane(upper8_s, upper9_s)\
            or self.modify_stage_plane(upper9_s)\
            or self.modify_stage_plane(upper8_s): pass
        
        while self.modify_stage_fill(upper6_s, upper7_s, upper8_s): pass

        for x_i in range(upper5_s.shape[0]):
            for y_i in range(upper5_s.shape[1]):
                if OutputFlag.is_exist(upper5_s, x_i, y_i):
                    if not OutputFlag.is_exist(upper5_s, x_i-1, y_i):
                       OutputFlag.set_x_m_side(upper5_s, x_i, y_i)
                    
                    if not OutputFlag.is_exist(upper5_s, x_i+1, y_i):
                       OutputFlag.set_x_p_side(upper5_s, x_i, y_i)
                    
                    if not OutputFlag.is_exist(upper5_s, x_i, y_i-1):
                       OutputFlag.set_y_m_side(upper5_s, x_i, y_i)
                    
                    if not OutputFlag.is_exist(upper5_s, x_i, y_i+1):
                       OutputFlag.set_y_p_side(upper5_s, x_i, y_i)
                    
                    if not OutputFlag.is_exist(upper6_s, x_i, y_i):
                       OutputFlag.set_z_p_side(upper5_s, x_i, y_i)
                    
                    if not OutputFlag.is_exist(upper4_s, x_i, y_i):
                       OutputFlag.set_z_m_side(upper5_s, x_i, y_i)
    
    def modify_stage_plane(self, upper_s):
        modified = False
        for x_i in range(1, upper_s.shape[0]-1):
            for y_i in range(1, upper_s.shape[1]-1):
                u_center = OutputFlag.is_exist(upper_s, x_i, y_i)
                if not u_center: continue
                u_corner_xp_yp = OutputFlag.is_exist(upper_s, x_i+1, y_i+1)
                u_corner_xp_ym = OutputFlag.is_exist(upper_s, x_i+1, y_i-1)
                u_corner_xm_yp = OutputFlag.is_exist(upper_s, x_i-1, y_i+1)
                u_corner_xm_ym = OutputFlag.is_exist(upper_s, x_i-1, y_i-1)

                u_side_xp = OutputFlag.is_exist(upper_s, x_i+1, y_i)
                u_side_xm = OutputFlag.is_exist(upper_s, x_i-1, y_i)
                u_side_yp = OutputFlag.is_exist(upper_s, x_i, y_i+1)
                u_side_ym = OutputFlag.is_exist(upper_s, x_i, y_i-1)

                if u_corner_xp_yp and (not u_side_xp and not u_side_yp):
                    OutputFlag.set_exist(upper_s, x_i+1, y_i)
                    OutputFlag.set_exist(upper_s, x_i, y_i+1)
                    modified = True
                
                if u_corner_xp_ym and (not u_side_xp and not u_side_ym):
                    OutputFlag.set_exist(upper_s, x_i+1, y_i)
                    OutputFlag.set_exist(upper_s, x_i, y_i-1)
                    modified = True

                if u_corner_xm_yp and (not u_side_xm and not u_side_yp):
                    OutputFlag.set_exist(upper_s, x_i-1, y_i)
                    OutputFlag.set_exist(upper_s, x_i, y_i+1)
                    modified = True
                
                if u_corner_xm_ym and (not u_side_xm and not u_side_ym):
                    OutputFlag.set_exist(upper_s, x_i-1, y_i)
                    OutputFlag.set_exist(upper_s, x_i, y_i-1)
                    modified = True
        return modified

    def modify_stage_side_inter_plane(self, current_s, upper_s):
        modified = False
        for x_i in range(1, upper_s.shape[0]-1):
            for y_i in range(1, upper_s.shape[1]-1):
                u_center = OutputFlag.is_exist(upper_s, x_i, y_i)
                if not u_center: continue
                u_side_xp = OutputFlag.is_exist(upper_s, x_i+1, y_i)
                u_side_xm = OutputFlag.is_exist(upper_s, x_i-1, y_i)
                u_side_yp = OutputFlag.is_exist(upper_s, x_i, y_i+1)
                u_side_ym = OutputFlag.is_exist(upper_s, x_i, y_i-1)

                c_center = OutputFlag.is_exist(current_s, x_i, y_i)
                c_side_xp = OutputFlag.is_exist(current_s, x_i+1, y_i)
                c_side_xm = OutputFlag.is_exist(current_s, x_i-1, y_i)
                c_side_yp = OutputFlag.is_exist(current_s, x_i, y_i+1)
                c_side_ym = OutputFlag.is_exist(current_s, x_i, y_i-1)

                if c_side_xp and (not u_side_xp and not c_center):
                    OutputFlag.set_exist(upper_s, x_i+1, y_i)
                    OutputFlag.set_exist(current_s, x_i, y_i)
                    modified = True
                
                if c_side_xm and (not u_side_xm and not c_center):
                    OutputFlag.set_exist(upper_s, x_i-1, y_i)
                    OutputFlag.set_exist(current_s, x_i, y_i)
                    modified = True

                if c_side_yp and (not u_side_yp and not c_center):
                    OutputFlag.set_exist(upper_s, x_i, y_i+1)
                    OutputFlag.set_exist(current_s, x_i, y_i)
                    modified = True
                
                if c_side_ym and (not u_side_ym and not c_center):
                    OutputFlag.set_exist(upper_s, x_i, y_i-1)
                    OutputFlag.set_exist(current_s, x_i, y_i)
                    modified = True
        return modified

    def modify_stage_corner_inter_plane(self, current_s, upper_s):
        modified = False
        for x_i in range(1, upper_s.shape[0]-1):
            for y_i in range(1, upper_s.shape[1]-1):
                u_center = OutputFlag.is_exist(upper_s, x_i, y_i)
                if not u_center: continue
                u_corner_xp_yp = OutputFlag.is_exist(upper_s, x_i+1, y_i+1)
                u_corner_xp_ym = OutputFlag.is_exist(upper_s, x_i+1, y_i-1)
                u_corner_xm_yp = OutputFlag.is_exist(upper_s, x_i-1, y_i+1)
                u_corner_xm_ym = OutputFlag.is_exist(upper_s, x_i-1, y_i-1)
                u_side_xp = OutputFlag.is_exist(upper_s, x_i+1, y_i)
                u_side_xm = OutputFlag.is_exist(upper_s, x_i-1, y_i)
                u_side_yp = OutputFlag.is_exist(upper_s, x_i, y_i+1)
                u_side_ym = OutputFlag.is_exist(upper_s, x_i, y_i-1)

                c_center = OutputFlag.is_exist(current_s, x_i, y_i)
                c_corner_xp_yp = OutputFlag.is_exist(current_s, x_i+1, y_i+1)
                c_corner_xp_ym = OutputFlag.is_exist(current_s, x_i+1, y_i-1)
                c_corner_xm_yp = OutputFlag.is_exist(current_s, x_i-1, y_i+1)
                c_corner_xm_ym = OutputFlag.is_exist(current_s, x_i-1, y_i-1)
                c_side_xp = OutputFlag.is_exist(current_s, x_i+1, y_i)
                c_side_xm = OutputFlag.is_exist(current_s, x_i-1, y_i)
                c_side_yp = OutputFlag.is_exist(current_s, x_i, y_i+1)
                c_side_ym = OutputFlag.is_exist(current_s, x_i, y_i-1)

                if c_corner_xp_yp and (\
                        (not c_side_xp and not u_side_xp) and (not c_side_yp and not u_side_yp) and\
                        (not c_center and not c_side_xp) and (not c_center and not c_side_yp) and\
                        (not u_corner_xp_yp and not u_side_xp) and (not u_corner_xp_yp and not u_side_yp)):
                    OutputFlag.set_exist(upper_s, x_i+1, y_i+1)
                    OutputFlag.set_exist(upper_s, x_i+1, y_i)
                    OutputFlag.set_exist(upper_s, x_i, y_i+1)
                    OutputFlag.set_exist(current_s, x_i, y_i)
                    OutputFlag.set_exist(current_s, x_i+1, y_i)
                    OutputFlag.set_exist(current_s, x_i, y_i+1)
                    modified = True
                
                if c_corner_xp_ym and (\
                        (not c_side_xp and not u_side_xp) and (not c_side_ym and not u_side_ym) and\
                        (not c_center and not c_side_xp) and (not c_center and not c_side_ym) and\
                        (not u_corner_xp_ym and not u_side_xp) and (not u_corner_xp_ym and not u_side_ym)):
                    OutputFlag.set_exist(upper_s, x_i+1, y_i-1)
                    OutputFlag.set_exist(upper_s, x_i+1, y_i)
                    OutputFlag.set_exist(upper_s, x_i, y_i-1)
                    OutputFlag.set_exist(current_s, x_i, y_i)
                    OutputFlag.set_exist(current_s, x_i+1, y_i)
                    OutputFlag.set_exist(current_s, x_i, y_i-1)
                    modified = True
                
                if c_corner_xm_yp and (\
                        (not c_side_xm and not u_side_xm) and (not c_side_yp and not u_side_yp) and\
                        (not c_center and not c_side_xm) and (not c_center and not c_side_yp) and\
                        (not u_corner_xm_yp and not u_side_xm) and (not u_corner_xm_yp and not u_side_yp)):
                    OutputFlag.set_exist(upper_s, x_i-1, y_i+1)
                    OutputFlag.set_exist(upper_s, x_i-1, y_i)
                    OutputFlag.set_exist(upper_s, x_i, y_i+1)
                    OutputFlag.set_exist(current_s, x_i, y_i)
                    OutputFlag.set_exist(current_s, x_i-1, y_i)
                    OutputFlag.set_exist(current_s, x_i, y_i+1)
                    modified = True
                
                if c_corner_xm_ym and (\
                        (not c_side_xm and not u_side_xm) and (not c_side_ym and not u_side_ym) and\
                        (not c_center and not c_side_xm) and (not c_center and not c_side_ym) and\
                        (not u_corner_xp_ym and not u_side_xm) and (not u_corner_xm_ym and not u_side_ym)):
                    OutputFlag.set_exist(upper_s, x_i-1, y_i-1)
                    OutputFlag.set_exist(upper_s, x_i-1, y_i)
                    OutputFlag.set_exist(upper_s, x_i, y_i-1)
                    OutputFlag.set_exist(current_s, x_i, y_i)
                    OutputFlag.set_exist(current_s, x_i-1, y_i)
                    OutputFlag.set_exist(current_s, x_i, y_i-1)
                    modified = True
        return modified

    def modify_stage_blank_corner_inter_plane(self, current_s, upper_s):
        modified = False
        for x_i in range(1, upper_s.shape[0]-1):
            for y_i in range(1, upper_s.shape[1]-1):
                u_center = OutputFlag.is_exist(upper_s, x_i, y_i)
                if u_center: continue
                c_center = OutputFlag.is_exist(current_s, x_i, y_i)
                if not c_center: continue
                u_corner_xp_yp = OutputFlag.is_exist(upper_s, x_i+1, y_i+1)
                u_corner_xp_ym = OutputFlag.is_exist(upper_s, x_i+1, y_i-1)
                u_corner_xm_yp = OutputFlag.is_exist(upper_s, x_i-1, y_i+1)
                u_corner_xm_ym = OutputFlag.is_exist(upper_s, x_i-1, y_i-1)
                u_side_xp = OutputFlag.is_exist(upper_s, x_i+1, y_i)
                u_side_xm = OutputFlag.is_exist(upper_s, x_i-1, y_i)
                u_side_yp = OutputFlag.is_exist(upper_s, x_i, y_i+1)
                u_side_ym = OutputFlag.is_exist(upper_s, x_i, y_i-1)

                c_corner_xp_yp = OutputFlag.is_exist(current_s, x_i+1, y_i+1)
                c_corner_xp_ym = OutputFlag.is_exist(current_s, x_i+1, y_i-1)
                c_corner_xm_yp = OutputFlag.is_exist(current_s, x_i-1, y_i+1)
                c_corner_xm_ym = OutputFlag.is_exist(current_s, x_i-1, y_i-1)
                c_side_xp = OutputFlag.is_exist(current_s, x_i+1, y_i)
                c_side_xm = OutputFlag.is_exist(current_s, x_i-1, y_i)
                c_side_yp = OutputFlag.is_exist(current_s, x_i, y_i+1)
                c_side_ym = OutputFlag.is_exist(current_s, x_i, y_i-1)

                if not c_corner_xp_yp\
                and c_side_xp and u_side_xp and c_side_yp and u_side_yp and u_corner_xp_yp:
                    OutputFlag.set_exist(current_s, x_i+1, y_i+1)
                    OutputFlag.set_exist(upper_s, x_i, y_i)
                    modified = True
                
                if not c_corner_xp_ym\
                and c_side_xp and u_side_xp and c_side_ym and u_side_ym and u_corner_xp_ym:
                    OutputFlag.set_exist(current_s, x_i+1, y_i-1)
                    OutputFlag.set_exist(upper_s, x_i, y_i)
                    modified = True
                
                if not c_corner_xm_yp\
                and c_side_xm and u_side_xm and c_side_yp and u_side_yp and u_corner_xm_yp:
                    OutputFlag.set_exist(current_s, x_i-1, y_i+1)
                    OutputFlag.set_exist(upper_s, x_i, y_i)
                    modified = True
                
                if not c_corner_xm_ym\
                and c_side_xm and u_side_xm and c_side_ym and u_side_ym and u_corner_xm_ym:
                    OutputFlag.set_exist(current_s, x_i-1, y_i-1)
                    OutputFlag.set_exist(upper_s, x_i, y_i)
                    modified = True
        return modified
    
    def modify_stage_fill(self, lower_s, current_s, upper_s):
        modified = False
        for x_i in range(1, upper_s.shape[0]-1):
            for y_i in range(1, upper_s.shape[1]-1):
                c_center = OutputFlag.is_exist(current_s, x_i, y_i)
                if c_center: continue
                
                u_center = OutputFlag.is_exist(current_s, x_i, y_i)
                l_center = OutputFlag.is_exist(lower_s, x_i, y_i)

                c_side_xp = OutputFlag.is_exist(current_s, x_i+1, y_i)
                c_side_xm = OutputFlag.is_exist(current_s, x_i-1, y_i)
                c_side_yp = OutputFlag.is_exist(current_s, x_i, y_i+1)
                c_side_ym = OutputFlag.is_exist(current_s, x_i, y_i-1)

                count = 0
                if u_center: count = count + 1
                if l_center: count = count + 1
                if c_side_xp: count = count + 1
                if c_side_xm: count = count + 1
                if c_side_yp: count = count + 1
                if c_side_ym: count = count + 1

                if 3 < count:
                    OutputFlag.set_exist(current_s, x_i, y_i)
                    modified = True
        return modified

    def union_panel_xy(self, stage_index, catConfig: ConcatConfig):
        delete_index = []
        for index in self.dict_stage_array.keys():
            if index < stage_index-1:
                delete_index.append(index)
        for index in delete_index:
            del self.dict_stage_array[index]
        if 0 != stage_index%3:
            return
        upper3_s = self.dict_stage_array[stage_index+3]
        upper4_s = self.dict_stage_array[stage_index+4]
        upper5_s = self.dict_stage_array[stage_index+5]
        
        if stage_index+3 not in self.dict_array_xp_union:
            self.dict_array_xp_union[stage_index+3] = np.copy(self.default_stage_array)
        union_xp_s3 = self.dict_array_xp_union[stage_index+3]
        
        if stage_index+4 not in self.dict_array_xp_union:
            self.dict_array_xp_union[stage_index+4] = np.copy(self.default_stage_array)
        union_xp_s4 = self.dict_array_xp_union[stage_index+4]

        if stage_index+5 not in self.dict_array_xp_union:
            self.dict_array_xp_union[stage_index+5] = np.copy(self.default_stage_array)
        union_xp_s5 = self.dict_array_xp_union[stage_index+5]

        if not catConfig.merge_consecutive_face:
            return
        
        for x_i in range(upper3_s.shape[0]):
            for y_i in range(0,upper3_s.shape[1],3):
                if OutputFlag.is_exist_range_all_side(upper3_s, x_i, x_i, y_i, y_i+2, OutputFlag.flag_x_p_side)\
                    and OutputFlag.is_exist_range_all_side(upper4_s, x_i, x_i, y_i, y_i+2, OutputFlag.flag_x_p_side)\
                    and OutputFlag.is_exist_range_all_side(upper5_s, x_i, x_i, y_i, y_i+2, OutputFlag.flag_x_p_side):
                    UnionFlag.set_base_corner_p(union_xp_s3, x_i, y_i)
                    UnionFlag.set_internal_p(union_xp_s3, x_i, y_i+1)
                    UnionFlag.set_internal_p(union_xp_s3, x_i, y_i+2)
                    UnionFlag.set_internal_p(union_xp_s4, x_i, y_i)
                    UnionFlag.set_internal_p(union_xp_s4, x_i, y_i+1)
                    UnionFlag.set_internal_p(union_xp_s4, x_i, y_i+2)
                    UnionFlag.set_internal_p(union_xp_s5, x_i, y_i)
                    UnionFlag.set_internal_p(union_xp_s5, x_i, y_i+1)
                    UnionFlag.set_internal_p(union_xp_s5, x_i, y_i+2)
                
                if OutputFlag.is_exist_range_all_side(upper3_s, x_i, x_i, y_i, y_i+2, OutputFlag.flag_x_m_side)\
                    and OutputFlag.is_exist_range_all_side(upper4_s, x_i, x_i, y_i, y_i+2, OutputFlag.flag_x_m_side)\
                    and OutputFlag.is_exist_range_all_side(upper5_s, x_i, x_i, y_i, y_i+2, OutputFlag.flag_x_m_side):
                    UnionFlag.set_base_corner_m(union_xp_s3, x_i, y_i)
                    UnionFlag.set_internal_m(union_xp_s3, x_i, y_i+1)
                    UnionFlag.set_internal_m(union_xp_s3, x_i, y_i+2)
                    UnionFlag.set_internal_m(union_xp_s4, x_i, y_i)
                    UnionFlag.set_internal_m(union_xp_s4, x_i, y_i+1)
                    UnionFlag.set_internal_m(union_xp_s4, x_i, y_i+2)
                    UnionFlag.set_internal_m(union_xp_s5, x_i, y_i)
                    UnionFlag.set_internal_m(union_xp_s5, x_i, y_i+1)
                    UnionFlag.set_internal_m(union_xp_s5, x_i, y_i+2)
        
        for x_i in range(0,upper3_s.shape[0],3):
            for y_i in range(upper3_s.shape[1]):
                if OutputFlag.is_exist_range_all_side(upper3_s, x_i, x_i+2, y_i, y_i, OutputFlag.flag_y_p_side)\
                    and OutputFlag.is_exist_range_all_side(upper4_s, x_i, x_i+2, y_i, y_i, OutputFlag.flag_y_p_side)\
                    and OutputFlag.is_exist_range_all_side(upper5_s, x_i, x_i+2, y_i, y_i, OutputFlag.flag_y_p_side):
                    UnionFlag.set_f2_base_corner_p(union_xp_s3, x_i, y_i)
                    UnionFlag.set_f2_internal_p(union_xp_s3, x_i+1, y_i)
                    UnionFlag.set_f2_internal_p(union_xp_s3, x_i+2, y_i)
                    UnionFlag.set_f2_internal_p(union_xp_s4, x_i, y_i)
                    UnionFlag.set_f2_internal_p(union_xp_s4, x_i+1, y_i)
                    UnionFlag.set_f2_internal_p(union_xp_s4, x_i+2, y_i)
                    UnionFlag.set_f2_internal_p(union_xp_s5, x_i, y_i)
                    UnionFlag.set_f2_internal_p(union_xp_s5, x_i+1, y_i)
                    UnionFlag.set_f2_internal_p(union_xp_s5, x_i+2, y_i)
                
                if OutputFlag.is_exist_range_all_side(upper3_s, x_i, x_i+2, y_i, y_i, OutputFlag.flag_y_m_side)\
                    and OutputFlag.is_exist_range_all_side(upper4_s, x_i, x_i+2, y_i, y_i, OutputFlag.flag_y_m_side)\
                    and OutputFlag.is_exist_range_all_side(upper5_s, x_i, x_i+2, y_i, y_i, OutputFlag.flag_y_m_side):
                    UnionFlag.set_f2_base_corner_m(union_xp_s3, x_i, y_i)
                    UnionFlag.set_f2_internal_m(union_xp_s3, x_i+1, y_i)
                    UnionFlag.set_f2_internal_m(union_xp_s3, x_i+2, y_i)
                    UnionFlag.set_f2_internal_m(union_xp_s4, x_i, y_i)
                    UnionFlag.set_f2_internal_m(union_xp_s4, x_i+1, y_i)
                    UnionFlag.set_f2_internal_m(union_xp_s4, x_i+2, y_i)
                    UnionFlag.set_f2_internal_m(union_xp_s5, x_i, y_i)
                    UnionFlag.set_f2_internal_m(union_xp_s5, x_i+1, y_i)
                    UnionFlag.set_f2_internal_m(union_xp_s5, x_i+2, y_i)

    def write_stage_xy(self, stage_index, f):
        union_xy = None
        if stage_index in self.dict_array_xp_union:
            union_xy = self.dict_array_xp_union[stage_index]
        else:
            union_xy = np.copy(self.default_stage_array)
        union_xy_zm1 = None
        if stage_index-1 in self.dict_array_xp_union:
            union_xy_zm1 = self.dict_array_xp_union[stage_index-1]
        else:
            union_xy_zm1 = np.copy(self.default_stage_array)
        union_xy_zp3 = None
        if stage_index+3 in self.dict_array_xp_union:
            union_xy_zp3 = self.dict_array_xp_union[stage_index+3]
        else:
            union_xy_zp3 = np.copy(self.default_stage_array)
        
        stage = self.dict_stage_array[stage_index]
        for x_i in range(stage.shape[0]):
            for y_i in range(stage.shape[1]):
                if OutputFlag.is_exist_any_xy_side(stage, x_i, y_i):
                    block = self.generate_block(stage_index, x_i, y_i)
                    if OutputFlag.is_x_p_side(stage, x_i, y_i)\
                    and not UnionFlag.is_union_p(union_xy, x_i, y_i):
                        square_tuple = (\
                            block.corner_xp_yp_zm(),\
                            block.corner_xp_yp_zp(),\
                            block.corner_xp_ym_zp(),\
                            block.corner_xp_ym_zm())
                        self.write_square(square_tuple, NormalVector.x_p_side, f)
                    elif UnionFlag.is_base_corner_p(union_xy, x_i, y_i):
                        if UnionFlag.is_union_p(union_xy, x_i, y_i-1) and UnionFlag.is_union_p(union_xy, x_i, y_i+3)\
                        and UnionFlag.is_union_p(union_xy_zm1, x_i, y_i) and UnionFlag.is_union_p(union_xy_zp3, x_i, y_i):
                            block_corner_ym_zp = self.generate_block(stage_index+2, x_i, y_i)
                            block_corner_yp_zm = self.generate_block(stage_index, x_i, y_i+2)
                            block_corner_yp_zp = self.generate_block(stage_index+2, x_i, y_i+2)
                            square_tuple = (\
                                block_corner_ym_zp.corner_xp_ym_zp(),\
                                block.corner_xp_ym_zm(),\
                                block_corner_yp_zm.corner_xp_yp_zm(),\
                                block_corner_yp_zp.corner_xp_yp_zp())
                            self.write_square(square_tuple, NormalVector.x_p_side, f)
                        else:
                            block_center = self.generate_block(stage_index+1, x_i, y_i+1)
                            panel_ym = UnionBlockPanel(\
                                block,\
                                self.generate_block(stage_index+1, x_i, y_i),
                                self.generate_block(stage_index+2, x_i, y_i),
                                block_center,
                                NormalVector.x_p_side)
                            for triangle in panel_ym.triangles(UnionFlag.is_union_p(union_xy, x_i, y_i-1)):
                                self.write_triangle(triangle, NormalVector.x_p_side, f)
                    
                            panel_yp = UnionBlockPanel(\
                                self.generate_block(stage_index+2, x_i, y_i+2),\
                                self.generate_block(stage_index+1, x_i, y_i+2),
                                self.generate_block(stage_index, x_i, y_i+2),
                                block_center,
                                NormalVector.x_p_side)
                            for triangle in panel_yp.triangles(UnionFlag.is_union_p(union_xy, x_i, y_i+3)):
                                self.write_triangle(triangle, NormalVector.x_p_side, f)
                            
                            panel_zm = UnionBlockPanel(\
                                self.generate_block(stage_index, x_i, y_i+2),
                                self.generate_block(stage_index, x_i, y_i+1),
                                block,
                                block_center,
                                NormalVector.x_p_side)
                            for triangle in panel_zm.triangles(UnionFlag.is_union_p(union_xy_zm1, x_i, y_i)):
                                self.write_triangle(triangle, NormalVector.x_p_side, f)
                            
                            panel_zp = UnionBlockPanel(\
                                self.generate_block(stage_index+2, x_i, y_i),\
                                self.generate_block(stage_index+2, x_i, y_i+1),
                                self.generate_block(stage_index+2, x_i, y_i+2),
                                block_center,
                                NormalVector.x_p_side)
                            for triangle in panel_zp.triangles(UnionFlag.is_union_p(union_xy_zp3, x_i, y_i)):
                                self.write_triangle(triangle, NormalVector.x_p_side, f)

                    if OutputFlag.is_x_m_side(stage, x_i, y_i)\
                    and not UnionFlag.is_union_m(union_xy, x_i, y_i):
                        square_tuple = (\
                            block.corner_xm_yp_zp(),\
                            block.corner_xm_yp_zm(),\
                            block.corner_xm_ym_zm(),\
                            block.corner_xm_ym_zp())
                        self.write_square(square_tuple, NormalVector.x_m_side, f)
                    elif UnionFlag.is_base_corner_m(union_xy, x_i, y_i):
                        if UnionFlag.is_union_m(union_xy, x_i, y_i-1) and UnionFlag.is_union_m(union_xy, x_i, y_i+3)\
                        and UnionFlag.is_union_m(union_xy_zm1, x_i, y_i) and UnionFlag.is_union_m(union_xy_zp3, x_i, y_i):
                            block_corner_ym_zp = self.generate_block(stage_index+2, x_i, y_i)
                            block_corner_yp_zm = self.generate_block(stage_index, x_i, y_i+2)
                            block_corner_yp_zp = self.generate_block(stage_index+2, x_i, y_i+2)
                            square_tuple = (\
                                block_corner_yp_zp.corner_xm_yp_zp(),\
                                block_corner_yp_zm.corner_xm_yp_zm(),\
                                block.corner_xm_ym_zm(),\
                                block_corner_ym_zp.corner_xm_ym_zp())
                            self.write_square(square_tuple, NormalVector.x_m_side, f)
                        else:
                            block_center = self.generate_block(stage_index+1, x_i, y_i+1)
                            panel_ym = UnionBlockPanel(\
                                self.generate_block(stage_index+2, x_i, y_i),\
                                self.generate_block(stage_index+1, x_i, y_i),
                                block,
                                block_center,
                                NormalVector.x_m_side)
                            for triangle in panel_ym.triangles(UnionFlag.is_union_m(union_xy, x_i, y_i-1)):
                                self.write_triangle(triangle, NormalVector.x_m_side, f)
                    
                            panel_yp = UnionBlockPanel(\
                                self.generate_block(stage_index, x_i, y_i+2),\
                                self.generate_block(stage_index+1, x_i, y_i+2),
                                self.generate_block(stage_index+2, x_i, y_i+2),
                                block_center,
                                NormalVector.x_m_side)
                            for triangle in panel_yp.triangles(UnionFlag.is_union_m(union_xy, x_i, y_i+3)):
                                self.write_triangle(triangle, NormalVector.x_m_side, f)
                            
                            panel_zm = UnionBlockPanel(\
                                block,
                                self.generate_block(stage_index, x_i, y_i+1),
                                self.generate_block(stage_index, x_i, y_i+2),
                                block_center,
                                NormalVector.x_m_side)
                            for triangle in panel_zm.triangles(UnionFlag.is_union_m(union_xy_zm1, x_i, y_i)):
                                self.write_triangle(triangle, NormalVector.x_m_side, f)
                            
                            panel_zp = UnionBlockPanel(\
                                self.generate_block(stage_index+2, x_i, y_i+2),\
                                self.generate_block(stage_index+2, x_i, y_i+1),
                                self.generate_block(stage_index+2, x_i, y_i),
                                block_center,
                                NormalVector.x_m_side)
                            for triangle in panel_zp.triangles(UnionFlag.is_union_m(union_xy_zp3, x_i, y_i)):
                                self.write_triangle(triangle, NormalVector.x_m_side, f)

                    if OutputFlag.is_y_p_side(stage, x_i, y_i)\
                    and not UnionFlag.is_f2_union_p(union_xy, x_i, y_i):
                        square_tuple = (\
                            block.corner_xm_yp_zp(),\
                            block.corner_xp_yp_zp(),\
                            block.corner_xp_yp_zm(),\
                            block.corner_xm_yp_zm())
                        self.write_square(square_tuple, NormalVector.y_p_side, f)
                    elif UnionFlag.is_f2_base_corner_p(union_xy, x_i, y_i):
                        if UnionFlag.is_f2_union_p(union_xy, x_i-1, y_i) and UnionFlag.is_f2_union_p(union_xy, x_i+3, y_i)\
                        and UnionFlag.is_f2_union_p(union_xy_zm1, x_i, y_i) and UnionFlag.is_f2_union_p(union_xy_zp3, x_i, y_i):
                            block_corner_xm_zp = self.generate_block(stage_index+2, x_i, y_i)
                            block_corner_xp_zm = self.generate_block(stage_index, x_i+2, y_i)
                            block_corner_xp_zp = self.generate_block(stage_index+2, x_i+2, y_i)
                            square_tuple = (\
                                block_corner_xm_zp.corner_xm_yp_zp(),\
                                block_corner_xp_zp.corner_xp_yp_zp(),\
                                block_corner_xp_zm.corner_xp_yp_zm(),\
                                block.corner_xm_yp_zm())
                            self.write_square(square_tuple, NormalVector.y_p_side, f)
                        else:
                            block_center = self.generate_block(stage_index+1, x_i+1, y_i)
                            panel_xm = UnionBlockPanel(\
                                self.generate_block(stage_index+2, x_i, y_i),\
                                self.generate_block(stage_index+1, x_i, y_i),
                                block,
                                block_center,
                                NormalVector.y_p_side)
                            for triangle in panel_xm.triangles(UnionFlag.is_f2_union_p(union_xy, x_i-1, y_i)):
                                self.write_triangle(triangle, NormalVector.y_p_side, f)
                    
                            panel_xp = UnionBlockPanel(\
                                self.generate_block(stage_index, x_i+2, y_i),\
                                self.generate_block(stage_index+1, x_i+2, y_i),
                                self.generate_block(stage_index+2, x_i+2, y_i),
                                block_center,
                                NormalVector.y_p_side)
                            for triangle in panel_xp.triangles(UnionFlag.is_f2_union_p(union_xy, x_i+3, y_i)):
                                self.write_triangle(triangle, NormalVector.y_p_side, f)
                            
                            panel_zm = UnionBlockPanel(\
                                block,
                                self.generate_block(stage_index, x_i+1, y_i),
                                self.generate_block(stage_index, x_i+2, y_i),
                                block_center,
                                NormalVector.y_p_side)
                            for triangle in panel_zm.triangles(UnionFlag.is_f2_union_p(union_xy_zm1, x_i, y_i)):
                                self.write_triangle(triangle, NormalVector.y_p_side, f)
                            
                            panel_zp = UnionBlockPanel(\
                                self.generate_block(stage_index+2, x_i+2, y_i),\
                                self.generate_block(stage_index+2, x_i+1, y_i),
                                self.generate_block(stage_index+2, x_i, y_i),
                                block_center,
                                NormalVector.y_p_side)
                            for triangle in panel_zp.triangles(UnionFlag.is_f2_union_p(union_xy_zp3, x_i, y_i)):
                                self.write_triangle(triangle, NormalVector.y_p_side, f)

                    if OutputFlag.is_y_m_side(stage, x_i, y_i)\
                    and not UnionFlag.is_f2_union_m(union_xy, x_i, y_i):
                        square_tuple = (\
                            block.corner_xp_ym_zp(),\
                            block.corner_xm_ym_zp(),\
                            block.corner_xm_ym_zm(),\
                            block.corner_xp_ym_zm())
                        self.write_square(square_tuple, NormalVector.y_m_side, f)
                    elif UnionFlag.is_f2_base_corner_m(union_xy, x_i, y_i):
                        if UnionFlag.is_f2_union_m(union_xy, x_i-1, y_i) and UnionFlag.is_f2_union_m(union_xy, x_i+3, y_i)\
                        and UnionFlag.is_f2_union_m(union_xy_zm1, x_i, y_i) and UnionFlag.is_f2_union_m(union_xy_zp3, x_i, y_i):
                            block_corner_xm_zp = self.generate_block(stage_index+2, x_i, y_i)
                            block_corner_xp_zm = self.generate_block(stage_index, x_i+2, y_i)
                            block_corner_xp_zp = self.generate_block(stage_index+2, x_i+2, y_i)
                            square_tuple = (\
                                block_corner_xp_zp.corner_xp_ym_zp(),\
                                block_corner_xm_zp.corner_xm_ym_zp(),\
                                block.corner_xm_ym_zm(),\
                                block_corner_xp_zm.corner_xp_ym_zm())
                            self.write_square(square_tuple, NormalVector.y_m_side, f)
                        else:
                            block_center = self.generate_block(stage_index+1, x_i+1, y_i)
                            panel_xm = UnionBlockPanel(\
                                block,\
                                self.generate_block(stage_index+1, x_i, y_i),
                                self.generate_block(stage_index+2, x_i, y_i),
                                block_center,
                                NormalVector.y_m_side)
                            for triangle in panel_xm.triangles(UnionFlag.is_f2_union_m(union_xy, x_i-1, y_i)):
                                self.write_triangle(triangle, NormalVector.y_m_side, f)
                    
                            panel_xp = UnionBlockPanel(\
                                self.generate_block(stage_index+2, x_i+2, y_i),\
                                self.generate_block(stage_index+1, x_i+2, y_i),
                                self.generate_block(stage_index, x_i+2, y_i),
                                block_center,
                                NormalVector.y_m_side)
                            for triangle in panel_xp.triangles(UnionFlag.is_f2_union_m(union_xy, x_i+3, y_i)):
                                self.write_triangle(triangle, NormalVector.y_m_side, f)
                            
                            panel_zm = UnionBlockPanel(\
                                self.generate_block(stage_index, x_i+2, y_i),
                                self.generate_block(stage_index, x_i+1, y_i),
                                block,
                                block_center,
                                NormalVector.y_m_side)
                            for triangle in panel_zm.triangles(UnionFlag.is_f2_union_m(union_xy_zm1, x_i, y_i)):
                                self.write_triangle(triangle, NormalVector.y_m_side, f)
                            
                            panel_zp = UnionBlockPanel(\
                                self.generate_block(stage_index+2, x_i, y_i),\
                                self.generate_block(stage_index+2, x_i+1, y_i),
                                self.generate_block(stage_index+2, x_i+2, y_i),
                                block_center,
                                NormalVector.y_m_side)
                            for triangle in panel_zp.triangles(UnionFlag.is_f2_union_m(union_xy_zp3, x_i, y_i)):
                                self.write_triangle(triangle, NormalVector.y_m_side, f)

    def write_stage_z(self, stage_index, f, catConfig: ConcatConfig):
        stage = self.dict_stage_array[stage_index]
        union_z = np.copy(self.default_stage_array)
        if catConfig.merge_consecutive_face:
            for x_i in range(0, stage.shape[0], 3):
                for y_i in range(0, stage.shape[1], 3):
                    if OutputFlag.is_exist_any_z_side(stage, x_i, y_i):
                        if OutputFlag.is_exist_range_all_side(stage, x_i, x_i+2, y_i, y_i+2, OutputFlag.flag_z_p_side):
                            UnionFlag.set_base_corner_p(union_z, x_i, y_i)
                            UnionFlag.set_internal_p(union_z, x_i, y_i+1)
                            UnionFlag.set_internal_p(union_z, x_i, y_i+2)
                            UnionFlag.set_internal_p(union_z, x_i+1, y_i)
                            UnionFlag.set_internal_p(union_z, x_i+1, y_i+1)
                            UnionFlag.set_internal_p(union_z, x_i+1, y_i+2)
                            UnionFlag.set_internal_p(union_z, x_i+2, y_i)
                            UnionFlag.set_internal_p(union_z, x_i+2, y_i+1)
                            UnionFlag.set_internal_p(union_z, x_i+2, y_i+2)
                        
                        if OutputFlag.is_exist_range_all_side(stage, x_i, x_i+2, y_i, y_i+2, OutputFlag.flag_z_m_side):
                            UnionFlag.set_base_corner_m(union_z, x_i, y_i)
                            UnionFlag.set_internal_m(union_z, x_i, y_i+1)
                            UnionFlag.set_internal_m(union_z, x_i, y_i+2)
                            UnionFlag.set_internal_m(union_z, x_i+1, y_i)
                            UnionFlag.set_internal_m(union_z, x_i+1, y_i+1)
                            UnionFlag.set_internal_m(union_z, x_i+1, y_i+2)
                            UnionFlag.set_internal_m(union_z, x_i+2, y_i)
                            UnionFlag.set_internal_m(union_z, x_i+2, y_i+1)
                            UnionFlag.set_internal_m(union_z, x_i+2, y_i+2)
        
        for x_i in range(stage.shape[0]):
            for y_i in range(stage.shape[1]):
                if OutputFlag.is_exist_any_z_side(stage, x_i, y_i):
                    block = self.generate_block(stage_index, x_i, y_i)
                    if OutputFlag.is_z_p_side(stage, x_i, y_i) and not UnionFlag.is_union_p(union_z, x_i, y_i):
                        square_tuple = (\
                            block.corner_xm_yp_zp(),\
                            block.corner_xm_ym_zp(),\
                            block.corner_xp_ym_zp(),\
                            block.corner_xp_yp_zp())
                        self.write_square(square_tuple, NormalVector.z_p_side, f)
                    elif UnionFlag.is_base_corner_p(union_z, x_i, y_i)\
                        and UnionFlag.is_internal_p(union_z, x_i-1, y_i) and UnionFlag.is_internal_p(union_z, x_i, y_i+3)\
                        and UnionFlag.is_internal_p(union_z, x_i+3, y_i+2) and UnionFlag.is_internal_p(union_z, x_i+2, y_i-1):
                        block_corner_xm_yp = self.generate_block(stage_index, x_i, y_i+2)
                        block_corner_xp_yp = self.generate_block(stage_index, x_i+2, y_i+2)
                        block_corner_xp_ym = self.generate_block(stage_index, x_i+2, y_i)
                        square_tuple = (\
                            block_corner_xm_yp.corner_xm_yp_zp(),\
                            block.corner_xm_ym_zp(),\
                            block_corner_xp_ym.corner_xp_ym_zp(),\
                            block_corner_xp_yp.corner_xp_yp_zp())
                        self.write_square(square_tuple, NormalVector.z_p_side, f)
                    elif UnionFlag.is_base_corner_p(union_z, x_i, y_i):
                        center = self.generate_block(stage_index, x_i+1, y_i+1)
                        
                        panel_xm = UnionBlockPanel(
                            block,
                            self.generate_block(stage_index, x_i, y_i+1),
                            self.generate_block(stage_index, x_i, y_i+2),
                            center,
                            NormalVector.z_p_side)
                        for triangle in panel_xm.triangles(UnionFlag.is_union_p(union_z, x_i-1, y_i)):
                            self.write_triangle(triangle, NormalVector.z_p_side, f)
                        
                        panel_xp = UnionBlockPanel(
                            self.generate_block(stage_index, x_i+2, y_i+2),
                            self.generate_block(stage_index, x_i+2, y_i+1),
                            self.generate_block(stage_index, x_i+2, y_i),
                            center,
                            NormalVector.z_p_side)
                        for triangle in panel_xp.triangles(UnionFlag.is_union_p(union_z, x_i+3, y_i)):
                            self.write_triangle(triangle, NormalVector.z_p_side, f)
                        
                        panel_ym = UnionBlockPanel(
                            self.generate_block(stage_index, x_i+2, y_i),
                            self.generate_block(stage_index, x_i+1, y_i),
                            block,
                            center,
                            NormalVector.z_p_side)
                        for triangle in panel_ym.triangles(UnionFlag.is_union_p(union_z, x_i, y_i-1)):
                            self.write_triangle(triangle, NormalVector.z_p_side, f)
                        
                        panel_yp = UnionBlockPanel(
                            self.generate_block(stage_index, x_i, y_i+2),
                            self.generate_block(stage_index, x_i+1, y_i+2),
                            self.generate_block(stage_index, x_i+2, y_i+2),
                            center,
                            NormalVector.z_p_side)
                        for triangle in panel_yp.triangles(UnionFlag.is_union_p(union_z, x_i, y_i+3)):
                            self.write_triangle(triangle, NormalVector.z_p_side, f)

                    if OutputFlag.is_z_m_side(stage, x_i, y_i) and not UnionFlag.is_union_m(union_z, x_i, y_i):
                        square_tuple = (\
                            block.corner_xp_yp_zm(),\
                            block.corner_xp_ym_zm(),\
                            block.corner_xm_ym_zm(),\
                            block.corner_xm_yp_zm())
                        self.write_square(square_tuple, NormalVector.z_m_side, f)
                    elif UnionFlag.is_base_corner_m(union_z, x_i, y_i)\
                        and UnionFlag.is_union_m(union_z, x_i-1, y_i) and UnionFlag.is_union_m(union_z, x_i, y_i+3)\
                        and UnionFlag.is_union_m(union_z, x_i+3, y_i+2) and UnionFlag.is_union_m(union_z, x_i+2, y_i-1):
                        block_corner_xm_yp = self.generate_block(stage_index, x_i, y_i+2)
                        block_corner_xp_yp = self.generate_block(stage_index, x_i+2, y_i+2)
                        block_corner_xp_ym = self.generate_block(stage_index, x_i+2, y_i)
                        square_tuple = (\
                            block_corner_xp_yp.corner_xp_yp_zm(),\
                            block_corner_xp_ym.corner_xp_ym_zm(),\
                            block.corner_xm_ym_zm(),\
                            block_corner_xm_yp.corner_xm_yp_zm())
                        self.write_square(square_tuple, NormalVector.z_m_side, f)
                    elif UnionFlag.is_base_corner_m(union_z, x_i, y_i):
                        center = self.generate_block(stage_index, x_i+1, y_i+1)

                        panel_xm = UnionBlockPanel(
                            self.generate_block(stage_index, x_i, y_i+2),
                            self.generate_block(stage_index, x_i, y_i+1),
                            block,
                            center,
                            NormalVector.z_m_side)
                        for triangle in panel_xm.triangles(UnionFlag.is_union_m(union_z, x_i-1, y_i)):
                            self.write_triangle(triangle, NormalVector.z_m_side, f)
                        
                        panel_xp = UnionBlockPanel(
                            self.generate_block(stage_index, x_i+2, y_i),
                            self.generate_block(stage_index, x_i+2, y_i+1),
                            self.generate_block(stage_index, x_i+2, y_i+2),
                            center,
                            NormalVector.z_m_side)
                        for triangle in panel_xp.triangles(UnionFlag.is_union_m(union_z, x_i+3, y_i)):
                            self.write_triangle(triangle, NormalVector.z_m_side, f)
                        
                        panel_ym = UnionBlockPanel(
                            block,
                            self.generate_block(stage_index, x_i+1, y_i),
                            self.generate_block(stage_index, x_i+2, y_i),
                            center,
                            NormalVector.z_m_side)
                        for triangle in panel_ym.triangles(UnionFlag.is_union_m(union_z, x_i, y_i-1)):
                            self.write_triangle(triangle, NormalVector.z_m_side, f)
                        
                        panel_yp = UnionBlockPanel(
                            self.generate_block(stage_index, x_i+2, y_i+2),
                            self.generate_block(stage_index, x_i+1, y_i+2),
                            self.generate_block(stage_index, x_i, y_i+2),
                            center,
                            NormalVector.z_m_side)
                        for triangle in panel_yp.triangles(UnionFlag.is_union_m(union_z, x_i, y_i+3)):
                            self.write_triangle(triangle, NormalVector.z_m_side, f)

    def generate_block(self, stage_index, x_i, y_i):
        z = self.catConfig.stage_position(stage_index)
        x = self.x_position(x_i)
        y = self.y_position(y_i)
        xy_interval = self.catConfig.xy_plane_interval
        z_pitch = self.catConfig.stage_pitch
        return Block(np.array([x,y,z,1.]), xy_interval/2, z_pitch/2)
        
    def write_square(self, tuple_square_positions, normal_vector, f):
        facet_1 = Facet(\
            tuple_square_positions[0],\
            tuple_square_positions[1],\
            tuple_square_positions[2],\
            normal_vector)
        facet_1.write_binary(f)
        facet_2 = Facet(\
            tuple_square_positions[0],\
            tuple_square_positions[2],\
            tuple_square_positions[3],\
            normal_vector)
        facet_2.write_binary(f)
        self.triangle_count = self.triangle_count + 2
    
    def write_triangle(self, tuple_triangle_positions, normal_vector, f):
        facet_1 = Facet(\
            tuple_triangle_positions[0],\
            tuple_triangle_positions[1],\
            tuple_triangle_positions[2],\
            normal_vector)
        facet_1.write_binary(f)
        self.triangle_count = self.triangle_count + 1
    
    def fetch_z_range(self):
        z_min = sys.float_info.max
        z_max = -sys.float_info.max
        for shell in self.shells:
            if shell.z_min() < z_min:
                z_min = shell.z_min()

            if z_max < shell.z_max():
                z_max = shell.z_max()
        return (z_min, z_max)
    
@dataclass
class Block:
    center_position:np.ndarray
    half_xy_edge_length:float
    half_z_edge_length:float
    
    def corner_xp_yp_zp(self):
        return self.corner((1,1,1))

    def corner_xp_yp_zm(self):
        return self.corner((1,1,-1))

    def corner_xp_ym_zp(self):
        return self.corner((1,-1,1))

    def corner_xp_ym_zm(self):
        return self.corner((1,-1,-1))

    def corner_xm_yp_zp(self):
        return self.corner((-1,1,1))

    def corner_xm_yp_zm(self):
        return self.corner((-1,1,-1))

    def corner_xm_ym_zp(self):
        return self.corner((-1,-1,1))

    def corner_xm_ym_zm(self):
        return self.corner((-1,-1,-1))
    
    def center_zp(self):
        p = self.center_position.copy()
        p[2] = p[2] + self.half_z_edge_length
        return p
    
    def center_zm(self):
        p = self.center_position.copy()
        p[2] = p[2] - self.half_z_edge_length
        return p
    
    def corner(self, tuple_xyz):
        p = self.center_position.copy()
        p[0] = p[0] + tuple_xyz[0]*self.half_xy_edge_length
        p[1] = p[1] + tuple_xyz[1]*self.half_xy_edge_length
        p[2] = p[2] + tuple_xyz[2]*self.half_z_edge_length
        return p

@dataclass
class UnionBlockPanel:
    start:Block
    internal:Block
    end:Block
    center:Block
    normal_vector:np.ndarray

    def triangles(self, contatinated):
        if contatinated:
            return self.triangles_contatinated()
        else:
            return self.triangles_separated()

    def triangles_contatinated(self):
        start_directions = (self.start_direction_x(), self.start_direction_y(), self.start_direction_z())
        end_directions = (self.end_direction_x(), self.end_direction_y(), self.end_direction_z())
        center_direction = (int(self.normal_vector[0]), int(self.normal_vector[1]), int(self.normal_vector[2]))
        return [(self.start.corner(start_directions), self.center.corner(center_direction), self.end.corner(end_directions))]

    def triangles_separated(self):
        start_directions = (self.start_direction_x(), self.start_direction_y(), self.start_direction_z())
        end_directions = (self.end_direction_x(), self.end_direction_y(), self.end_direction_z())
        center_direction = (int(self.normal_vector[0]), int(self.normal_vector[1]), int(self.normal_vector[2]))
        triangle1 = (self.start.corner(start_directions), self.center.corner(center_direction), self.start.corner(end_directions))
        triangle2 = (self.internal.corner(start_directions), self.center.corner(center_direction), self.internal.corner(end_directions))
        triangle3 = (self.end.corner(start_directions), self.center.corner(center_direction), self.end.corner(end_directions))
        return [triangle1, triangle2, triangle3]

    def start_direction_x(self):
        return self.start_direction(0)
    
    def end_direction_x(self):
        direction = self.start_direction(0)
        if self.start.center_position[0] == self.end.center_position[0]:
            return direction
        return -direction
    
    def start_direction_y(self):
        return self.start_direction(1)
    
    def end_direction_y(self):
        direction = self.start_direction(1)
        if self.start.center_position[1] == self.end.center_position[1]:
            return direction
        return -direction

    def start_direction_z(self):
        return self.start_direction(2)
    
    def end_direction_z(self):
        direction = self.start_direction(2)
        if self.start.center_position[2] == self.end.center_position[2]:
            return direction
        return -direction

    def start_direction(self, axis):
        if self.center.center_position[axis] == self.start.center_position[axis]\
        and self.center.center_position[axis] == self.end.center_position[axis]:
            return int(self.normal_vector[axis])
        else:
            if self.center.center_position[axis] == self.internal.center_position[axis]:
                if self.start.center_position[axis] < self.end.center_position[axis]:
                    return -1
                else:
                    return 1
            else:
                if self.center.center_position[axis] < self.internal.center_position[axis]:
                    return 1
                else:
                    return -1

def float_to_int_range_included(float_min, float_max, scale):
    min_index_f = float_min/scale
    min_index = int(min_index_f)
    if min_index <= min_index_f:
        min_index = min_index + 1
    max_index_f = float_max/scale
    max_index = int(max_index_f)
    if max_index_f <= max_index:
        max_index = max_index - 1
    return (min_index, max_index)

def calc_penetration_y_axis_pararell(triangles, y_start_pos, y_vector):
    y_end_pos = y_start_pos + y_vector
    list_penetration = []
    for triangle in triangles:
        if not calc_util.is_positions_and_array_overrap_on_plane(triangle.get_positions(), [y_start_pos, y_end_pos], 0):
            continue
        if not calc_util.is_positions_and_array_overrap_on_plane(triangle.get_positions(), [y_start_pos, y_end_pos], 2):
            continue
        vector_ray_to_v1 = calc_util.extract_vector_1by3(triangle.vertex_1.position)-y_start_pos
        vector_ray_to_v2 = calc_util.extract_vector_1by3(triangle.vertex_2.position)-y_start_pos
        vector_ray_to_v3 = calc_util.extract_vector_1by3(triangle.vertex_3.position)-y_start_pos

        outer1_2 = np.cross(vector_ray_to_v1, vector_ray_to_v2)
        outer2_3 = np.cross(vector_ray_to_v2, vector_ray_to_v3)
        outer3_1 = np.cross(vector_ray_to_v3, vector_ray_to_v1)

        inner_product_with_side1_2 = np.dot(outer1_2, y_vector)
        inner_product_with_side2_3 = np.dot(outer2_3, y_vector)
        inner_product_with_side3_1 = np.dot(outer3_1, y_vector)
        
        if 0 >= inner_product_with_side1_2 * inner_product_with_side2_3 \
            or 0 >= inner_product_with_side1_2 * inner_product_with_side3_1:
            continue

        vector_side1_2 = calc_util.extract_vector_1by3(triangle.vertex_1.vector_to(triangle.vertex_2))
        vector_side1_3 = calc_util.extract_vector_1by3(triangle.vertex_1.vector_to(triangle.vertex_3))
        vector_ray_origin_to_vertex1 = y_start_pos-calc_util.extract_vector_1by3(triangle.vertex_1.position)
        
        solved = np.dot(vector_ray_origin_to_vertex1, np.linalg.inv(np.array([-y_vector, vector_side1_2, vector_side1_3])))
        list_penetration.append(y_start_pos[1] + y_vector[1] * solved[0])
            
    return list_penetration

class OutputFlag:
    flag_exist = 0b00000001
    flag_z_p_side = 0b00000010
    flag_z_m_side = 0b00000100
    flag_x_p_side = 0b00001000
    flag_x_m_side = 0b00010000
    flag_y_p_side = 0b00100000
    flag_y_m_side = 0b01000000
    flag_any_side = 0b01111110
    flag_any_xy_side = 0b01111000
    flag_any_z_side = 0b00000110

    def set_exist(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | OutputFlag.flag_exist
    
    def set_z_p_side(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | OutputFlag.flag_z_p_side

    def set_z_m_side(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | OutputFlag.flag_z_m_side

    def set_x_p_side(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | OutputFlag.flag_x_p_side

    def set_x_m_side(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | OutputFlag.flag_x_m_side

    def set_y_p_side(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | OutputFlag.flag_y_p_side

    def set_y_m_side(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | OutputFlag.flag_y_m_side

    def is_exist(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & OutputFlag.flag_exist)
    
    def is_exist_range_all_side(ndarray_2_by_2, x_index_start, x_index_end, y_index_start, y_index_end, side_byte):
        for x_i in range(x_index_end - x_index_start + 1):
            for y_i in range(y_index_end - y_index_start + 1):
                if not 0b0 != (ndarray_2_by_2[x_index_start + x_i][y_index_start + y_i] & side_byte):
                    return False
        return True
    
    def is_exist_any_side(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & OutputFlag.flag_any_side)
    
    def is_exist_any_xy_side(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & OutputFlag.flag_any_xy_side)
        
    def is_exist_any_z_side(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & OutputFlag.flag_any_z_side)
    
    def is_z_p_side(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & OutputFlag.flag_z_p_side)

    def is_z_m_side(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & OutputFlag.flag_z_m_side)

    def is_x_p_side(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & OutputFlag.flag_x_p_side)

    def is_x_m_side(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & OutputFlag.flag_x_m_side)

    def is_y_p_side(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & OutputFlag.flag_y_p_side)

    def is_y_m_side(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & OutputFlag.flag_y_m_side)

class UnionFlag:
    flag_base_corner_p = 0b00000001
    flag_internal_p = 0b00000010
    flag_base_corner_m = 0b00000100
    flag_internal_m = 0b00001000
    flag2_base_corner_p = 0b00010000
    flag2_internal_p = 0b00100000
    flag2_base_corner_m = 0b01000000
    flag2_internal_m = 0b10000000
    flag_any_p = 0b00000011
    flag_any_m = 0b00001100
    flag2_any_p = 0b00110000
    flag2_any_m = 0b11000000
    
    def set_base_corner_p(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | UnionFlag.flag_base_corner_p

    def set_internal_p(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | UnionFlag.flag_internal_p
    
    def set_base_corner_m(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | UnionFlag.flag_base_corner_m

    def set_internal_m(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | UnionFlag.flag_internal_m

    def set_f2_base_corner_p(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | UnionFlag.flag2_base_corner_p

    def set_f2_internal_p(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | UnionFlag.flag2_internal_p
    
    def set_f2_base_corner_m(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | UnionFlag.flag2_base_corner_m

    def set_f2_internal_m(ndarray_2_by_2, x_index, y_index):
        ndarray_2_by_2[x_index][y_index] = ndarray_2_by_2[x_index][y_index] | UnionFlag.flag2_internal_m

    def is_base_corner_p(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & UnionFlag.flag_base_corner_p)
    
    def is_internal_p(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & UnionFlag.flag_internal_p)
    
    def is_union_p(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & UnionFlag.flag_any_p)
    
    def is_base_corner_m(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & UnionFlag.flag_base_corner_m)
    
    def is_internal_m(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & UnionFlag.flag_internal_m)

    def is_union_m(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & UnionFlag.flag_any_m)
    
    def is_f2_base_corner_p(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & UnionFlag.flag2_base_corner_p)
    
    def is_f2_internal_p(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & UnionFlag.flag2_internal_p)
    
    def is_f2_union_p(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & UnionFlag.flag2_any_p)
    
    def is_f2_base_corner_m(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & UnionFlag.flag2_base_corner_m)
    
    def is_f2_internal_m(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & UnionFlag.flag2_internal_m)
    
    def is_f2_union_m(ndarray_2_by_2, x_index, y_index):
        return 0b0 != (ndarray_2_by_2[x_index][y_index] & UnionFlag.flag2_any_m)

class NormalVector:
    z_p_side = np.array([0.,0.,1.,1.])
    z_m_side = np.array([0.,0.,-1.,1.])
    x_p_side = np.array([1.,0.,0.,1.])
    x_m_side = np.array([-1.,0.,0.,1.])
    y_p_side = np.array([0.,1.,0.,1.])
    y_m_side = np.array([0.,-1.,0.,1.])
