import numpy as np

from xsens.quaternion import Quaternion


class IMUParser:

    def __init__(self):
        self.state = None

    def update(self, navigation_state):
        self.state = navigation_state

    @property
    def available(self):
        return self.state is not None

    @property
    def quaternion(self):
        return self.state.quaternion if self.available else None

    @property
    def roll(self):
        return self.state.roll if self.available else None

    @property
    def pitch(self):
        return self.state.pitch if self.available else None

    @property
    def yaw(self):
        return self.state.yaw if self.available else None

    @property
    def acceleration(self):
        return self.state.acceleration if self.available else None

    @property
    def free_acceleration(self):
        return self.state.free_acceleration if self.available else None

    @property
    def gyro(self):
        return self.state.gyro if self.available else None

    @property
    def gyro_hr(self):
        return self.state.gyro_hr if self.available else None

    @property
    def delta_q(self):
        return self.state.delta_q if self.available else None

    @property
    def delta_v(self):
        return self.state.delta_v if self.available else None

    @property
    def magnetic(self):
        return self.state.magnetic if self.available else None

    @property
    def pressure(self):
        return self.state.pressure if self.available else None

    @property
    def temperature(self):
        return self.state.temperature if self.available else None

    @property
    def packet_counter(self):
        return self.state.packet_counter if self.available else None

    @property
    def sample_time(self):
        return self.state.sample_time if self.available else None

    @property
    def filter_valid(self):
        return self.state.filter_valid if self.available else False

    @property
    def gnss_valid(self):
        return self.state.gnss_valid if self.available else False

    @property
    def rtk_status(self):
        return self.state.rtk_state if self.available else 0

    @property
    def utc(self):
        return self.state.utc if self.available else None

    def get_rotation_matrix(self):
        if self.quaternion is None:
            return np.eye(3)
        return self.quaternion.to_rotation_matrix()

    def get_transform(self):
        if self.quaternion is None:
            return np.eye(4)
        return self.quaternion.to_homogeneous_matrix()

    def rotate_vector(self, vector):
        if self.quaternion is None:
            return vector
        return self.quaternion.rotate_vector(vector)

    def is_stationary(self):
        if self.gyro is None:
            return False
        gx, gy, gz = self.gyro
        return np.linalg.norm([gx, gy, gz]) < 0.01

    def acceleration_magnitude(self):
        if self.acceleration is None:
            return None
        return float(np.linalg.norm(self.acceleration))

    def gyro_magnitude(self):
        if self.gyro is None:
            return None
        return float(np.linalg.norm(self.gyro))

    def magnetic_magnitude(self):
        if self.magnetic is None:
            return None
        return float(np.linalg.norm(self.magnetic))

    def gravity_vector(self):
        if self.quaternion is None:
            return np.array([0.0, 0.0, 9.81])
        return self.rotate_vector(np.array([0.0, 0.0, 9.81]))

    def body_axes(self):
        R = self.get_rotation_matrix()
        return R[:, 0], R[:, 1], R[:, 2]

    def health(self):
        return {
            "orientation": self.quaternion is not None,
            "acceleration": self.acceleration is not None,
            "gyro": self.gyro is not None,
            "magnetic": self.magnetic is not None,
            "pressure": self.pressure is not None,
            "temperature": self.temperature is not None,
            "filter_valid": self.filter_valid,
            "gnss_valid": self.gnss_valid
        }

    def as_dict(self):
        return {
            "utc": self.utc,
            "packet_counter": self.packet_counter,
            "sample_time": self.sample_time,
            "roll": self.roll,
            "pitch": self.pitch,
            "yaw": self.yaw,
            "quaternion": self.quaternion,
            "acceleration": self.acceleration,
            "free_acceleration": self.free_acceleration,
            "gyro": self.gyro,
            "gyro_hr": self.gyro_hr,
            "delta_q": self.delta_q,
            "delta_v": self.delta_v,
            "magnetic": self.magnetic,
            "pressure": self.pressure,
            "temperature": self.temperature,
            "filter_valid": self.filter_valid,
            "gnss_valid": self.gnss_valid,
            "rtk_status": self.rtk_status
        }

    def __repr__(self):
        return (
            f"IMUParser("
            f"Roll={self.roll}, "
            f"Pitch={self.pitch}, "
            f"Yaw={self.yaw})"
        )
