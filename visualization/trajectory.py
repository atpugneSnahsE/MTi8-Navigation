"""
trajectory.py

Trajectory Manager

Maintains the GNSS/RTK trajectory in ENU coordinates,
computes statistics, supports exporting and smoothing.
"""

import csv
import math
import numpy as np


class Trajectory:

    def __init__(self):

        self.points = []

        self.timestamps = []

        self.total_distance = 0.0

        self.last_point = None

    def clear(self):

        self.points.clear()

        self.timestamps.clear()

        self.total_distance = 0.0

        self.last_point = None

    def add_point(self, x, y, z=0.0, timestamp=None):

        point = np.array(
            [x, y, z],
            dtype=float
        )

        if self.last_point is not None:

            self.total_distance += np.linalg.norm(
                point - self.last_point
            )

        self.points.append(point)

        self.timestamps.append(timestamp)

        self.last_point = point

    def update_from_navigation_state(self, state, local_position):
        if local_position is not None:
            self.add_point(
                local_position[0],
                local_position[1],
                local_position[2],
                state.gnss.utc if state else None
            )

    def __len__(self):

        return len(self.points)

    def empty(self):

        return len(self.points) == 0

    def first(self):

        if self.empty():
            return None

        return self.points[0]

    def last(self):

        if self.empty():
            return None

        return self.points[-1]

    def distance(self):

        return self.total_distance

    def displacement(self):

        if len(self.points) < 2:
            return 0.0

        return np.linalg.norm(
            self.points[-1] -
            self.points[0]
        )

    def heading(self):

        if len(self.points) < 2:
            return None

        dx = self.points[-1][0] - self.points[-2][0]

        dy = self.points[-1][1] - self.points[-2][1]

        return math.degrees(
            math.atan2(
                dx,
                dy
            )
        )

    def bounding_box(self):

        if self.empty():

            return None

        pts = np.asarray(
            self.points
        )

        minimum = pts.min(axis=0)

        maximum = pts.max(axis=0)

        return minimum, maximum

    def centroid(self):

        if self.empty():

            return None

        return np.mean(
            np.asarray(
                self.points
            ),
            axis=0
        )

    def numpy(self):

        if self.empty():

            return np.zeros(
                (0, 3)
            )

        return np.asarray(
            self.points
        )

    def smoothed(self, window=5):

        if len(self.points) < window:

            return self.numpy()

        pts = self.numpy()

        result = []

        for i in range(len(pts)):

            start = max(
                0,
                i - window
            )

            end = min(
                len(pts),
                i + window + 1
            )

            result.append(
                pts[start:end].mean(
                    axis=0
                )
            )

        return np.asarray(
            result
        )

    def export_csv(self, filename):

        with open(
            filename,
            "w",
            newline=""
        ) as f:

            writer = csv.writer(f)

            writer.writerow(
                [
                    "Time",
                    "East",
                    "North",
                    "Up"
                ]
            )

            for t, p in zip(
                self.timestamps,
                self.points
            ):

                writer.writerow(
                    [
                        t,
                        p[0],
                        p[1],
                        p[2]
                    ]
                )

    def export_xyz(self, filename):

        np.savetxt(
            filename,
            self.numpy(),
            fmt="%.6f"
        )

    def statistics(self):

        return {

            "points": len(self),

            "distance": self.distance(),

            "displacement": self.displacement(),

            "heading": self.heading(),

            "centroid": self.centroid(),

            "bbox": self.bounding_box()

        }

    def print_statistics(self):

        stats = self.statistics()

        print()

        print("=" * 60)

        print("TRAJECTORY")

        print("=" * 60)

        print(

            "Points       :",

            stats["points"]

        )

        print(

            "Distance     :",

            f"{stats['distance']:.3f} m"

        )

        print(

            "Displacement :",

            f"{stats['displacement']:.3f} m"

        )

        print(

            "Heading      :",

            stats["heading"]

        )

        print(

            "Centroid     :",

            stats["centroid"]

        )

        print("=" * 60)

    def __repr__(self):

        return (

            f"Trajectory("

            f"{len(self.points)} points, "

            f"{self.total_distance:.2f} m)"

        )


if __name__ == "__main__":

    import random

    traj = Trajectory()

    x = 0

    y = 0

    for i in range(100):

        x += random.uniform(-0.3, 0.3)

        y += random.uniform(-0.3, 0.3)

        traj.add_point(
            x,
            y,
            0,
            i
        )

    traj.print_statistics()

    traj.export_csv(
        "trajectory.csv"
    )
