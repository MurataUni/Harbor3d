from harbor3d import Dock, Shipwright
import numpy as np
import os

# subtract function is incomplete, it contains many bugs
def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    fname = path.split(os.sep)[-1] + '.stl'
    sw = Shipwright(Dock())

    base = sw.rotate(np.pi/2, 0.).void(5.)

    # object1
    cube1 = sw.parent(base,0.).cube(2.)

    beam = sw.parent(base, 0).rotate(0.,np.pi/6).void(1.)
    rectangular = sw.parent(beam).rotate(np.pi/4).rectangular(2., 1., 4.)

    cube1.subtracts.append(rectangular)

    # object2
    cube2 = sw.parent(base,1.).cube(2.)
    turn = sw.parent(cube2).void(1.)
    cube_sub = sw.parent(turn).rotate(np.pi, np.pi/4).rectangular(1.5, 1.5, 3.5)
    cube2.subtracts.append(cube_sub)

    # sw.start_display()
    sw.generate_stl(path, fname)

if __name__ == "__main__":
    main()
