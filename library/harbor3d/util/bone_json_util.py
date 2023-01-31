from dataclasses import dataclass

class BoneKeys:
    parent = 'parent'
    length = 'length'
    z = 'z'
    y = 'y'
    x = 'x'
    is_disconnected_to_parent = 'is_disconnected_to_parent'
    parent_offset = 'parent_offset'
    offset_x = 'x'
    offset_y = 'y'
    offset_z = 'z'

@dataclass
class GlobalAxisValue:
    x_global:float
    y_global:float
    z_global:float

    # global | bone
    # x axis =  x axis
    # y axis = -z axis
    # z axis =  y axis

    def bone_x(self):
        return self.x_global

    def bone_y(self):
        return -self.z_global

    def bone_z(self):
        return self.y_global
    
    def bone_xyz(self):
        return (self.bone_x(), self.bone_y(), self.bone_z())

@dataclass
class BoneAxisValue:
    x_bone:float
    y_bone:float
    z_bone:float

    # bone   | global
    # x axis =  x axis
    # y axis =  z axis
    # z axis = -y axis

    def global_x(self):
        return self.x_bone

    def global_y(self):
        return self.z_bone

    def global_z(self):
        return -self.y_bone
    
    def global_xyz(self):
        return (self.global_x(), self.global_y(), self.global_z())

@dataclass
class PostureWrapper:
    postures:dict

    def fetch_bone_names(self):
        return self.postures.keys()

    def fetch_bone(self, bone_key):
        if bone_key in self.postures.keys():
            return self.postures[bone_key]
        return None
    
    def fetch(self, bone_key, param_key):
        bone = self.fetch_bone(bone_key)
        if bone == None:
            Exception('invalid bone key')
        return bone[param_key]
    
    def fetch_bone_rotate_dict(self, bone_key):
        rotate = {}
        rotate[BoneKeys.x] = self.fetch(bone_key, BoneKeys.x)
        rotate[BoneKeys.y] = self.fetch(bone_key, BoneKeys.y)
        rotate[BoneKeys.z] = self.fetch(bone_key, BoneKeys.z)
        return rotate

    def set_offset_on_bone_axis(self, key:str, x:float = 0., y:float = 0., z:float= 0.):
        self.postures[key][BoneKeys.is_disconnected_to_parent] = True
        parent_offset = {}
        parent_offset[BoneKeys.offset_x] = x
        parent_offset[BoneKeys.offset_y] = y
        parent_offset[BoneKeys.offset_z] = z
        self.postures[key][BoneKeys.parent_offset] = parent_offset

    def set_offset(self, key:str, x:float = 0., y:float = 0., z:float= 0.):
        value = GlobalAxisValue(x,y,z)
        self.set_offset_on_bone_axis(key, value.bone_x(), value.bone_y(), value.bone_z())
    
    def remove_offset(self, key:str):
        self.postures[key][BoneKeys.is_disconnected_to_parent] = False
        if BoneKeys.parent_offset in self.postures[key].keys():
            del self.postures[key][BoneKeys.parent_offset]
    
    def set_length(self, key:str, length:float):
        self.postures[key][BoneKeys.length] = length
    
    def set_length_all(self, langth_info:dict):
        posture_keys = self.postures.keys()
        for k,v in langth_info.items():
            if k in posture_keys:
                self.postures[k][BoneKeys.length] = v
