import numpy as np
from bvh_node import BvhNode, BvhHeader
from math_utils import dcm_from_axis, dcm2quat, quat_divide, quat2euler
from bvh_writer import write_bvh
class Skeleton(object):

    def __init__(self):
        self.root = 'HipCenter'
        self.keypoint2index = {
            'HipCenter': 0,
            'Spine': 1,
            'Spine1': 2,
            'Spine2': 3,
            'Spine3': 4,
            'Spine4': 5,
            'ShoulderCenter': 6,
            'Head': 7,
            'ShoulderLeft': 8,
            'ElbowLeft': 9,
            'WristLeft': 10,
            'HandLeft': 11,
            'ShoulderRight': 12,
            'ElbowRight': 13,
            'WristRight': 14,
            'HandRight': 15,
            'HipLeft': 16,
            'KneeLeft': 17,
            'AnkleLeft': 18,
            'FootLeft': 19,
            'HipRight': 20,
            'KneeRight': 21,
            'AnkleRight': 22,
            'FootRight': 23
        }


        
        self.index2keypoint = {v: k for k, v in self.keypoint2index.items()}
        self.keypoint_num = len(self.keypoint2index)

        #children, parents, and initial directions
        self.children = {
            "HipCenter": ["HipLeft", "HipRight", "Spine"],
            "HipLeft": ["KneeLeft"],
            "KneeLeft": ["AnkleLeft"],
            "AnkleLeft": ["FootLeft"],
            "FootLeft": [],
            "HipRight": ["KneeRight"],
            "KneeRight": ["AnkleRight"],
            "AnkleRight": ["FootRight"],
            "FootRight": [],
            "Spine": ["Spine1"],
            "Spine1": ["Spine2"],
            "Spine2": ["Spine3"],
            "Spine3": ["Spine4"],
            "Spine4": ["ShoulderRight", "ShoulderLeft", "ShoulderCenter"],
            "ShoulderRight": ["ElbowRight"],
            "ElbowRight": ["WristRight"],
            "WristRight": ["HandRight"],
            "HandRight": [],
            "ShoulderLeft": ["ElbowLeft"],
            "ElbowLeft": ["WristLeft"],
            "WristLeft": ["HandLeft"],
            "HandLeft": [],
            "ShoulderCenter": ["Head"],
            "Head": []
        }

        self.parent = {self.root: None}
        for parent, children in self.children.items():
            for child in children:
                self.parent[child] = parent

        self.left_joints = [
            joint for joint in self.keypoint2index
            if 'Left' in joint
        ]
        self.right_joints = [
            joint for joint in self.keypoint2index
            if 'Right' in joint
        ]

        # T-pose
        self.initial_directions = {
            'HipCenter': [0, 0, 0],
            'Spine': [0, 0, 1],
            'Spine1': [0, 0, 1],
            'Spine2': [0, 0, 1],
            'Spine3': [0, 0, 1],
            'Spine4': [0, 0, 1],
            'ShoulderCenter': [0, 0, 1],
            'Head': [0, 0, 1],
            'ShoulderLeft': [1, 0, 0],
            'ElbowLeft': [1, 0, 0],
            'WristLeft': [1, 0, 0],
            'HandLeft': [1, 0, 0],
            'ShoulderRight': [-1, 0, 0],
            'ElbowRight': [-1, 0, 0],
            'WristRight': [-1, 0, 0],
            'HandRight': [-1, 0, 0],
            'HipLeft': [1, 0, 0],
            'KneeLeft': [0, 0, -1],
            'AnkleLeft': [0, 0, -1],
            'FootLeft': [0, -1, 0],
            'HipRight': [-1, 0, 0],
            'KneeRight': [0, 0, -1],
            'AnkleRight': [0, 0, -1],
            'FootRight': [0, -1, 0]
        }

    def get_initial_offset(self, poses_3d):
        # TODO: RANSAC
        bone_lens = {self.root: [0]}
        stack = [self.root]
        while stack:
            parent = stack.pop()
            p_idx = self.keypoint2index[parent]
            p_name = parent
            while p_idx == -1:
                # find real parent
                p_name = self.parent[p_name]
                p_idx = self.keypoint2index[p_name]
            for child in self.children[parent]:
                stack.append(child)

                if self.keypoint2index[child] == -1:
                    bone_lens[child] = [0.1]
                else:
                    c_idx = self.keypoint2index[child]
                    bone_lens[child] = np.linalg.norm(
                        poses_3d[:, p_idx] - poses_3d[:, c_idx],
                        axis=1
                    )

        bone_len = {}
        for joint in self.keypoint2index:
            if 'Left' in joint or 'Right' in joint:
                base_name = joint.replace('Left', '').replace('Right', '')
                left_len = np.mean(bone_lens[base_name + 'Left'])
                right_len = np.mean(bone_lens[base_name + 'Right'])
                bone_len[joint] = (left_len + right_len) / 2
            else:
                bone_len[joint] = np.mean(bone_lens[joint])

        initial_offset = {}
        for joint, direction in self.initial_directions.items():
            direction = np.array(direction) / max(np.linalg.norm(direction), 1e-12)
            initial_offset[joint] = direction * bone_len[joint]

        return initial_offset

    def get_bvh_header(self, poses_3d):
        initial_offset = self.get_initial_offset(poses_3d)

        nodes = {}
        for joint in self.keypoint2index:
            is_root = joint == self.root
            is_end_site = 'EndSite' in joint
            nodes[joint] = BvhNode(
                name=joint,
                offset=initial_offset[joint],
                rotation_order='zxy' if not is_end_site else '',
                is_root=is_root,
                is_end_site=is_end_site,
            )
        for joint, children in self.children.items():
            nodes[joint].children = [nodes[child] for child in children]
            for child in children:
                nodes[child].parent = nodes[joint]

        header = BvhHeader(root=nodes[self.root], nodes=nodes)
        return header


    def pose2euler(self, pose, header):
        channel = []
        quats = {}
        eulers = {}
        stack = [header.root]
        while stack:
            node = stack.pop()
            joint = node.name
            joint_idx = self.keypoint2index[joint]

            if node.is_root:
                channel.extend(pose[joint_idx])

            index = self.keypoint2index
            order = None
            if joint == 'HipCenter':
                x_dir = pose[index['HipLeft']] - pose[index['HipRight']]
                y_dir = None
                z_dir = pose[index['Spine']] - pose[joint_idx]
                order = 'zyx'
            elif joint in ['HipRight', 'KneeRight']:
                child_idx = self.keypoint2index[node.children[0].name]
                x_dir = pose[index['HipCenter']] - pose[index['HipRight']]
                y_dir = None
                z_dir = pose[joint_idx] - pose[child_idx]
                order = 'zyx'
            elif joint in ['HipLeft', 'KneeLeft']:
                child_idx = self.keypoint2index[node.children[0].name]
                x_dir = pose[index['HipLeft']] - pose[index['HipCenter']]
                y_dir = None
                z_dir = pose[joint_idx] - pose[child_idx]
                order = 'zyx'
            elif joint == 'Spine':
                x_dir = pose[index['HipLeft']] - pose[index['HipRight']]
                y_dir = None
                z_dir = pose[index['ShoulderCenter']] - pose[joint_idx]
                order = 'zyx'
            elif joint == 'ShoulderCenter':
                x_dir = pose[index['ShoulderLeft']] - pose[index['ShoulderRight']]
                y_dir = None
                z_dir = pose[joint_idx] - pose[index['Spine']]
                order = 'zyx'
            elif joint == 'ShoulderLeft':
                x_dir = pose[index['ElbowLeft']] - pose[joint_idx]
                y_dir = pose[index['ElbowLeft']] - pose[index['WristLeft']]
                z_dir = None
                order = 'xzy'
            elif joint == 'ElbowLeft':
                x_dir = pose[index['WristLeft']] - pose[joint_idx]
                y_dir = pose[joint_idx] - pose[index['ShoulderLeft']]
                z_dir = None
                order = 'xzy'
            elif joint == 'ShoulderRight':
                x_dir = pose[joint_idx] - pose[index['ElbowRight']]
                y_dir = pose[index['ElbowRight']] - pose[index['WristRight']]
                z_dir = None
                order = 'xzy'
            elif joint == 'ElbowRight':
                x_dir = pose[joint_idx] - pose[index['WristRight']]
                y_dir = pose[joint_idx] - pose[index['ShoulderRight']]
                z_dir = None
                order = 'xzy'
            elif joint == 'WristRight':
                child_idx = self.keypoint2index[self.children[joint][0]]
                x_dir = pose[index['ElbowRight']] - pose[index[joint]]
                y_dir = pose[index[joint]] - pose[index['HandRight']]
                z_dir = pose[index[joint]] - pose[child_idx]
                order = 'xzy'
            elif joint == 'WristLeft':
                child_idx = self.keypoint2index[self.children[joint][0]]
                x_dir = pose[index[joint]] - pose[index['ElbowLeft']]
                y_dir = pose[index['HandLeft']] - pose[index[joint]]
                z_dir = pose[index[joint]] - pose[child_idx]
                order = 'xzy'
            elif joint == 'AnkleRight':
                child_idx = self.keypoint2index[self.children[joint][0]]
                x_dir = pose[index['KneeRight']] - pose[index[joint]]
                y_dir = None
                z_dir = pose[index[joint]] - pose[child_idx]
                order = 'zyx'
            elif joint == 'AnkleLeft':
                child_idx = self.keypoint2index[self.children[joint][0]]
                x_dir = pose[index[joint]] - pose[index['KneeLeft']]
                y_dir = None
                z_dir = pose[index[joint]] - pose[child_idx]
                order = 'zyx'



            if order:
                dcm = dcm_from_axis(x_dir, y_dir, z_dir, order)
                quats[joint] = dcm2quat(dcm)
            else:
                quats[joint] = quats[self.parent[joint]].copy()

            local_quat = quats[joint].copy()
            if node.parent:
                local_quat = quat_divide(
                    q=quats[joint], r=quats[node.parent.name]
                )

            euler = quat2euler(
                q=local_quat, order=node.rotation_order
            )
            euler = np.rad2deg(euler)
            eulers[joint] = euler
            channel.extend(euler)

            for child in node.children[::-1]:
                if not child.is_end_site:
                    stack.append(child)

        return channel


    def poses2bvh(self, poses_3d, header=None, output_file=None):
        if not header:
            header = self.get_bvh_header(poses_3d)

        channels = []
        for frame, pose in enumerate(poses_3d):
            channels.append(self.pose2euler(pose, header))

        if output_file:
            write_bvh(output_file, header, channels)

        return channels, header

