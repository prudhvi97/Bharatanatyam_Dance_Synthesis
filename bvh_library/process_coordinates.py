import numpy as np
import argparse
from scipy.spatial.transform import Rotation
import decimal

def get_poses_3d(file_path):
    decimal.getcontext().prec = 16
    data = []

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                data.append(line)

    frame_list = []
    for fdata in data:
        frame_joint_coordinates = {}
        fdata_list = eval(fdata)
        for item in fdata_list:
            joint_data = item.split(': ')
            joint = joint_data[0]
            coordinates = joint_data[1].strip('[]').split(', ')
            x, y, z = [float(c) for c in coordinates]
            frame_joint_coordinates[joint] = np.array([x, y, z])
        frame_list.append(frame_joint_coordinates)

    # Assuming frame_list is a list of dictionaries containing joint coordinates
    num_frames = len(frame_list)
    num_joints = len(frame_list[0])  # Assuming all frames have the same number of joints

    # Initialize poses_3d array
    poses_3d = np.zeros((num_frames, num_joints, 3))

    # Create a dictionary to map joint names to indices
    joint_indices = {
        'HipCenter': 0, 'Spine': 1, 'Spine1': 2, 'Spine2': 3, 'Spine3': 4, 'Spine4': 5,
        'ShoulderCenter': 6, 'Head': 7, 'ShoulderLeft': 8, 'ElbowLeft': 9, 'WristLeft': 10, 'HandLeft': 11,
        'ShoulderRight': 12, 'ElbowRight': 13, 'WristRight': 14, 'HandRight': 15, 'HipLeft': 16, 'KneeLeft': 17,
        'AnkleLeft': 18, 'FootLeft': 19, 'HipRight': 20, 'KneeRight': 21, 'AnkleRight': 22, 'FootRight': 23
    }

    for frame_index, frame in enumerate(frame_list):
        for joint_name, joint_coordinates in frame.items():
            joint_index = joint_indices[joint_name]
            x, y, z = joint_coordinates
            # Scaling by 156
            poses_3d[frame_index, joint_index] = [x*156, y*156, z*156]

    return poses_3d

def main():
    parser = argparse.ArgumentParser(description='Process 3D joint coordinates to generate poses_3d data.')
    parser.add_argument('--filename', required=True, help='Path to the input file containing joint coordinates.')
    
    args = parser.parse_args()
    file_path = args.filename

    # Generate poses_3d from the specified file
    poses_3d = get_poses_3d(file_path)
    
    print("Generated poses_3d data from:", file_path)
    # Further processing can be done with poses_3d here

if __name__ == '__main__':
    main()
