from harbor3d import Dock, Shipwright
import numpy as np
import os

def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    fname_ascii = path.split(os.sep)[-1] + '_ascii.stl'
    fname_binary = path.split(os.sep)[-1] + '_binary.stl'

    sw = Shipwright(Dock())

    edges = sw.rib_edges_rectangular_from_edges((1., -1.),(1., -1.))

    obj = sw.void(10.)
    obj.add_rib(0., edges)
    obj.add_rib(0.2, [(0.,0.)])
    obj.add_rib(0.4, [(0.,0.)])
    obj.add_rib(0.6, edges)
    obj.add_rib(0.8, edges)
    obj.add_rib(1., [(0.,0.)])

    obj2 = sw.rotate(np.pi/4).parent(obj).void(10.)
    obj2.add_rib(0., [(0.,0.)])
    obj2.add_rib(0.2, edges)
    obj2.add_rib(0.4, edges)
    obj2.add_rib(0.6, [(0.,0.)])
    obj2.add_rib(0.8, [(0.,0.)])
    obj2.add_rib(1., edges)

    # sw.start_display()
    sw.generate_stl(path, fname_ascii) # write_stl側の検証
    sw.generate_stl_binary(path, fname_binary, divided=False) # convert_to_monocoque側の検証

if __name__ == "__main__":
    main()