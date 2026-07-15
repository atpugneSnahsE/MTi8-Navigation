from dataclasses import dataclass, field
from typing import Optional, Tuple
from xsens.quaternion import Quaternion


@dataclass
class NavigationState:
    packet_counter: Optional[int] = None
    sample_time: Optional[int] = None
    sample_time_coarse: Optional[int] = None

    utc: Optional[str] = None
    timestamp: Optional[float] = None

    itow: Optional[int] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    second: Optional[int] = None
    nano: Optional[int] = None
    t_acc: Optional[int] = None
    valid_flags: Optional[int] = None

    quaternion: Optional[Quaternion] = None
    roll: Optional[float] = None
    pitch: Optional[float] = None
    yaw: Optional[float] = None

    acceleration: Optional[Tuple[float, float, float]] = None
    free_acceleration: Optional[Tuple[float, float, float]] = None
    acceleration_hr: Optional[Tuple[float, float, float]] = None
    gyro: Optional[Tuple[float, float, float]] = None
    gyro_hr: Optional[Tuple[float, float, float]] = None
    delta_v: Optional[Tuple[float, float, float]] = None
    delta_q: Optional[Tuple[float, float, float, float]] = None
    magnetometer: Optional[Tuple[float, float, float]] = None
    magnetic: Optional[Tuple[float, float, float]] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None

    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    height_msl: Optional[float] = None

    velocity_n: Optional[float] = None
    velocity_e: Optional[float] = None
    velocity_d: Optional[float] = None
    ground_speed: Optional[float] = None
    heading_motion: Optional[float] = None
    heading_vehicle: Optional[float] = None

    horizontal_accuracy: Optional[float] = None
    vertical_accuracy: Optional[float] = None
    speed_accuracy: Optional[float] = None
    heading_accuracy: Optional[float] = None

    gdop: Optional[float] = None
    pdop: Optional[float] = None
    tdop: Optional[float] = None
    vdop: Optional[float] = None
    hdop: Optional[float] = None
    ndop: Optional[float] = None
    edop: Optional[float] = None

    fix_type: Optional[int] = None
    num_sv: Optional[int] = None
    flags: Optional[int] = None
    flags2: Optional[int] = None
    gnss_receiver_seen: bool = False
    gnss_state: str = "No Receiver"

    status_word: Optional[int] = None
    status_word_hex: Optional[str] = None
    status_word_binary: Optional[str] = None
    status_word_bits: dict = field(default_factory=dict)
    status_byte: Optional[int] = None

    rtk_state: int = 0
    carrier_state: int = 0
    clock_sync: bool = False
    differential: bool = False
    external_gnss: bool = False
    filter_valid: bool = False
    gnss_valid: bool = False
    no_gnss_fix: bool = False
    orientation_valid: bool = False
    pps: bool = False
    representative_motion: bool = False
    clipping: bool = False
    sync_in: bool = False
    sync_out: bool = False

    nav_quality: int = 0

    fields: dict = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Backward-compatible accessors
    # ------------------------------------------------------------------

    @property
    def orientation(self):
        class OrientationCompat:
            def __init__(self, s):
                self._s = s
            @property
            def quaternion(self):
                return self._s.quaternion
            @property
            def roll(self):
                return self._s.roll
            @property
            def pitch(self):
                return self._s.pitch
            @property
            def yaw(self):
                return self._s.yaw
            def as_euler(self):
                return (self._s.roll, self._s.pitch, self._s.yaw)
            def to_rotation_matrix(self):
                if self._s.quaternion is None:
                    import numpy as np
                    return np.eye(3)
                return self._s.quaternion.to_rotation_matrix()
            def to_homogeneous_matrix(self):
                if self._s.quaternion is None:
                    import numpy as np
                    return np.eye(4)
                return self._s.quaternion.to_homogeneous_matrix()
            def update_from_quaternion(self, q):
                self._s.quaternion = q
                if q is not None:
                    self._s.roll, self._s.pitch, self._s.yaw = q.to_euler()
        return OrientationCompat(self)

    @property
    def position(self):
        class PositionCompat:
            def __init__(self, s):
                self._s = s
            @property
            def latitude(self):
                return self._s.latitude
            @property
            def longitude(self):
                return self._s.longitude
            @property
            def altitude(self):
                return self._s.altitude
            @property
            def altitude_msl(self):
                return self._s.height_msl
            def is_valid(self):
                lat, lon = self._s.latitude, self._s.longitude
                if lat is None or lon is None:
                    return False
                return -90 <= lat <= 90 and -180 <= lon <= 180
            def as_lla(self):
                return (self._s.latitude, self._s.longitude, self._s.altitude)
        return PositionCompat(self)

    @property
    def velocity(self):
        class VelocityCompat:
            def __init__(self, s):
                self._s = s
            @property
            def north(self):
                return self._s.velocity_n
            @property
            def east(self):
                return self._s.velocity_e
            @property
            def down(self):
                return self._s.velocity_d
            @property
            def ground_speed(self):
                return self._s.ground_speed
            @property
            def heading(self):
                return self._s.heading_motion
        return VelocityCompat(self)

    @property
    def imu(self):
        class IMUCompat:
            def __init__(self, s):
                self._s = s
            @property
            def acceleration(self):
                return self._s.acceleration
            @property
            def free_acceleration(self):
                return self._s.free_acceleration
            @property
            def acceleration_hr(self):
                return self._s.acceleration_hr
            @property
            def gyro(self):
                return self._s.gyro
            @property
            def gyro_hr(self):
                return self._s.gyro_hr
            @property
            def delta_v(self):
                return self._s.delta_v
            @property
            def delta_q(self):
                return self._s.delta_q
            @property
            def magnetic(self):
                return self._s.magnetic
            @property
            def pressure(self):
                return self._s.pressure
            @property
            def temperature(self):
                return self._s.temperature
        return IMUCompat(self)

    @property
    def gnss(self):
        class GNSSCompat:
            def __init__(self, s):
                self._s = s
            @property
            def fix_type(self):
                return self._s.fix_type
            @property
            def satellites(self):
                return self._s.num_sv
            @property
            def carrier_phase(self):
                return (self._s.flags >> 1) & 0x01 if self._s.flags is not None else None
            @property
            def horizontal_accuracy(self):
                return self._s.horizontal_accuracy
            @property
            def vertical_accuracy(self):
                return self._s.vertical_accuracy
            @property
            def speed_accuracy(self):
                return self._s.speed_accuracy
            @property
            def heading_accuracy(self):
                return self._s.heading_accuracy
            @property
            def heading_vehicle(self):
                return self._s.heading_vehicle
            @property
            def hdop(self):
                return self._s.hdop
            @property
            def vdop(self):
                return self._s.vdop
            @property
            def pdop(self):
                return self._s.pdop
            @property
            def gdop(self):
                return self._s.gdop
            @property
            def utc(self):
                return self._s.utc
            @property
            def itow(self):
                return self._s.itow
            @property
            def nano(self):
                return self._s.nano
            @property
            def valid_flags(self):
                return self._s.valid_flags
            @property
            def flags(self):
                return self._s.flags
            @property
            def flags2(self):
                return self._s.flags2
            @property
            def time_accuracy(self):
                return self._s.t_acc
            @property
            def year(self):
                return self._s.year
            @property
            def month(self):
                return self._s.month
            @property
            def day(self):
                return self._s.day
            @property
            def hour(self):
                return self._s.hour
            @property
            def minute(self):
                return self._s.minute
            @property
            def second(self):
                return self._s.second
            @property
            def flags2(self):
                return None
            @property
            def magnetic_declination(self):
                return None
            @property
            def magnetic_accuracy(self):
                return None
        return GNSSCompat(self)

    @property
    def gnss_raw(self):
        class GNSSRawCompat:
            def __init__(self, s):
                self._s = s
            @property
            def itow(self):
                return self._s.itow
            @property
            def year(self):
                return self._s.year
            @property
            def month(self):
                return self._s.month
            @property
            def day(self):
                return self._s.day
            @property
            def hour(self):
                return self._s.hour
            @property
            def minute(self):
                return self._s.minute
            @property
            def second(self):
                return self._s.second
            @property
            def valid_flags(self):
                return self._s.valid_flags
            @property
            def nano(self):
                return self._s.nano
            @property
            def time_accuracy(self):
                return self._s.t_acc
            @property
            def fix_type(self):
                return self._s.fix_type
            @property
            def flags(self):
                return self._s.flags
            @property
            def num_sv(self):
                return self._s.num_sv
            @property
            def latitude(self):
                return self._s.latitude
            @property
            def longitude(self):
                return self._s.longitude
            @property
            def altitude(self):
                return self._s.altitude
            @property
            def altitude_msl(self):
                return self._s.height_msl
            @property
            def horizontal_accuracy(self):
                return self._s.horizontal_accuracy
            @property
            def vertical_accuracy(self):
                return self._s.vertical_accuracy
            @property
            def velocity_north(self):
                return self._s.velocity_n
            @property
            def velocity_east(self):
                return self._s.velocity_e
            @property
            def velocity_down(self):
                return self._s.velocity_d
            @property
            def ground_speed(self):
                return self._s.ground_speed
            @property
            def heading(self):
                return self._s.heading_motion
            @property
            def heading_vehicle(self):
                return self._s.heading_vehicle
            @property
            def speed_accuracy(self):
                return self._s.speed_accuracy
            @property
            def heading_accuracy(self):
                return self._s.heading_accuracy
            @property
            def gdop(self):
                return self._s.gdop
            @property
            def pdop(self):
                return self._s.pdop
            @property
            def tdop(self):
                return self._s.tdop
            @property
            def vdop(self):
                return self._s.vdop
            @property
            def hdop(self):
                return self._s.hdop
            @property
            def ndop(self):
                return self._s.ndop
            @property
            def edop(self):
                return self._s.edop
            @property
            def utc(self):
                return self._s.utc
        return GNSSRawCompat(self)

    @property
    def rtk(self):
        import config
        class RTKCompat:
            def __init__(self, s):
                self._s = s
            @property
            def status(self):
                return self._s.rtk_state
            def is_fixed(self):
                return self._s.rtk_state == config.RTK_FIXED
            def is_float(self):
                return self._s.rtk_state == config.RTK_FLOAT
            def display_string(self):
                return config.RTK_NAMES.get(self._s.rtk_state, "No RTK")
        return RTKCompat(self)

    @property
    def status(self):
        class StatusCompat:
            def __init__(self, s):
                self._s = s
            @property
            def status_word(self):
                return self._s.status_word
            @property
            def status_word_hex(self):
                return self._s.status_word_hex
            @property
            def status_word_binary(self):
                return self._s.status_word_binary
            @property
            def status_byte(self):
                return self._s.status_byte
            @property
            def filter_valid(self):
                return self._s.filter_valid
            @property
            def gnss_valid(self):
                return self._s.gnss_valid
        return StatusCompat(self)

    def is_valid(self):
        if self.latitude is None or self.longitude is None:
            return False
        return -90 <= self.latitude <= 90 and -180 <= self.longitude <= 180

    def as_lla(self):
        return (self.latitude, self.longitude, self.altitude)
