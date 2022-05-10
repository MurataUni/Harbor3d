from harbor3d import Dock, Shipwright
import numpy as np
import os

def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    fname = path.split(os.sep)[-1] + ".stl"

    sw = Shipwright(Dock())
    pole = sw.pole(20., 5., 2 * np.pi, 32, True)
    sw.parent(pole).rotate(-np.pi/3., 0).pole(20., 5., 2 * np.pi, 32, True)

    sw.generate_stl_binary(path, 'load_obj.stl')

if __name__ == "__main__":
    main()