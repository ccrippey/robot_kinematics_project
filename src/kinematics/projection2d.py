from typing import Tuple, Iterable
import math
import numpy as np

def project_point(point3d: Tuple[float, float, float], z_rotation: float, center) -> Tuple[float, float]:

    E = np.array([[math.cos(math.radians(z_rotation)), 0, math.sin(math.radians(z_rotation))],
                  [0, 1, 0],
                  [-math.sin(math.radians(z_rotation)), 0, math.cos(math.radians(z_rotation))]])
    # print(E)
    point2d = E @ (np.array(point3d))

    return center[0]*float(point2d[0])+center[0]/2, center[1]*float(point2d[1])+center[1]/2, float(point2d[2])


def back_project(point2d: Tuple[float, float], z_rotation: float = 0.0, depth: float = 0.0, window=(0,0)) -> Tuple[float, float, float]:
    e1 = [math.cos(math.radians(z_rotation)), -math.sin(math.radians(z_rotation)), 0]
    e2 = [math.sin(math.radians(z_rotation)), math.cos(math.radians(z_rotation)), 0]
    e3 = [0, 0, 1]
    E = np.array([[math.cos(math.radians(z_rotation)), 0, math.sin(math.radians(z_rotation))],
                  [0, 1, 0],
                  [-math.sin(math.radians(z_rotation)), 0, math.cos(math.radians(z_rotation))]])
    point2d_scaled = [(point2d[0]-window[0]/2)/window[0], (point2d[1]-window[1]/2)/window[1]]
    point2d_augmented = [point2d_scaled[0], point2d_scaled[1], depth]
    point3 = E.T @ np.array(point2d_augmented)

    return float(point3[0]), float(point3[1]), float(point3[2])


def project_points(points: Iterable[Tuple[float, float, float]], z_rotation: float = 0.0) -> list:
    return [project_point(p, z_rotation) for p in points]


def test_simple_projection():
    print("=== test_simple_projection ===")
    window = (800, 600)
    z_rot = -90.0

    pts = [
        (0.0, 0.0, 0.0),
        (0.5, 0.5, 0.0),
        (-0.5, -0.5, 0.0),
    ]
    # for p in pts:
    #     u, v = project_point(p, z_rot, window)
    #     print(f"3D {p} -> 2D ({u:.2f}, {v:.2f})")

    #     x, y, z = back_project((u,v), z_rot, p[0], window)
    #     print(x, y, z)

    pts = [
        (317, 150),
        (480, 120)
    ]
    for p in pts:
        x, y, z = back_project(p, 0, 0, window)
        print(x, y, z)

        u, v = project_point((x,y,z), 90, window)
        print(f"3D {(x,y,z)} -> 2D ({u:.2f}, {v:.2f})")

        x, y, z = back_project(p, 0, 90, window)
        print(x, y, z)

if __name__ == "__main__":
    test_simple_projection()