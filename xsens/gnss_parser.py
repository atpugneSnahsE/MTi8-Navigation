import math

import config


class GNSSParser:

    def __init__(self):
        self.state = None
        self.trajectory = []

    def update(self, navigation_state):
        self.state = navigation_state

    def set_navigation_state(self, navigation_state):
        self.state = navigation_state

    @property
    def available(self):
        return self.state is not None and self.state.is_valid()

    @property
    def latitude(self):
        return self.state.latitude if self.available else None

    @property
    def longitude(self):
        return self.state.longitude if self.available else None

    @property
    def altitude(self):
        return self.state.altitude if self.available else None

    @property
    def speed(self):
        return self.state.ground_speed if self.available else None

    @property
    def heading(self):
        return self.state.heading_motion if self.available else None

    @property
    def heading_vehicle(self):
        return self.state.heading_vehicle if self.available else None

    @property
    def satellites(self):
        return self.state.num_sv if self.available else None

    @property
    def fix_type(self):
        return self.state.fix_type if self.available else None

    @property
    def horizontal_accuracy(self):
        return self.state.horizontal_accuracy if self.available else None

    @property
    def vertical_accuracy(self):
        return self.state.vertical_accuracy if self.available else None

    @property
    def hdop(self):
        return self.state.hdop if self.available else None

    @property
    def vdop(self):
        return self.state.vdop if self.available else None

    @property
    def pdop(self):
        return self.state.pdop if self.available else None

    @property
    def carrier_phase(self):
        return self.state.carrier_state if self.available else None

    @property
    def corrections_applied(self):
        return self.state.differential if self.available else None

    @property
    def utc(self):
        return self.state.utc if self.available else None

    @property
    def velocity_north(self):
        return self.state.velocity_n if self.available else None

    @property
    def velocity_east(self):
        return self.state.velocity_e if self.available else None

    @property
    def velocity_down(self):
        return self.state.velocity_d if self.available else None

    def fix_string(self):
        return config.GNSS_FIX_NAMES.get(self.fix_type, "Unknown")

    def current_velocity_vector(self):
        import numpy as np
        if not self.available or self.state.velocity_n is None:
            return None
        return np.array([
            self.state.velocity_e,
            self.state.velocity_n,
            -self.state.velocity_d
        ])

    def velocity_magnitude(self):
        import numpy as np
        v = self.current_velocity_vector()
        if v is None:
            return None
        return float(np.linalg.norm(v))

    def is_stationary(self):
        s = self.speed
        if s is None:
            return False
        return s < 0.05

    def heading_vector(self):
        import numpy as np
        h = self.heading
        if h is None:
            return None
        heading_rad = math.radians(h)
        return np.array([
            math.sin(heading_rad),
            math.cos(heading_rad),
            0
        ])

    def accuracy(self):
        return {
            "horizontal": self.horizontal_accuracy,
            "vertical": self.vertical_accuracy
        }

    def as_dict(self):
        return {
            "utc": self.utc,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "speed": self.speed,
            "heading": self.heading,
            "satellites": self.satellites,
            "fix_type": self.fix_type,
            "fix_string": self.fix_string(),
            "horizontal_accuracy": self.horizontal_accuracy,
            "vertical_accuracy": self.vertical_accuracy,
            "hdop": self.hdop,
            "pdop": self.pdop,
            "vdop": self.vdop,
            "carrier_phase": self.carrier_phase,
            "heading_vehicle": self.heading_vehicle,
            "trajectory_points": len(self.trajectory)
        }

    def print_summary(self):
        def _fmt(value, spec=""):
            if value is None:
                return "---"
            try:
                return format(value, spec)
            except (TypeError, ValueError):
                return "---"
        print()
        print("=" * 60)
        print("GNSS STATUS")
        print("=" * 60)
        print(f"UTC           : {self.utc}")
        print(f"Latitude      : {_fmt(self.latitude, '.6f')}")
        print(f"Longitude     : {_fmt(self.longitude, '.6f')}")
        print(f"Altitude      : {_fmt(self.altitude, '.3f')} m")
        print(f"Speed         : {_fmt(self.speed, '.3f')} m/s")
        print(f"Heading       : {_fmt(self.heading, '.2f')} deg")
        print(f"Satellites    : {self.satellites}")
        print(f"Fix           : {self.fix_string()}")
        print(f"H Accuracy    : {_fmt(self.horizontal_accuracy, '.3f')} m")
        print(f"V Accuracy    : {_fmt(self.vertical_accuracy, '.3f')} m")
        print("=" * 60)

    def __repr__(self):
        return (
            f"GNSSParser("
            f"{self.latitude}, "
            f"{self.longitude}, "
            f"{self.altitude})"
        )
