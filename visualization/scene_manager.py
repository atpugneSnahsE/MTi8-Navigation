"""
scene_manager.py

Central Open3D Scene Manager

Reads pose and trajectory from NavigationState + XbusParser.
"""

import copy
import time

import open3d as o3d
import numpy as np

import config

from visualization.vehicle3d import Vehicle3D
from visualization.coordinate_frames import CoordinateFrames
from visualization.trajectory import Trajectory


class SceneManager:

    def __init__(self):

        self.vis = None
        self._scene_available = False

        if not config.ENABLE_SCENE_VIEWER:
            print("3D scene viewer disabled; running without Open3D window.")
            return

        try:
            self.vis = o3d.visualization.Visualizer()

            self.vis.create_window(

                "MTi-8 Navigation",

                width=config.WINDOW_WIDTH,

                height=config.WINDOW_HEIGHT

            )

            option = self.vis.get_render_option()

            option.background_color = np.asarray(

                config.BACKGROUND_COLOR

            )

            option.point_size = config.TRAJECTORY_POINT_SIZE

            self.vehicle = Vehicle3D()

            self.frames = CoordinateFrames()

            self.trajectory = Trajectory()

            self._base_mesh = self.vehicle.create_vehicle()

            self._display_mesh = copy.deepcopy(self._base_mesh)

            self.world = self.frames.world_frame()

            self.body = self.frames.body_frame()

            self.path = o3d.geometry.PointCloud()
            self._path_added = False

            self.vis.add_geometry(self.world)

            self.vis.add_geometry(self._display_mesh)

            self.vis.add_geometry(self.body)

            axis = o3d.geometry.TriangleMesh.create_coordinate_frame(
                size=2.0,
                origin=[0, 0, 0]
            )

            self.vis.add_geometry(axis)

            self.set_camera()

            self._last_pose = None
            self._last_body_pose = None
            self._scene_available = True

        except Exception as exc:
            print(f"Open3D scene unavailable: {exc}")
            self.vis = None
            self._scene_available = False

    def set_camera(self):

        if not self._scene_available:
            return

        ctr = self.vis.get_view_control()

        ctr.set_zoom(0.7)

        ctr.set_front([1, -1, 0.8])

        ctr.set_up([0, 0, 1])

    def update(self, nav_state, parser):

        if not self._scene_available:
            return True

        self._update_pose(parser)

        self._update_trajectory(parser)

        alive = self.vis.poll_events()

        self.vis.update_renderer()

        return alive

    def _get_vehicle_pose(self, parser):
        q = parser.get_quaternion()
        T = q.to_homogeneous_matrix() if q else None
        position = parser.get_local_position()
        if T is not None and position is not None:
            T[0, 3] = position[0]
            T[1, 3] = position[1]
            T[2, 3] = position[2]
        return T, position

    def _update_pose(self, parser):
        transform, position = self._get_vehicle_pose(parser)
        if transform is not None:
            self._update_vehicle_mesh(transform)
            self._update_body_frame(transform)

    def _update_vehicle_mesh(self, new_pose):

        if self._last_pose is not None:
            inv_prev = np.linalg.inv(self._last_pose)
            self._display_mesh.transform(inv_prev)

        self._display_mesh.transform(new_pose)

        self._last_pose = new_pose.copy()

        self.vis.update_geometry(self._display_mesh)

    def _update_body_frame(self, new_pose):

        if self._last_body_pose is not None:
            inv_prev = np.linalg.inv(self._last_body_pose)
            self.body.transform(inv_prev)

        self.body.transform(new_pose)

        self._last_body_pose = new_pose.copy()

        self.vis.update_geometry(self.body)

    def _update_trajectory(self, parser):
        position = parser.get_local_position()
        if position is not None:
            self.trajectory.add_point(
                position[0],
                position[1],
                position[2]
            )
        self._update_path()

    def _update_path(self):

        points = self.trajectory.numpy()

        if len(points):

            self.path.points = o3d.utility.Vector3dVector(
                points
            )

            colors = np.zeros(
                (len(points), 3)
            )

            colors[:] = config.TRAJECTORY_COLOR

            self.path.colors = o3d.utility.Vector3dVector(
                colors
            )

            if not self._path_added:

                self.vis.add_geometry(self.path, reset_bounding_box=False)

                self._path_added = True

            else:

                self.vis.update_geometry(
                    self.path
                )

    def run(self):

        if not self._scene_available:
            return

        while True:

            alive = self.vis.poll_events()

            if not alive:
                break

            self.vis.update_renderer()

            time.sleep(
                1 / config.GUI_UPDATE_RATE
            )

        self.destroy()

    def destroy(self):

        if self.vis is not None:
            self.vis.destroy_window()
