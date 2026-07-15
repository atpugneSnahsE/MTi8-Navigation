"""
=========================================================
coordinate_frames.py

Author : Eshan Sengupta

Coordinate Frame Utilities

Provides

    • World Frame
    • Vehicle Body Frame
    • ENU Frame
    • NED Frame
    • ECEF Frame
    • Transformation Utilities

=========================================================
"""

import numpy as np
import open3d as o3d
import math


class CoordinateFrames:

    EARTH_RADIUS = 6378137.0

    def __init__(self):

        self.world = o3d.geometry.TriangleMesh.create_coordinate_frame(
            size=2.0
        )

        self.body = o3d.geometry.TriangleMesh.create_coordinate_frame(
            size=1.0
        )

        self.enu = o3d.geometry.TriangleMesh.create_coordinate_frame(
            size=1.5
        )

        self.ned = o3d.geometry.TriangleMesh.create_coordinate_frame(
            size=1.5
        )

        self.origin = None

    # --------------------------------------------------

    def set_origin(self, latitude, longitude, altitude):

        self.origin = (

            latitude,

            longitude,

            altitude

        )

    # --------------------------------------------------

    def body_frame(self):

        return self.body

    # --------------------------------------------------

    def world_frame(self):

        return self.world

    # --------------------------------------------------

    def enu_frame(self):

        return self.enu

    # --------------------------------------------------

    def ned_frame(self):

        return self.ned

    # --------------------------------------------------

    def update_body(self, transform):

        frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
            size=1.0
        )

        frame.transform(transform)

        self.body = frame

    # --------------------------------------------------

    def update_enu(self, transform):

        frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
            size=1.5
        )

        frame.transform(transform)

        self.enu = frame

    # --------------------------------------------------

    def update_ned(self, transform):

        frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
            size=1.5
        )

        frame.transform(transform)

        self.ned = frame

    # --------------------------------------------------

    def geodetic_to_ecef(self, lat, lon, h):

        lat = math.radians(lat)

        lon = math.radians(lon)

        a = 6378137.0

        e2 = 6.69437999014e-3

        N = a / np.sqrt(

            1 -

            e2 *

            np.sin(lat) ** 2

        )

        x = (

            N + h

        ) * np.cos(lat) * np.cos(lon)

        y = (

            N + h

        ) * np.cos(lat) * np.sin(lon)

        z = (

            N *

            (1 - e2) +

            h

        ) * np.sin(lat)

        return np.array(

            [

                x,

                y,

                z

            ]

        )

    # --------------------------------------------------

    def ecef_to_enu(self, ecef):

        if self.origin is None:

            return None

        lat0 = math.radians(

            self.origin[0]

        )

        lon0 = math.radians(

            self.origin[1]

        )

        origin = self.geodetic_to_ecef(

            *self.origin

        )

        d = ecef - origin

        R = np.array([

            [

                -np.sin(lon0),

                np.cos(lon0),

                0

            ],

            [

                -np.sin(lat0) * np.cos(lon0),

                -np.sin(lat0) * np.sin(lon0),

                np.cos(lat0)

            ],

            [

                np.cos(lat0) * np.cos(lon0),

                np.cos(lat0) * np.sin(lon0),

                np.sin(lat0)

            ]

        ])

        return R @ d

    # --------------------------------------------------

    def enu_to_ecef(self, enu):

        if self.origin is None:

            return None

        lat0 = math.radians(

            self.origin[0]

        )

        lon0 = math.radians(

            self.origin[1]

        )

        origin = self.geodetic_to_ecef(

            *self.origin

        )

        R = np.array([

            [

                -np.sin(lon0),

                -np.sin(lat0) * np.cos(lon0),

                np.cos(lat0) * np.cos(lon0)

            ],

            [

                np.cos(lon0),

                -np.sin(lat0) * np.sin(lon0),

                np.cos(lat0) * np.sin(lon0)

            ],

            [

                0,

                np.cos(lat0),

                np.sin(lat0)

            ]

        ])

        return origin + R @ enu

    # --------------------------------------------------

    def transformation_matrix(

        self,

        position,

        rotation

    ):

        T = np.eye(4)

        T[:3, :3] = rotation

        T[:3, 3] = position

        return T

    # --------------------------------------------------

    def transform_points(

        self,

        points,

        transform

    ):

        pts = np.asarray(points)

        ones = np.ones(

            (

                pts.shape[0],

                1

            )

        )

        pts = np.hstack(

            [

                pts,

                ones

            ]

        )

        transformed = (

            transform @ pts.T

        ).T

        return transformed[:, :3]

    # --------------------------------------------------

    def rotation_x(self, angle):

        c = np.cos(angle)

        s = np.sin(angle)

        return np.array([

            [1, 0, 0],

            [0, c, -s],

            [0, s, c]

        ])

    # --------------------------------------------------

    def rotation_y(self, angle):

        c = np.cos(angle)

        s = np.sin(angle)

        return np.array([

            [c, 0, s],

            [0, 1, 0],

            [-s, 0, c]

        ])

    # --------------------------------------------------

    def rotation_z(self, angle):

        c = np.cos(angle)

        s = np.sin(angle)

        return np.array([

            [c, -s, 0],

            [s, c, 0],

            [0, 0, 1]

        ])

    # --------------------------------------------------

    def euler_to_rotation(

        self,

        roll,

        pitch,

        yaw

    ):

        roll = math.radians(roll)

        pitch = math.radians(pitch)

        yaw = math.radians(yaw)

        Rx = self.rotation_x(roll)

        Ry = self.rotation_y(pitch)

        Rz = self.rotation_z(yaw)

        return Rz @ Ry @ Rx

    # --------------------------------------------------

    def body_transform(

        self,

        position,

        roll,

        pitch,

        yaw

    ):

        R = self.euler_to_rotation(

            roll,

            pitch,

            yaw

        )

        return self.transformation_matrix(

            position,

            R

        )

    # --------------------------------------------------

    def update_from_parser(self, parser):

        pose = parser.get_vehicle_pose()

        if pose is None:

            return

        T = pose["transform"]

        if T is None:

            return

        self.update_body(T)

    # --------------------------------------------------

    def all_frames(self):

        return [

            self.world,

            self.body,

            self.enu,

            self.ned

        ]


# ==========================================================
# Standalone Test
# ==========================================================

if __name__ == "__main__":

    cf = CoordinateFrames()

    cf.set_origin(

        54.7215,

        25.3376,

        200

    )

    print("CoordinateFrames initialized successfully.")