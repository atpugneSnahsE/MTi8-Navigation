import time

import config


class GPSStatus:

    FIX_TYPES = config.GNSS_FIX_NAMES
    RTK_TYPES = config.RTK_NAMES

    def __init__(self):

        self.state = None

        self.start_time = time.time()

        self.last_update = None

    def update(self, navigation_state):

        self.state = navigation_state

        self.last_update = time.time()

    @property
    def valid(self):

        if self.state is None:
            return False

        return self.state.gnss_valid

    @property
    def filter_valid(self):

        if self.state is None:
            return False

        return self.state.filter_valid

    @property
    def satellites(self):

        if self.state is None:
            return 0

        return self.state.num_sv

    @property
    def latitude(self):

        if self.state is None:
            return None

        return self.state.latitude

    @property
    def longitude(self):

        if self.state is None:
            return None

        return self.state.longitude

    @property
    def altitude(self):

        if self.state is None:
            return None

        return self.state.altitude

    @property
    def speed(self):

        if self.state is None:
            return None

        return self.state.ground_speed

    @property
    def heading(self):

        if self.state is None:
            return None

        return self.state.heading_motion

    @property
    def hdop(self):

        if self.state is None:
            return None

        return self.state.hdop

    @property
    def vdop(self):

        if self.state is None:
            return None

        return self.state.vdop

    @property
    def pdop(self):

        if self.state is None:
            return None

        return self.state.pdop

    @property
    def utc(self):

        if self.state is None:
            return None

        return self.state.utc

    @property
    def fix_type(self):

        if self.state is None:
            return 0

        return self.state.fix_type

    @property
    def rtk_status(self):

        if self.state is None:
            return 0

        return self.state.rtk_state

    @property
    def nav_quality(self):

        if self.state is None:
            return 0

        return self.state.nav_quality

    def fix_string(self):

        return self.FIX_TYPES.get(
            self.fix_type,
            "Unknown"
        )

    def rtk_string(self):

        return self.RTK_TYPES.get(
            self.rtk_status,
            "Unknown"
        )

    def is_rtk_fixed(self):

        return self.rtk_status == 2

    def is_rtk_float(self):

        return self.rtk_status == 1

    def has_fix(self):

        return self.fix_type >= 2

    def health_score(self):

        score = 0

        if self.valid:
            score += 20

        if self.filter_valid:
            score += 20

        if self.has_fix():
            score += 20

        if self.satellites is not None:

            score += min(
                self.satellites,
                20
            )

        if self.is_rtk_float():
            score += 10

        if self.is_rtk_fixed():
            score += 20

        if self.state is not None and self.state.horizontal_accuracy is not None:
            hacc = self.state.horizontal_accuracy
            if hacc < config.NAVQ_HACC_BEST:
                score += 20
            elif hacc < config.NAVQ_HACC_GOOD:
                score += 10
            elif hacc >= config.NAVQ_HACC_BAD:
                score -= 10

        return max(0, min(score, 100))

    def uptime(self):

        return time.time() - self.start_time

    def as_dict(self):

        return {
            "utc": self.utc,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "speed": self.speed,
            "heading": self.heading,
            "satellites": self.satellites,
            "fix": self.fix_string(),
            "rtk": self.rtk_string(),
            "horizontal_accuracy": self.state.horizontal_accuracy if self.state else None,
            "vertical_accuracy": self.state.vertical_accuracy if self.state else None,
            "hdop": self.hdop,
            "pdop": self.pdop,
            "vdop": self.vdop,
            "gnss_valid": self.valid,
            "filter_valid": self.filter_valid,
            "nav_quality": self.nav_quality,
            "nav_quality_name": config.NAVQ_NAMES.get(self.nav_quality, "---"),
            "health": self.health_score(),
            "uptime": self.uptime()
        }

    def print_status(self):

        print()
        print("=" * 70)
        print("GPS / RTK STATUS")
        print("=" * 70)
        print(f"UTC                 : {self.utc}")
        print(f"Latitude            : {self.latitude}")
        print(f"Longitude           : {self.longitude}")
        print(f"Altitude            : {self.altitude}")
        print(f"Speed               : {self.speed}")
        print(f"Heading             : {self.heading}")
        print(f"Satellites          : {self.satellites}")
        print(f"GNSS Fix            : {self.fix_string()}")
        print(f"RTK Status          : {self.rtk_string()}")
        print(f"Horizontal Accuracy : {self.hdop}")
        print(f"Vertical Accuracy   : {self.vdop}")
        print(f"GNSS Valid          : {self.valid}")
        print(f"Filter Valid        : {self.filter_valid}")
        print(f"Health Score        : {self.health_score()}/100")
        print("=" * 70)

    def __repr__(self):

        return (
            f"GPSStatus("
            f"{self.fix_string()}, "
            f"{self.rtk_string()}, "
            f"Sat={self.satellites})"
        )


if __name__ == "__main__":

    print()
    print("GPSStatus module loaded successfully.")
