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
    if (r_p > r_lim):
        theta2 = 0
        theta1 = math.atan2(Py,Px)
    elif (Px**2 + Py**2) - (a1 - a2)**2 < 1e-3:
        theta2 = math.pi
        theta1 = math.atan2(Py,Px)
    else:
        theta2 = 2*math.atan(math.sqrt( ((a1 + a2)**2 - (Px**2 + Py**2))/( (Px**2 + Py**2) - (a1 - a2)**2 ) ))
        #theta2_alt = -1*theta2 #Negative soln ignored for now
        theta1 = math.atan2(Py,Px) - math.atan2(a2*math.sin(theta2), a1+a2*math.cos(theta2))

    return (theta1, theta2)

def inverse_kinematics_3D_2link(a1, a2, base3, end3):
    Px = end3[0] - base3[0]
    Py = end3[1] - base3[1]
    Pz = end3[2] - base3[2]
    hip_yaw = math.atan2(Pz, Px)

    
    end_relative = np.array(end3)-np.array(base3)
    end2 = rot3y(hip_yaw) @ end_relative.T
    hip_pitch, knee_pitch = inverse_kinematics_2D_2link(a1, a2, 0,0, end2[0], end2[1])
    hip_roll = 0

    return (hip_yaw, hip_pitch, hip_roll, knee_pitch)