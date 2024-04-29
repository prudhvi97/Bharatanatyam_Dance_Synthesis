import os
import sys
import scipy.io
import re
from pathlib import Path

check_empty = 0.0
def extract_coordinates_from_mat(mat_file_path):
    # Load the MAT file
    mat_data = scipy.io.loadmat(mat_file_path)
    skeleton_frames = mat_data['SkeletonFrame']

    # Extract the X, Y, and Z coordinates
    coordinates = []
    for frame in skeleton_frames:
        for i in range(0, 20):
            part = frame[0][2][0][0][4][i]
            joint_name = part[0][0][0]
            x = part[0][1][0][0][0][0][0]
            y = part[0][1][0][0][1][0][0]
            z = part[0][1][0][0][2][0][0]
            check_empty = x+y+z
            coordinate_str = f"{joint_name}: [{x}, {y}, {z}]"
            if joint_name == 'Spine':
                Scoord = (x,y,z)
            elif joint_name == 'ShoulderCenter':
                SCcoord = (x,y,z)
                val = 0
                for cords in insert_points_between_coordinates(Scoord,SCcoord):
                    val = val+1
                    jx,jy,jz = cords
                    joint_coordinate_str = f"Spine{val}: [{jx}, {jy}, {jz}]"
                    coordinates.append(joint_coordinate_str)
            coordinates.append(coordinate_str)

    # print(coordinates)
    if check_empty == 0.0:
        return []
    else:
        check_empty = 0.0
        return coordinates

#Insert missing spines data
def insert_points_between_coordinates(coord1, coord2):
    x1, y1, z1 = coord1
    x2, y2, z2 = coord2

    # Calculate the distances between the coordinates
    distance_x = x2 - x1
    distance_y = y2 - y1
    distance_z = z2 - z1

    points = []
    for i in range(1, 5):
        # Calculate the intermediate coordinates based on relative distances
        x = x1 + (i / 5) * distance_x
        y = y1 + (i / 5) * distance_y
        z = z1 + (i / 5) * distance_z
        points.append((x, y, z))

    return points

def get_numeric_value(filename):
    # Extract the numeric part of the file name
    file_number = filename.split("_")[-1].split(".")[0]
    try:
        return int(file_number)
    except ValueError:
        return float('inf')


def process_folder(folder_path, output_file_path):
    # Get all .mat files in the folder
    mat_files = [file for file in os.listdir(folder_path) if file.endswith('.mat')]

    mat_files.sort(key=get_numeric_value)
    with open(output_file_path, 'w') as output_file:
        for file in mat_files:
            file_path = os.path.join(folder_path, file)
            coordinates = extract_coordinates_from_mat(file_path)
            # Check if the coordinates list is not empty
            if coordinates:
                output_file.write(str(coordinates))
                output_file.write("\n")

folder_names = ['7_paikkal', '8_tei_tei_dhatta', '9_katti_kartari', '10_utsanga', '11_mandi', '12_sarrikkal', '13_tirmana', '14_sarika', '15_joining']

for folder_name in folder_names:
    base_folder_path = Path(f'E:/Adavus_Session_1/Kinect1/{folder_name}')
    for folder in range(1, 9):
        for dancer in range(1, 4):
            folder_path = base_folder_path / str(folder) / f'Dancer{dancer}'
            folder_path_str = str(folder_path)
            output_file_path = f'coordinates_{folder_name}_{folder}_D{dancer}.txt'

            if folder_path.exists():
                print(f"Started processing {folder_path_str}")
                process_folder(folder_path_str, output_file_path)
                print(f"Completed processing {folder_path_str}, Created {output_file_path}")
            else:
                print(f"Error: {folder_path_str} does not exist. Skipping to next iteration.")


