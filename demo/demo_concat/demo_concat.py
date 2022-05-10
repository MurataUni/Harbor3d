from harbor3d import Dock, Shipwright
from harbor3d.util.concat_util import ConcatConfig, Concatinator
from harbor3d.util import stl_delete_shell_util
import os
import glob
import numpy as np

def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    fname_added = path.split(os.sep)[-1] + '_added.stl'
    fname_temp = path.split(os.sep)[-1] + '_temp.stl'
    fname_cleared = path.split(os.sep)[-1] + '_cleared.stl'
    sw = Shipwright(Dock())

    cube = sw.cube(2.)
    rectangular = sw.parent(cube,0.5).rectangular(2., 3., 4.)
    pole = sw.parent(rectangular,0.9).pole(1., 0.5, 2*np.pi, 16, True)
    pole_half = sw.parent(pole,0.5).pole(1., 0.5, 2*np.pi*3/4, 16)
    sphere = sw.parent(pole_half,0.5).sphere(2., 16, 16)
    sw.parent(sphere,0.5).spheroid(4., 1., 16, 32)

    sw.generate_stl_binary(path, fname_added)

    list_fname = []
    if os.path.exists(os.path.join(path, "divided")):
        list_fname = glob.glob(os.path.join(path, "divided/*.stl"))
    if 0 == len(list_fname):
        return

    sw = Shipwright(Dock())
    catConfig = ConcatConfig(0.1, 0.1)
    c = Concatinator(catConfig, sw)
    c.init_shells_data(list_fname)
    c.border_data_load()
    c.output(os.path.join(path, fname_temp))
    stl_delete_shell_util.delete_separated_shell(sw, path, fname_temp, fname_cleared, (0,0,-1))

if __name__ == "__main__":
    main()