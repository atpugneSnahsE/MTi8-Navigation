"""
Quaternion Mathematics for MTi-8 Navigation System
"""

import math


class Quaternion:

    def __init__(self, w=1.0, x=0.0, y=0.0, z=0.0):
        self.w = float(w)
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def copy(self):
        return Quaternion(self.w, self.x, self.y, self.z)

    def as_array(self):
        import numpy as np
        return np.array([self.w, self.x, self.y, self.z], dtype=np.float64)

    def magnitude(self):
        return math.sqrt(self.w * self.w + self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self):
        n = self.magnitude()
        if n == 0:
            return Quaternion()
        return Quaternion(self.w / n, self.x / n, self.y / n, self.z / n)

    def conjugate(self):
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def inverse(self):
        c = self.conjugate()
        n = self.magnitude() ** 2
        return Quaternion(c.w / n, c.x / n, c.y / n, c.z / n)

    def multiply(self, q):
        w = self.w * q.w - self.x * q.x - self.y * q.y - self.z * q.z
        x = self.w * q.x + self.x * q.w + self.y * q.z - self.z * q.y
        y = self.w * q.y - self.x * q.z + self.y * q.w + self.z * q.x
        z = self.w * q.z + self.x * q.y - self.y * q.x + self.z * q.w
        return Quaternion(w, x, y, z)

    def to_rotation_matrix(self):
        import numpy as np
        q = self.normalize()
        w, x, y, z = q.w, q.x, q.y, q.z
        return np.array([
            [1 - 2 * (y*y + z*z), 2 * (x*y - z*w),     2 * (x*z + y*w)],
            [2 * (x*y + z*w),     1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
            [2 * (x*z - y*w),     2 * (y*z + x*w),     1 - 2 * (x*x + y*y)],
        ])

    def to_homogeneous_matrix(self):
        import numpy as np
        R = self.to_rotation_matrix()
        T = np.eye(4)
        T[:3, :3] = R
        return T

    def to_euler(self):
        q = self.normalize()
        w, x, y, z = q.w, q.x, q.y, q.z

        sinr = 2 * (w * x + y * z)
        cosr = 1 - 2 * (x * x + y * y)
        roll = math.atan2(sinr, cosr)

        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        siny = 2 * (w * z + x * y)
        cosy = 1 - 2 * (y * y + z * z)
        yaw = math.atan2(siny, cosy)

        return (math.degrees(roll), math.degrees(pitch), math.degrees(yaw))

    def rotate_vector(self, vector):
        import numpy as np
        vector = np.asarray(vector, dtype=np.float64)
        R = self.to_rotation_matrix()
        return R @ vector

    def __str__(self):
        return f"Quaternion({self.w:.6f}, {self.x:.6f}, {self.y:.6f}, {self.z:.6f})"


def quaternion_from_array(array):
    return Quaternion(array[0], array[1], array[2], array[3])

def quaternion_from_float32(data):
    return Quaternion(*data)

def quaternion_from_float64(data):
    return Quaternion(*data)

def identity():
    return Quaternion(1.0, 0.0, 0.0, 0.0)

def wrap_angle(angle):
    while angle > 180: angle -= 360
    while angle < -180: angle += 360
    return angle

def wrap_euler(roll, pitch, yaw):
    return (wrap_angle(roll), wrap_angle(pitch), wrap_angle(yaw))
