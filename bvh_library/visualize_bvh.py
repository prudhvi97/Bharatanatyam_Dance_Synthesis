import json
from pythreejs import *
import numpy as np

def create_bone(bone, parent=None):
    bone_geometry = CylinderBufferGeometry(1, 1, bone["length"], 8, 1)
    bone_material = MeshBasicMaterial(color="blue")
    bone_mesh = Mesh(bone_geometry, bone_material)

    if parent:
        parent.add(bone_mesh)
        bone_mesh.position.set(0, bone["length"] / 2, 0)
    else:
        scene.add(bone_mesh)

    if "children" in bone:
        for child in bone["children"]:
            create_bone(child, bone_mesh)

# Load BVH file
with open("your_animation.bvh", "r") as f:
    bvh_data = json.load(f)

# Create scene
scene = Scene()

# Create bones
for bone in bvh_data["bones"]:
    create_bone(bone)

# Set up camera
camera = PerspectiveCamera(75, 1, 0.1, 1000)
camera.position.z = 5

# Set up renderer
renderer = Renderer(camera=camera, scene=scene, controls=[OrbitControls(camera)])
renderer.width = 800
renderer.height = 800

# Display the renderer
renderer.render()
