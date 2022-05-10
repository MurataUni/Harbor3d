from harbor3d import Dock, Shipwright
import numpy as np
import os

# This function is incomplete yet
def main():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)))

    sw = Shipwright(Dock())
    sw.spin([(1., 1.), (1., 0.), (0., 0.), (0., 1.)], 1., 16)

    # sw.start_display()
    sw.generate_stl_binary(path, "spin_object.stl", divided=False)

if __name__ == "__main__":
    main()
