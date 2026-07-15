import math
import struct
import time
from typing import Callable, Dict, Optional

import config
from xsens.decoder import decoder_for
from xsens.decoder.gnss_pvt import is_valid_pvt
from xsens.navigation_state import NavigationState

PREAMBLE = config.PREAMBLE
MID_MTDATA2 = config.MID_MTDATA2

RTK_NONE = config.RTK_NONE
RTK_FLOAT = config.RTK_FLOAT
RTK_FIXED = config.RTK_FIXED


def checksum_ok(frame: bytes) -> bool:
    xor = 0
    for b in frame[1:]:
        xor ^= b
    return xor == 0


def extract_frame(buffer: bytearray):
    while len(buffer) >= 4:
        if buffer[0] != PREAMBLE:
            del buffer[0]
            continue
        mid = buffer[2]
        length = buffer[3]
        if length == 0xFF:
            if len(buffer) < 6:
                return None
            length = struct.unpack(">H", buffer[4:6])[0]
            data_start = 6
        else:
            data_start = 4
        total = data_start + length + 1
        if len(buffer) < total:
            return None
        frame = bytes(buffer[:total])
        del buffer[:total]
        if not checksum_ok(frame):
            continue
        return {"mid": mid, "payload": frame[data_start:data_start + length]}
    return None


