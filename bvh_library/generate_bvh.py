import argparse
import os
import numpy as np
from skeleton import Skeleton
from process_coordinates import get_poses_3d
from modify_bvh import modify_bvh_content

def moving_average(data, window_size):
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

def smooth_poses_3d(poses_3d, window_size):
    num_frames, num_joints, _ = poses_3d.shape
    # Initialize the smoothed poses_3d array with NaNs to handle the reduced size after moving average
    smoothed_poses_3d = np.full((num_frames, num_joints, 3), np.nan)

    # Apply moving average to each joint coordinate
    for joint_index in range(num_joints):
        for coordinate_index in range(3):  # X, Y, Z coordinates
            smoothed_data = moving_average(poses_3d[:, joint_index, coordinate_index], window_size)
            # Fill the smoothed data back into the array, centered
            start_index = window_size // 2
            end_index = start_index + len(smoothed_data)
            smoothed_poses_3d[start_index:end_index, joint_index, coordinate_index] = smoothed_data

    return smoothed_poses_3d

def process_file(filename):
    # Step 1: Generate poses_3d from the specified text file
    poses_3d = get_poses_3d(filename)
    #print("filename: "+filename)
    num_frames = len(poses_3d)
    num_joints = len(poses_3d[0])
    
    # Step 2: Use poses_3d to generate a BVH file
    file_name_without_ext = os.path.splitext(os.path.basename(filename))[0]
    #print("filename no ext: " + file_name_without_ext)

    output_bvh_file = f'{file_name_without_ext}.bvh'
    skeleton = Skeleton()


    #Step 3: Smoothen 3D coordinates with moving average
    # Define the window size for the moving average
    window_size = 5

    # Apply the smoothing function to the entire poses_3d array
    poses_3d_smoothed = smooth_poses_3d(poses_3d, window_size)

    for joint_index in range(num_joints):
        for coordinate_index in range(3):
            # Forward fill
            nan_indices = np.where(np.isnan(poses_3d_smoothed[:, joint_index, coordinate_index]))[0]
            if nan_indices.size > 0 and nan_indices[0] == 0:
                next_valid_index = np.where(~np.isnan(poses_3d_smoothed[:, joint_index, coordinate_index]))[0][0]
                poses_3d_smoothed[:next_valid_index, joint_index, coordinate_index] = poses_3d_smoothed[next_valid_index, joint_index, coordinate_index]

            # Backward fill
            nan_indices = np.where(np.isnan(poses_3d_smoothed[:, joint_index, coordinate_index]))[0]
            if nan_indices.size > 0 and nan_indices[-1] == len(poses_3d_smoothed[:, joint_index, coordinate_index]) - 1:
                last_valid_index = np.where(~np.isnan(poses_3d_smoothed[:, joint_index, coordinate_index]))[0][-1]
                poses_3d_smoothed[last_valid_index + 1:, joint_index, coordinate_index] = poses_3d_smoothed[last_valid_index, joint_index, coordinate_index]

    channels, header = skeleton.poses2bvh(poses_3d_smoothed, output_file=output_bvh_file)
    print(f"BVH file generated and saved to {output_bvh_file}")

    # Step 4: Modify the generated BVH file
    modified_bvh_file = modify_bvh_content(output_bvh_file)  # Adjust this function call based on your setup in modify_bvh.py
    print(f"Modified BVH file saved as {modified_bvh_file}")

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Generate BVH file from 3D pose data in all text files within a specified folder.")
    parser.add_argument('--foldername', required=True, help="Folder containing the 3D pose data files.")
    
    # Parse arguments
    args = parser.parse_args()

    # Process each .txt file in the folder
    for filename in os.listdir(args.foldername):
        if filename.endswith(".txt"):
            full_path = os.path.join(args.foldername, filename)
            print(f"Processing {full_path}...")
            process_file(full_path)

if __name__ == "__main__":
    main()
