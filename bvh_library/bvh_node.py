import os
from pathlib import Path

class BvhNode(object):
    def __init__(
        self, name, offset, rotation_order,
        children=None, parent=None, is_root=False, is_end_site=False
    ):
        if not is_end_site and \
          rotation_order not in ['xyz', 'xzy', 'yxz', 'yzx', 'zxy', 'zyx']:
            raise ValueError(f'Rotation order invalid.')
        self.name = name
        self.offset = offset
        self.rotation_order = rotation_order
        self.children = children if children is not None else []
        self.parent = parent
        self.is_root = is_root
        self.is_end_site = is_end_site

class BvhHeader(object):
    def __init__(self, root, nodes):
        self.root = root
        self.nodes = nodes