class XbusParser:
    def __init__(self):
        self.state = NavigationState()
        self._origin_initialized = False
        self._status_word_seen = False

    def parse_buffer(self, buffer: bytearray) -> Optional[NavigationState]:
        frame = extract_frame(buffer)
        if frame is None:
            return None
        if frame["mid"] != MID_MTDATA2:
            return None
        self._parse_payload(frame["payload"])
        return self.state

    def _parse_payload(self, payload: bytes):
        i = 0
        n = len(payload)
        s = self.state

        while i < n:
            if i + 3 > n:
                break
            data_id = struct.unpack(">H", payload[i:i + 2])[0]
            size_byte = payload[i + 2]
            offset = 3
            size = size_byte
            if size_byte == 0xFF:
                if i + 5 > n:
                    break
                size = struct.unpack(">H", payload[i + 3:i + 5])[0]
                offset = 5
            field_start = i + offset
            field_end = field_start + size
            if field_end > n:
                break
            raw = payload[field_start:field_end]
            i = field_end

            decoder = decoder_for(data_id)
            if decoder is not None:
                value = decoder(data_id, raw)
                if value is None:
                    continue
                self._apply(data_id, value, s)
            else:
                s.fields[data_id] = raw

    _KEEP_ITEMS = {
        config.XDI_QUATERNION, 0x2020,
        config.XDI_ACCELERATION, config.XDI_ACCELERATION_HR,
        config.XDI_RATE_OF_TURN, config.XDI_RATE_OF_TURN_HR,
        config.XDI_MAGNETIC_FIELD,
        config.XDI_GNSS_PVT,
        config.XDI_GNSS_SATELLITES,
        config.XDI_STATUS_WORD,
        config.XDI_PACKET_COUNTER,
        config.XDI_UTC_TIME, 0x1050,
        config.XDI_SAMPLE_TIME_FINE, config.XDI_SAMPLE_TIME_COARSE,
    }

    def _apply(self, data_id: int, value, s: NavigationState):
        base = data_id & config.XDI_BASE_MASK

        if data_id == config.XDI_PACKET_COUNTER:
            s.packet_counter = value

        elif base == 0x2010:
            s.quaternion = value
            if value is not None:
                s.roll, s.pitch, s.yaw = value.to_euler()

        elif data_id == config.XDI_ACCELERATION:
            s.acceleration = value

        elif data_id == config.XDI_RATE_OF_TURN:
            s.gyro = value

        elif data_id == config.XDI_MAGNETIC_FIELD:
            s.magnetic = value

        elif data_id == config.XDI_GNSS_SATELLITES:
            if isinstance(value, int):
                s.num_sv = value

        elif data_id == config.XDI_STATUS_WORD:
            self._apply_status_word(value, s)

        elif data_id == config.XDI_GNSS_PVT:
            self._apply_gnss_pvt(value, s)

    def _apply_status_word(self, value, s: NavigationState):
        raw = int(value)
        bits = getattr(value, "bits", {})
        self._status_word_seen = True

        s.status_word = raw
        s.status_word_hex = getattr(value, "raw_hex", f"0x{raw:08X}")
        s.status_word_binary = getattr(value, "raw_binary", f"{raw:032b}")
        s.status_word_bits = dict(bits)

        s.orientation_valid = bits.get("orientation_valid", bool(raw & (1 << 0)))
        s.gnss_valid = bits.get("gnss_valid", bool(raw & (1 << 1)))
        s.no_gnss_fix = bits.get("no_gnss_fix", bool(raw & (1 << 2)))
        s.filter_valid = bits.get("filter_valid", bool(raw & (1 << 4)))
        s.clock_sync = bits.get("clock_sync", bool(raw & (1 << 10)))
        s.pps = bits.get("pps", bool(raw & (1 << 14)))
        s.sync_in = bits.get("sync_in", bool(raw & (1 << 18)))
        s.sync_out = bits.get("sync_out", bool(raw & (1 << 19)))
        s.differential = bits.get("differential", bool(raw & (1 << 23)))
        s.external_gnss = bits.get("external_gnss", bool(raw & (1 << 24)))
        s.representative_motion = bits.get(
            "representative_motion", bool(raw & (1 << 25))
        )
        s.clipping = bits.get("clipping", bool(raw & (1 << 26)))

        rtk_bits = getattr(value, "rtk_phase", (raw >> config.STATUS_BIT_RTK_SHIFT) & config.STATUS_BIT_RTK_MASK)
        new_rtk = RTK_FIXED if rtk_bits == 2 else (RTK_FLOAT if rtk_bits == 1 else RTK_NONE)
        s.rtk_state = new_rtk
        s.carrier_state = s.rtk_state

        self._update_gnss_state(s)

    def _apply_gnss_pvt(self, pvt, s: NavigationState):
        s.gnss_receiver_seen = True

        if not is_valid_pvt(pvt):
            s.fix_type = pvt.fix_type if pvt.fix_type is not None else 0
            s.flags = getattr(pvt, "flags", None)
            s.num_sv = pvt.num_sv if pvt.num_sv is not None else 0
            s.latitude = None
            s.longitude = None
            s.gnss_valid = False
            self._update_gnss_state(s)
            return

        s.itow = pvt.itow
        s.year = pvt.year
        s.month = pvt.month
        s.day = pvt.day
        s.hour = pvt.hour
        s.minute = pvt.minute
        s.second = pvt.second
        s.valid_flags = pvt.valid_flags
        s.nano = pvt.nano
        s.t_acc = pvt.time_accuracy
        s.fix_type = pvt.fix_type
        s.no_gnss_fix = pvt.fix_type is not None and pvt.fix_type < config.GNSS_FIX_2D
        s.flags = pvt.flags
        s.flags2 = getattr(pvt, "flags2", None)
        if pvt.num_sv is not None and pvt.num_sv > 0:
            s.num_sv = pvt.num_sv
        elif s.num_sv is None or s.num_sv == 0:
            sv_from_fields = s.fields.get(config.XDI_GNSS_SATELLITES)
            if isinstance(sv_from_fields, int) and sv_from_fields > 0:
                s.num_sv = sv_from_fields

        has_3d_fix = pvt.fix_type is not None and pvt.fix_type >= config.GNSS_FIX_3D
        pos_valid = pvt.valid_flags is not None and bool(pvt.valid_flags & 0x01)

        if has_3d_fix:
            s.latitude = pvt.latitude
            s.longitude = pvt.longitude
            s.altitude = pvt.altitude
            s.height_msl = pvt.altitude_msl
            s.gnss_valid = True
        else:
            s.latitude = None
            s.longitude = None
            s.altitude = None
            s.height_msl = None
        s.horizontal_accuracy = pvt.horizontal_accuracy
        s.vertical_accuracy = pvt.vertical_accuracy
        raw_speed = pvt.ground_speed if pvt.ground_speed is not None else 0.0
        parked = raw_speed < 0.05
        s.ground_speed = 0.0 if parked else raw_speed
        s.velocity_n = 0.0 if parked else pvt.velocity_north
        s.velocity_e = 0.0 if parked else pvt.velocity_east
        s.velocity_d = 0.0 if parked else pvt.velocity_down
        s.heading_motion = pvt.heading
        s.heading_vehicle = pvt.heading_vehicle
        s.speed_accuracy = pvt.speed_accuracy
        s.heading_accuracy = pvt.heading_accuracy
        s.gdop = pvt.gdop
        s.pdop = pvt.pdop
        s.tdop = pvt.tdop
        s.vdop = pvt.vdop
        s.hdop = pvt.hdop
        s.ndop = pvt.ndop
        s.edop = pvt.edop

        diff_from_pvt = bool(pvt.flags & config.FLAG_DIFFERENTIAL) if pvt.flags is not None else False
        if not s.differential:
            s.differential = diff_from_pvt and has_3d_fix

        if pvt.flags is not None:
            carr = (pvt.flags >> 6) & 0x03
            if carr == 2:
                s.rtk_state = RTK_FIXED
                s.carrier_state = RTK_FIXED
            elif carr == 1:
                s.rtk_state = RTK_FLOAT
                s.carrier_state = RTK_FLOAT

        if pvt.utc:
            s.utc = pvt.utc
        elif all(v is not None for v in (pvt.year, pvt.month, pvt.day,
                                         pvt.hour, pvt.minute, pvt.second)):
            s.utc = f"{pvt.year:04d}-{pvt.month:02d}-{pvt.day:02d} " \
                    f"{pvt.hour:02d}:{pvt.minute:02d}:{pvt.second:02d}"

        if s.yaw is None:
            self._apply_yaw_drift_compensation(s)

        if self._origin_initialized and s.latitude is not None:
            self._update_local_position(s)

        self._update_gnss_state(s)
        self._update_nav_quality(s)

    def _apply_yaw_drift_compensation(self, s: NavigationState):
        speed = s.ground_speed if s.ground_speed is not None else 0.0
        hdg_acc = s.heading_accuracy if s.heading_accuracy is not None else 999.0
        gnss_heading_valid = bool(s.flags & config.FLAG_HEADING_VALID) if s.flags is not None else False
        moving = speed >= 1.0
        heading_valid = gnss_heading_valid and hdg_acc <= 10.0

        if not hasattr(self, "_last_good_yaw"):
            self._last_good_yaw = None
            self._last_good_time = 0

        if moving and heading_valid and s.heading_motion is not None:
            self._last_good_yaw = s.heading_motion
            self._last_good_time = time.time()

        if s.yaw is None and self._last_good_yaw is not None:
            s.yaw = self._last_good_yaw

    def _update_nav_quality(self, s: NavigationState):
        fix = s.fix_type if s.fix_type is not None else 0
        rtk = s.rtk_state
        diff = s.differential

        if rtk == config.RTK_FIXED:
            s.nav_quality = config.NAVQ_BEST
        elif rtk == config.RTK_FLOAT:
            s.nav_quality = config.NAVQ_GOOD
        elif diff:
            s.nav_quality = config.NAVQ_GOOD
        elif fix >= config.GNSS_FIX_3D:
            s.nav_quality = config.NAVQ_OK
        elif s.gnss_receiver_seen:
            s.nav_quality = config.NAVQ_BAD
        else:
            s.nav_quality = config.NAVQ_NONE

    def _update_gnss_state(self, s: NavigationState):
        if not s.gnss_receiver_seen:
            s.gnss_state = "No Receiver"
        elif s.fix_type is None:
            s.gnss_state = "Receiver Running"
        elif s.fix_type < config.GNSS_FIX_2D:
            s.gnss_state = "No Fix"
        elif s.rtk_state == RTK_FIXED:
            s.gnss_state = "RTK Fixed"
        elif s.rtk_state == RTK_FLOAT:
            s.gnss_state = "RTK Float"
        elif s.differential:
            s.gnss_state = "Differential"
        elif s.fix_type == config.GNSS_FIX_3D:
            s.gnss_state = "3D"
        elif s.fix_type == config.GNSS_FIX_2D:
            s.gnss_state = "2D"
        else:
            s.gnss_state = "No Fix"

    def _update_local_position(self, s: NavigationState):
        lat = math.radians(s.latitude)
        lon = math.radians(s.longitude)
        lat0 = math.radians(self.origin_lat)
        lon0 = math.radians(self.origin_lon)
        R = 6378137.0
        east = (lon - lon0) * math.cos(lat0) * R
        north = (lat - lat0) * R
        up = (s.altitude if s.altitude is not None else 0.0) - self.origin_alt
        s.fields["local_east"] = east
        s.fields["local_north"] = north
        s.fields["local_up"] = up

    def get_state(self) -> NavigationState:
        return self.state

    def reset(self):
        self.state = NavigationState()
        self._origin_initialized = False
        self._status_word_seen = False

    def has_orientation(self):
        return self.state.quaternion is not None

    def has_gnss(self):
        return self.state.is_valid()

    def has_quaternion(self):
        return self.state.quaternion is not None

    def has_rtk(self):
        return self.state.rtk_state in (RTK_FLOAT, RTK_FIXED)

    def is_rtk_fixed(self):
        return self.state.rtk_state == RTK_FIXED

    def is_rtk_float(self):
        return self.state.rtk_state == RTK_FLOAT

    def get_rtk_string(self):
        return config.RTK_NAMES.get(self.state.rtk_state, "No RTK")

    def get_orientation(self):
        return (self.state.roll, self.state.pitch, self.state.yaw)

    def get_quaternion(self):
        return self.state.quaternion

    def get_position(self):
        return (self.state.latitude, self.state.longitude, self.state.altitude)

    def get_velocity(self):
        s = self.state
        if s.velocity_n is None:
            return None
        return (s.velocity_n, s.velocity_e, s.velocity_d)

    def get_acceleration(self):
        return self.state.acceleration

    def get_free_acceleration(self):
        return self.state.free_acceleration

    def get_gyro(self):
        return self.state.gyro

    def get_pressure(self):
        return self.state.pressure

    def get_temperature(self):
        return self.state.temperature

    def get_packet_counter(self):
        return self.state.packet_counter

    def get_sample_time(self):
        return self.state.sample_time

    def get_ground_speed(self):
        return self.state.ground_speed

    def get_fix_type(self):
        return self.state.fix_type

    def get_satellites(self):
        return self.state.num_sv

    def get_navigation_dictionary(self):
        return {
            "packet_counter": self.state.packet_counter,
            "sample_time": self.state.sample_time,
            "utc": self.state.utc,
            "roll": self.state.roll,
            "pitch": self.state.pitch,
            "yaw": self.state.yaw,
            "quaternion": self.state.quaternion,
            "acceleration": self.state.acceleration,
            "free_acceleration": self.state.free_acceleration,
            "gyro": self.state.gyro,
            "gyro_hr": self.state.gyro_hr,
            "magnetic": self.state.magnetic,
            "pressure": self.state.pressure,
            "temperature": self.state.temperature,
            "latitude": self.state.latitude,
            "longitude": self.state.longitude,
            "altitude": self.state.altitude,
            "speed": self.state.ground_speed,
            "heading": self.state.heading_motion,
            "horizontal_accuracy": self.state.horizontal_accuracy,
            "vertical_accuracy": self.state.vertical_accuracy,
            "satellites": self.state.num_sv,
            "fix_type": self.state.fix_type,
            "pdop": self.state.pdop,
            "hdop": self.state.hdop,
            "vdop": self.state.vdop,
            "filter_valid": self.state.filter_valid,
            "gnss_valid": self.state.gnss_valid,
            "rtk_status": self.get_rtk_string(),
            "carrier_phase": self.state.carrier_state,
            "nav_quality": self.state.nav_quality,
            "nav_quality_name": config.NAVQ_NAMES.get(self.state.nav_quality, "---"),
        }

    def reset_origin_and_trajectory(self):
        self._origin_initialized = False
        self.clear_trajectory()

    def initialize_local_origin(self):
        s = self.state
        if not s.is_valid() or not s.gnss_valid:
            return False
        if self._origin_initialized:
            return True
        self.origin_lat = s.latitude
        self.origin_lon = s.longitude
        self.origin_alt = s.altitude if s.altitude is not None else 0.0
        self._origin_initialized = True
        return True

    def geodetic_to_local(self):
        s = self.state
        if s.latitude is None or s.longitude is None:
            return None
        if not self.initialize_local_origin():
            return None
        lat = math.radians(s.latitude)
        lon = math.radians(s.longitude)
        lat0 = math.radians(self.origin_lat)
        lon0 = math.radians(self.origin_lon)
        R = 6378137.0
        east = (lon - lon0) * math.cos(lat0) * R
        north = (lat - lat0) * R
        up = (s.altitude if s.altitude is not None else 0.0) - self.origin_alt
        return (east, north, up)

    def get_local_position(self):
        return self.geodetic_to_local()

    def get_vehicle_pose(self):
        q = self.state.quaternion
        T = q.to_homogeneous_matrix() if q else None
        position = self.get_local_position()
        if T is not None and position is not None:
            T[0, 3] = position[0]
            T[1, 3] = position[1]
            T[2, 3] = position[2]
        return {
            "position": position,
            "orientation": self.get_orientation(),
            "quaternion": self.get_quaternion(),
            "transform": T,
        }

    def update_history(self):
        if not hasattr(self, "trajectory"):
            self.trajectory = []
        s = self.state
        if s.latitude is None or s.longitude is None:
            return
        if s.fix_type is None or s.fix_type < config.GNSS_FIX_3D:
            return
        if s.ground_speed is not None and s.ground_speed < 0.05:
            return
        hacc = s.horizontal_accuracy if s.horizontal_accuracy is not None else 999.0
        if hacc >= 2.0:
            return
        if not s.differential:
            return
        if not self._origin_initialized:
            self.initialize_local_origin()
        position = self.get_local_position()
        if position is None:
            return
        self.trajectory.append(position)
        if len(self.trajectory) > config.MAX_TRAJECTORY_POINTS:
            self.trajectory.pop(0)

    def get_trajectory(self):
        if not hasattr(self, "trajectory"):
            self.trajectory = []
        return self.trajectory

    def clear_trajectory(self):
        self.trajectory = []

    def close(self):
        pass

    def __repr__(self):
        return (
            f"<XbusParser "
            f"Packet={self.state.packet_counter} "
            f"RTK={self.get_rtk_string()} "
            f"Sat={self.state.num_sv}>"
        )

    def __str__(self):
        return self.__repr__()
