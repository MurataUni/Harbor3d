from harbor3d import Dock, Shipwright
import numpy as np
import os

def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    fname = path.split(os.sep)[-1] + '.stl'

    sw = Shipwright(Dock())

    obj = sw.load_submodule(os.path.join(path, 'load_obj1')).align_keel_size_to_monocoque_shell()
    sw.parent(obj).rotate(np.pi/3., 0).load_submodule(os.path.join(path, 'load_obj2'))

    # sw.start_display()
    sw.generate_stl_binary(path, fname, divided=False)

if __name__ == "__main__":
    main()