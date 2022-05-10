from harbor3d import Dock, Shipwright
import numpy as np
import os

def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    fname = path.split(os.sep)[-1] + '.stl'
    sw = Shipwright(Dock())

    obj1 = sw.void(50.)
    obj1.add_rib_load_bmp(0., os.path.join(path, "test.bmp"), 5, 0.1)
    obj1.add_rib_load_bmp(0.2, os.path.join(path, "test.bmp"), 5, 0.1)
    obj1.add_rib_load_bmp(0.4, os.path.join(path, "test2.bmp"), 5, 0.1)
    obj1.add_rib_load_bmp(0.5, os.path.join(path, "test2.bmp"), 5, 0.1)
    obj1.add_rib_load_bmp(0.6, os.path.join(path, "test3.bmp"), 5, 0.05)
    obj1.add_rib_load_bmp(0.7, os.path.join(path, "test3.bmp"), 5, 0.05)
    obj1.add_rib_load_bmp(0.8, os.path.join(path, "test.bmp"), 5, 0.1, 3)
    obj1.add_rib_load_bmp(1., os.path.join(path, "test.bmp"), 5, 0.1, 3)

    # sw.start_display()
    sw.generate_stl_binary(path, fname, divided=False)

if __name__ == "__main__":
    main()