from dataclasses import dataclass, field

import numpy as np

@dataclass
class Spec:
    l:float
    h_w:tuple = field(default=None)
    r_d:tuple = field(default=None)
    rib_divid:int = field(default=0)
    wrap_offset:float = field(default=0.)
    # chamfer
    root_end_ratio:tuple = field(default=None)
    root_end_coner_length:float = field(default=0.)
    tip_end_ratio:tuple = field(default=None)
    tip_end_coner_length:float = field(default=0.)
    # move
    move_xyz:tuple = field(default=None)
    # rotation
    list_rotation_yz:list = field(default=None)

    def is_rectangle(self):
        return None != self.h_w

    def height(self):
        if not self.is_rectangle(): return 0.
        return self.h_w[0]
    
    def width(self):
        if not self.is_rectangle(): return 0.
        return self.h_w[1]

    def length_without_overwrap(self):
        return self.l-self.wrap_offset
    
    def is_pole(self):
        return None != self.r_d

    def radius(self):
        if not self.is_pole(): return 0.
        return self.r_d[0]
    
    def divid(self):
        if not self.is_pole(): return 0.
        return self.r_d[1]

    # chamfer: root end
    def needs_root_end_chamfered(self):
        return None != self.root_end_ratio
    
    def root_end_chamfered_ratio_w(self):
        return self.root_end_ratio[0]
    
    def root_end_chamfered_ratio_h(self):
        return self.root_end_ratio[1]
    
    def root_end_chamfered_ratio_r(self):
        return self.root_end_ratio[0]
    
    # chamfer: tip end
    def needs_tip_end_chamfered(self):
        return None != self.tip_end_ratio

    def tip_end_chamfered_ratio_w(self):
        return self.tip_end_ratio[0]
    
    def tip_end_chamfered_ratio_h(self):
        return self.tip_end_ratio[1]

    def tip_end_chamfered_ratio_r(self):
        return self.tip_end_ratio[0]
    
    # set chamfer: root end
    def set_rect_root_end_chamfered_ratio(self, length, w_ratio=1., h_ratio=1.):
        self.root_end_ratio = (w_ratio,h_ratio)
        self.root_end_coner_length = length
        return self
    
    def set_pole_root_end_chamfered_ratio(self, length, r_ratio=1.):
        self.root_end_ratio = (r_ratio,)
        self.root_end_coner_length = length
        return self

    def set_rect_root_end_chamfer(self, length, w=0., h=0.):
        self.set_rect_root_end_chamfered_ratio(
            length=length,
            x_ratio=(self.width()-w)/self.width(),
            y_ratio=(self.height()-h)/self.height())
        return self
    
    def set_pole_root_end_chamfer(self, r=0., length=0.):
        self.set_pole_root_end_chamfered_ratio(
            length=length,
            r_ratio=(self.radius()-r)/self.radius())
        return self

    # set chamfer: tip end
    def set_rect_tip_end_chamfered_ratio(self, length, w_ratio=1., h_ratio=1.):
        self.tip_end_ratio = (w_ratio,h_ratio)
        self.tip_end_coner_length = length
        return self
    
    def set_pole_tip_end_chamfered_ratio(self, length, r_ratio=1.):
        self.tip_end_ratio = (r_ratio,)
        self.tip_end_coner_length = length
        return self

    def set_rect_tip_end_chamfer(self, length, w=0., h=0.):
        self.set_rect_tip_end_chamfered_ratio(
            x_ratio=(self.width()-w)/self.width(),
            y_ratio=(self.height()-h)/self.height(),
            length=length)
        return self
    
    def set_pole_tip_end_chamfer(self, length, r=0.):
        self.set_pole_tip_end_chamfered_ratio(
            length=length,
            r_ratio=(self.radius()-r)/self.radius())
        return self
    
    # set chamfer: both end
    def set_rect_end_chamfered_ratio(self, length, w_ratio=1., h_ratio=1.):
        self.set_rect_root_end_chamfered_ratio(length,w_ratio,h_ratio)
        self.set_rect_tip_end_chamfered_ratio(length,w_ratio,h_ratio)
        return self
    
    def set_pole_end_chamfered_ratio(self, length, r_ratio=1.):
        self.set_pole_root_end_chamfered_ratio(length,r_ratio)
        self.set_pole_tip_end_chamfered_ratio(length,r_ratio)
        return self

    def set_rect_end_chamfer(self, length, w=0., h=0.):
        self.set_rect_root_end_chamfer(length,w,h)
        self.set_rect_tip_end_chamfer(length,w,h)
        return self
    
    def set_pole_end_chamfer(self, length, r=0.):
        self.set_pole_root_end_chamfer(length,r)
        self.set_pole_tip_end_chamfer(length,r)
        return self
    
    # move
    def needs_move(self):
        return None != self.move_xyz

    def move_x(self):
        if not self.needs_move(): return 0.
        return self.move_xyz[0]
    
    def move_y(self):
        if not self.needs_move(): return 0.
        return self.move_xyz[1]
    
    def move_z(self):
        if not self.needs_move(): return 0.
        return self.move_xyz[2]
    
    def set_move_xyz(self,x=0.,y=0.,z=0.):
        self.move_xyz = (x,y,z)
        return self
    
    # rotation
    def needs_rotation(self):
        return None != self.list_rotation_yz
    
    def add_list_rotation_yz(self, list_rotation_yz):
        if self.list_rotation_yz == None: self.list_rotation_yz = []
        self.list_rotation_yz = self.list_rotation_yz + list_rotation_yz
        return self

    def add_rotation_x(self, x_axis_rotation):
        self.add_list_rotation_yz([(x_axis_rotation, -np.pi/2), (0., np.pi/2)])
        return self
