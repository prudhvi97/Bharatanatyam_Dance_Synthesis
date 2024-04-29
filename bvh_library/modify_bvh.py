import argparse

def change_joint_names(bvh_content, old_name, new_name):
    return bvh_content.replace(old_name, new_name)

def add_end_sites(input_text):
    lines = input_text.split('\n')
    output_lines = []
    previous_line_was_channels = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('CHANNELS'):
            previous_line_was_channels = True
            indent_level_channels = line.index(stripped[0])
        elif stripped.startswith('}') and previous_line_was_channels:
            output_lines.append(' ' * indent_level_channels + 'End Site')
            output_lines.append(' ' * indent_level_channels + '{')
            output_lines.append(' ' * (indent_level_channels + 4) + 'OFFSET 0 0 0')
            output_lines.append(' ' * indent_level_channels + '}')
            previous_line_was_channels = False

        output_lines.append(line)

    return '\n'.join(output_lines)


def modify_bvh_content(input_bvh_file):
    with open(input_bvh_file, "r") as file:
        bvh_content = file.read()

    # Specify the changes to joint names here
    changes = [
        ("ROOT HipCenter", "ROOT Hips"),
        ("JOINT HipLeft", "JOINT LeftUpLeg"),
        ("JOINT KneeLeft", "JOINT LeftLeg"),
        ("JOINT AnkleLeft", "JOINT LeftFoot"),
        ("JOINT FootLeft", "JOINT LeftToeBase"),
        ("JOINT HipRight", "JOINT RightUpLeg"),
        ("JOINT KneeRight", "JOINT RightLeg"),
        ("JOINT AnkleRight", "JOINT RightFoot"),
        ("JOINT FootRight", "JOINT RightToeBase"),
        ("JOINT Spine", "JOINT Spine"),
        ("JOINT Spine1", "JOINT Spine1"),
        ("JOINT Spine2", "JOINT Spine2"),
        ("JOINT Spine3", "JOINT Spine3"),
        ("JOINT Spine4", "JOINT Spine4"),
        ("JOINT ShoulderRight", "JOINT RightShoulder"),
        ("JOINT ElbowRight", "JOINT RightArm"),
        ("JOINT WristRight", "JOINT RightForeArm"),
        ("JOINT HandRight", "JOINT RightHand"),
        ("JOINT ShoulderLeft", "JOINT LeftShoulder"),
        ("JOINT ElbowLeft", "JOINT LeftArm"),
        ("JOINT WristLeft", "JOINT LeftForeArm"),
        ("JOINT HandLeft", "JOINT LeftHand"),
        ("JOINT ShoulderCenter", "JOINT Neck"),
        ("JOINT Head", "JOINT Head"),
    ]

    for old_name, new_name in changes:
        bvh_content = change_joint_names(bvh_content, old_name, new_name)

    bvh_content = add_end_sites(bvh_content)

    output_file_end = input_bvh_file.replace('.bvh', '_end.bvh')
    with open(output_file_end, "w") as file:
        file.write(bvh_content)

    return output_file_end

def main():
    parser = argparse.ArgumentParser(description='Modify BVH file content.')
    parser.add_argument('--filename', required=True, help='Path to the BVH file to modify.')
    args = parser.parse_args()

    modified_bvh_file = modify_bvh_content(args.filename)
    print(f"Modified BVH file saved as {modified_bvh_file}")

if __name__ == "__main__":
    main()
