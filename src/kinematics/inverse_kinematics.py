import math
import numpy as np

# Input: a1, a2 - link lengths; x_base, y_base - location of 2link base; x_end, y_end - location of target position
# Output: theta1, theta2 - 2link angles
def inverse_kinematics_2D_2link(a1, a2, x_base, y_base, x_end, y_end):
    Px = x_end - x_base
    Py = y_end - y_base
    r_p = math.sqrt(Px**2 + Py**2)
    r_lim = math.sqrt(a1**2 + a2**2)

    if (r_p >= r_lim - 1e-6):
        theta2 = 0
        theta1 = math.atan2(Py,Px)
    else:
        theta2 = 2*math.atan(math.sqrt( ((a1 + a2)**2 - (Px**2 + Py**2))/( (Px**2 + Py**2) - (a1 - a2)**2 ) ))
        #theta2_alt = -1*theta2 #Negative soln ignored for now
        theta1 = math.atan2(Py,Px) - math.atan2(a2*math.sin(theta2), a1+a2*math.cos(theta2))

    return (theta1, theta2)