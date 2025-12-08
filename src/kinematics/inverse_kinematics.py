import math
import numpy as np
from src.kinematics.projection2d import project_point
from src.kinematics.forward_kinematics import rot3y, rot3x, rot3z


# Input: a1, a2 - link lengths; x_base, y_base - location of 2link base; x_end, y_end - location of target position
# Output: theta1, theta2 - 2link angles
def inverse_kinematics_2D_2link(a1, a2, x_base, y_base, x_end, y_end):
    Px = x_end - x_base
    Py = y_end - y_base
    r_p = math.sqrt(Px**2 + Py**2)
    r_lim = a1 + a2
    solution = []
    if r_p > r_lim:
        theta2 = 0
        theta1 = math.atan2(Py, Px)
        solution.append((theta1, theta2))
    elif (Px**2 + Py**2) - (a1 - a2) ** 2 < 1e-3:
        theta2 = math.pi
        theta1 = math.atan2(Py, Px)
        solution.append((theta1, theta2))
    else:
        theta2 = 2 * math.atan(math.sqrt(((a1 + a2) ** 2 - (Px**2 + Py**2)) / ((Px**2 + Py**2) - (a1 - a2) ** 2)))
        theta2_alt = -1 * theta2
        theta1 = math.atan2(Py, Px) - math.atan2(a2 * math.sin(theta2), a1 + a2 * math.cos(theta2))
        theta1_alt = math.atan2(Py, Px) - math.atan2(a2 * math.sin(theta2_alt), a1 + a2 * math.cos(theta2_alt))
        solution.append((theta1, theta2))
        solution.append((theta1_alt, theta2_alt))

    return solution


def inverse_kinematics_3D_2link(a1, a2, base3, end3, limb_id):

    if limb_id == "left_arm" or limb_id == "right_arm":
        Px = end3[0] - base3[0]
        Pz = end3[2] - base3[2]

        solutions = []
        yaw = math.atan2(Pz, Px)
        yaw_planes = [yaw, yaw + math.pi]
        for yaw_plane in yaw_planes:
            hip_yaw = -yaw_plane
            end3_shifted = np.array(end3) - np.array(base3)
            end3_shifted_projected = rot3y(yaw_plane) @ end3_shifted.T
            hip_roll = 0
            for hip_pitch, knee_pitch in inverse_kinematics_2D_2link(
                a1, a2, 0, 0, end3_shifted_projected[0], end3_shifted_projected[1]
            ):
                solutions.append((hip_yaw, hip_pitch, hip_roll, knee_pitch))
    else:  # Actually Leg This shit don't work
        Px = end3[0] - base3[0]
        Py = end3[1] - base3[1]

        solutions = []
        roll = math.atan2(Py, Px)
        roll_planes = [roll, roll + math.pi]
        for roll_plane in roll_planes:
            hip_roll = -roll_plane
            end3_shifted = np.array(end3) - np.array(base3)
            end3_shifted_projected = rot3z(roll_plane) @ end3_shifted.T
            hip_yaw = math.pi / 2.0
            for hip_pitch, knee_pitch in inverse_kinematics_2D_2link(
                a1, a2, 0, 0, end3_shifted_projected[0], end3_shifted_projected[1]
            ):
                solutions.append((hip_yaw, hip_pitch, hip_roll, knee_pitch))
        pass
    return solutions


def choose_best_solution_3d(solutions, limb_id):
    best_soln = solutions[0]
    for soln in solutions:
        if (limb_id == "left_leg" or limb_id == "right_leg") and soln[1] > best_soln[1]:  # Find biggest hip pitch
            best_soln = soln
    return best_soln


def cart_to_joint_config(cart_config):
    """Convert CartesianStickConfig to JointStickConfig using IK.

    Args:
        cart_config: CartesianStickConfig with normalized 3D positions

    Returns:
        JointStickConfig with joint angles and origin positions
    """
    from src.kinematics.stick_config import JointStickConfig, JointLimbConfig, LIMB_LENGTH_RATIOS

    limb_configs = []
    limb_names = ["left_arm", "right_arm", "left_leg", "right_leg"]
    origins = [cart_config.shoulder, cart_config.shoulder, cart_config.pelvis, cart_config.pelvis]
    targets = [cart_config.hand_left, cart_config.hand_right, cart_config.foot_left, cart_config.foot_right]

    for limb_name, origin, target in zip(limb_names, origins, targets):
        a1_ratio, a2_ratio = LIMB_LENGTH_RATIOS[limb_name]

        solutions = inverse_kinematics_3D_2link(a1_ratio, a2_ratio, origin, target, limb_name)
        hip_yaw, hip_pitch, hip_roll, knee_pitch = choose_best_solution_3d(solutions, limb_name)

        limb_configs.append(
            JointLimbConfig(hip_yaw=hip_yaw, hip_pitch=hip_pitch, hip_roll=hip_roll, knee_pitch=knee_pitch)
        )

    return JointStickConfig(
        shoulder=cart_config.shoulder,
        pelvis=cart_config.pelvis,
        left_arm=limb_configs[0],
        right_arm=limb_configs[1],
        left_leg=limb_configs[2],
        right_leg=limb_configs[3],
    )
