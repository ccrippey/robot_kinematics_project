import math
import numpy as np

def rot2d_deg(theta):
    theta_rad = math.radians(theta)
    
    R = np.array([[math.cos(theta_rad), -math.sin(theta_rad)],
                 [math.sin(theta_rad), math.cos(theta_rad)]])
    
    return R

def transformation2d(R, d):
    T = np.eye(3) 
    T[:2, :2] = R
    T[:2, 2] = d 
    return T

def forward_kinematics_2D_2link(a1, a2, theta, x_origin, y_origin, theta_origin):
    T0 = transformation2d(rot2d_deg(theta_origin), np.array([0, 0]).T)
    T1 = transformation2d(rot2d_deg(theta), np.array([a1, 0]).T)
    T2 = transformation2d(rot2d_deg(0), np.array([a2, 0]).T)

    origin0_translated = np.array([x_origin, y_origin])
    origin0 = np.array([0, 0, 1])
    origin1 = T0 @ T1 @ origin0
    origin2 = T0 @ T1 @ T2 @ origin0
    points = []
    points.extend(origin0[:2] + origin0_translated)
    points.extend(origin1[:2] + origin0_translated)
    points.extend(origin2[:2] + origin0_translated)

    return points

if __name__ == "__main__":
    print("Testing forward kinematics")

    T = transformation2d(rot2d_deg(90), np.array([3, 0]).T)
    origin = np.array([5, 1, 1])
    print(T@origin)
    print(forward_kinematics_2D_2link(1, 1, 90, 4, 4, 90))