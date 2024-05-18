import re
import copy

from dataclasses import dataclass, field

from .bone_json_util import BoneKeys

@dataclass
class Restriction:
    fix_x:bool = field(default=False)
    fix_y:bool = field(default=False)
    fix_z:bool = field(default=False)

@dataclass
class DefaultAngle:
    x:float = field(default=0.)
    y:float = field(default=0.)
    z:float = field(default=0.)

    def get_rotation(self, mirror_x = False, mirror_y = False, mirror_z = False):
        return {
            BoneKeys.x: -self.x if mirror_x else self.x,
            BoneKeys.y: -self.y if mirror_y else self.y,
            BoneKeys.z: -self.z if mirror_z else self.z,
        }

@dataclass
class DefaultLocation:
    x:float = field(default=0.)
    y:float = field(default=0.)
    z:float = field(default=0.)

    def get_location(self, mirror_x = False, mirror_y = False, mirror_z = False):
        return {
            BoneKeys.location_x: -self.x if mirror_x else self.x,
            BoneKeys.location_y: -self.y if mirror_y else self.y,
            BoneKeys.location_z: -self.z if mirror_z else self.z,
        }

@dataclass
class ModelMirrorInfo:
    original:str
    x:bool = field(default=False)
    y:bool = field(default=False)
    z:bool = field(default=False)

    def mirror_count(self):
        return (1 if self.x else 0) + (1 if self.y else 0) + (1 if self.z else 0)

@dataclass
class LocationMirrorInfo:
    x:bool = field(default=False)
    y:bool = field(default=False)
    z:bool = field(default=False)

    def info(self):
        return {
            "mirror_x": self.x,
            "mirror_y": self.y,
            "mirror_z": self.z,
        }

@dataclass
class AngleMirrorInfo:
    x:bool = field(default=False)
    y:bool = field(default=False)
    z:bool = field(default=False)

    def info(self):
        return {
            "mirror_x": self.x,
            "mirror_y": self.y,
            "mirror_z": self.z,
        }

@dataclass
class Info:
    length:float = field(default=None)
    spec:any = field(default=None)
    restriction:any = field(default=None)
    alias_of:str = field(default=None)
    mirror_info:any = field(default=None)
    default_angle:any = field(default=None)
    default_location:any = field(default=None)
    angle_mirror:any = field(default=None)
    location_mirror:any = field(default=None)

    def set_pose(self, angle=None, location=None):
        self.default_angle = angle
        self.default_location = location

    def set_mirror_info(self, model=None, angle=None, location=None):
        self.mirror_info = model
        self.angle_mirror = angle
        self.location_mirror = location

@dataclass
class Relationship:
    bone:any
    key_parent:str

@dataclass
class Bone:
    name:str
    child:list = field(default_factory=list)
    info: Info = field(default_factory=Info)

    def flatten(self, parent:str, flattened:dict):
        flattened[self.name] = Relationship(self, parent)
        for child in self.child:
            child.flatten(self.name, flattened)
        return flattened
    
    def left_to_right(self):
        flattened = self.flatten(None, {})
        bones = {}
        for key_left, relationship in flattened.items():
            bone_left = relationship.bone
            parent_left = relationship.key_parent
            key_right = re.sub('_l$', '_r', key_left)
            parent_right = None if parent_left == None else re.sub('_l$', '_r', parent_left)
            bones[key_right] = Relationship(Bone(name=key_right, info=copy.deepcopy(bone_left.info)), parent_right)

        key_root = None
        for relationship in bones.values():
            bone = relationship.bone
            parent = relationship.key_parent
            if parent == None:
                key_root = bone.name
            else:
                bones[parent].bone.child.append(bone)
        
        return bones[key_root].bone


