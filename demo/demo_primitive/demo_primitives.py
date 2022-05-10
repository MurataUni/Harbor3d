from harbor3d import Dock, Shipwright
import numpy as np
import os

def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    fname = path.split(os.sep)[-1] + '.stl'
    sw = Shipwright(Dock())

    cube = sw.cube(2.)

    rectangular = sw.parent(cube).rectangular(2., 3., 4.)

    pole = sw.parent(rectangular).pole(1., 0.5, 2*np.pi, 16, True)

    pole_half = sw.parent(pole).pole(1., 0.5, 2*np.pi*3/4, 16)

    sphere = sw.parent(pole_half).sphere(2., 16, 16)

    sw.parent(sphere).spheroid(4., 1., 16, 32)

    # sw.start_display()
    sw.generate_stl_binary(path, fname, divided=False)

if __name__ == "__main__":
    main()