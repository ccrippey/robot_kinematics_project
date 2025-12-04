import math
import numpy as np
from src.kinematics.projection2d import project_point
from src.kinematics.forward_kinematics import rot3y

# Input: a1, a2 - link lengths; x_base, y_base - location of 2link base; x_end, y_end - location of target position
# Output: theta1, theta2 - 2link angles
def inverse_kinematics_2D_2link(a1, a2, x_base, y_base, x_end, y_end):
    Px = x_end - x_base
    Py = y_end - y_base
    r_p = math.sqrt(Px**2 + Py**2)
    r_lim = a1 + a2
    solution = []
    if (r_p > r_lim):
        theta2 = 0
        theta1 = math.atan2(Py,Px)
        solution.append((theta1,theta2))
    elif (Px**2 + Py**2) - (a1 - a2)**2 < 1e-3:
        theta2 = math.pi
        theta1 = math.atan2(Py,Px)
        solution.append((theta1,theta2))
    else:
        theta2 = 2*math.atan(math.sqrt( ((a1 + a2)**2 - (Px**2 + Py**2))/( (Px**2 + Py**2) - (a1 - a2)**2 ) ))
        theta2_alt = -1*theta2
        theta1 = math.atan2(Py,Px) - math.atan2(a2*math.sin(theta2), a1+a2*math.cos(theta2))
        theta1_alt = math.atan2(Py,Px) - math.atan2(a2*math.sin(theta2_alt), a1+a2*math.cos(theta2_alt))
        solution.append((theta1,theta2))
        solution.append((theta1_alt,theta2_alt))

    return solution

def inverse_kinematics_3D_2link(a1, a2, base3, end3):
    Px = end3[0] - base3[0]
    Pz = end3[2] - base3[2]

    solutions = []
    # Use the yaw that aligns the target with +X for the 2D IK plane, but flip
    # the sign before passing to forward kinematics to match its frame.
    yaw_plane = math.atan2(Pz, Px)
    yaw_planes = [yaw_plane, -yaw_plane]
    for yaw_plane in yaw_planes:
        hip_yaw = -yaw_plane
        end3_shifted = np.array(end3)-np.array(base3)
        end3_shifted_projected = rot3y(yaw_plane) @ end3_shifted.T
        hip_roll = 0
        for hip_pitch, knee_pitch in inverse_kinematics_2D_2link(a1, a2, 0, 0, end3_shifted_projected[0], end3_shifted_projected[1]):
            solutions.append((hip_yaw, hip_pitch, hip_roll, knee_pitch))

    return solutions

def choose_best_solution_3d(solutions, limb_id):
    best_soln = solutions[0]
    for soln in solutions:
        if (limb_id == "left_leg" or limb_id == "right_leg") and soln[1] > best_soln[1]: #Find biggest hip pitch
            best_soln = soln
    return best_soln
