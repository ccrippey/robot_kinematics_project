import math
import numpy as np


# Input: rotation in degrees
# Output: 2x2 Rotation matrix representing a 2d rotation by this amount
def rot2d(theta):
    R = np.array([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])

    return R


# Input: Rotation Matrix, displacement vector
# Output: 3x3 Homogeneous transformation matrix combining the rotation matrix and displacement
def transformation2d(R, d):
    T = np.eye(3)
    T[:2, :2] = R
    T[:2, 2] = d
    return T


# Input: a1, a2 - Link lengths; x0, y0 - base location of 2link actuator; theta1, theta2 - joint angle of base link and second link respectively
# Output: [x0, y0, x1, y1, x2 y2] - x and y coords of manipulator base, end of link 1, and end of link 2
def forward_kinematics_2D_2link(a1, a2, x0, y0, theta1, theta2):
    T0 = transformation2d(rot2d(theta1), np.array([0, 0]).T)
    T1 = transformation2d(rot2d(theta2), np.array([a1, 0]).T)
    T2 = transformation2d(rot2d(0), np.array([a2, 0]).T)

    origin0_translated = np.array([x0, y0])
    origin0 = np.array([0, 0, 1])
    origin1 = T0 @ T1 @ origin0
    origin2 = T0 @ T1 @ T2 @ origin0
    points = []
    points.extend(origin0[:2] + origin0_translated)  # x0 y0
    points.extend(origin1[:2] + origin0_translated)  # x1 y1
    points.extend(origin2[:2] + origin0_translated)  # x2 y2

    return points


if __name__ == "__main__":
    print("Testing forward kinematics")

    T = transformation2d(rot2d(90), np.array([3, 0]).T)
    origin = np.array([5, 1, 1])
    print(T @ origin)
    print(forward_kinematics_2D_2link(1, 1, 4, 4, 90, 90))
