"""
=========================================================
vehicle3d.py

Author : Eshan Sengupta

Mesh factory for the MTi-8 vehicle model.

Provides create_vehicle() which returns an
Open3D TriangleMesh that the SceneManager updates.
=========================================================
"""

import copy

import numpy as np
import open3d as o3d

import config


class Vehicle3D:

    def __init__(self):

        self.pose = np.eye(4)

        self._base_mesh = self._build_vehicle()

    # -----------------------------------------------------

    def _build_vehicle(self):

        body = o3d.geometry.TriangleMesh.create_box(
            width=0.25,
            height=0.6,
            depth=0.15
        )

        body.compute_vertex_normals()

        body.paint_uniform_color(
            config.VEHICLE_COLOR
        )

        body.translate(
            [-0.125, -0.30, -0.075]
        )

        nose = o3d.geometry.TriangleMesh.create_cone(
            radius=0.07,
            height=0.25
        )

        nose.compute_vertex_normals()

        nose.paint_uniform_color(
            [0.2, 0.2, 0.2]
        )

        nose.rotate(
            body.get_rotation_matrix_from_xyz(
                (-np.pi / 2, 0, 0)
            )
        )

        nose.translate(
            [0.0, 0.30, 0.0]
        )

        body += nose

        return body

    # -----------------------------------------------------

    def create_vehicle(self):

        return copy.deepcopy(self._base_mesh)

    # -----------------------------------------------------

    def set_pose(self, transform):

        self.pose = transform.copy()

    # -----------------------------------------------------

    def reset(self):

        self.pose = np.eye(4)


# ==========================================================
# Standalone Test
# ==========================================================

if __name__ == "__main__":

    import math

    vis = o3d.visualization.Visualizer()

    vis.create_window("Vehicle3D Test")

    opt = vis.get_render_option()

    opt.background_color = np.asarray(
        config.BACKGROUND_COLOR
    )

    vehicle = Vehicle3D()

    mesh = vehicle.create_vehicle()

    vis.add_geometry(mesh)

    world = o3d.geometry.TriangleMesh.create_coordinate_frame(
        size=2.0
    )

    vis.add_geometry(world)

    angle = 0

    try:

        while True:

            T = np.eye(4)

            c = math.cos(angle)

            s = math.sin(angle)

            T[:3, :3] = np.array(
                [
                    [c, -s, 0],
                    [s, c, 0],
                    [0, 0, 1]
                ]
            )

            T[0, 3] = math.cos(angle) * 2

            T[1, 3] = math.sin(angle) * 2

            mesh2 = vehicle.create_vehicle()

            mesh2.transform(T)

            vis.remove_geometry(mesh, reset_bounding_box=False)

            mesh = mesh2

            vis.add_geometry(mesh, reset_bounding_box=False)

            vis.poll_events()

            vis.update_renderer()

            angle += 0.01

    except KeyboardInterrupt:

        vis.destroy_window()
