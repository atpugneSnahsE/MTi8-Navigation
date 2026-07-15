"""
GNSS PVT Decoder (0x7010)

Decodes UBX NAV-PVT payload (92-94 bytes) and FP32 float payload (52 bytes)
from the MTi-8 GNSS PVT data output.

XDI 0x7010 format detected automatically by payload length.
"""

import struct
from dataclasses import dataclass
from typing import Optional
from xsens.decoder._helpers import f32, f64


def i32be(data, offset=0):
    return struct.unpack_from(">i", data, offset)[0]


def u32be(data, offset=0):
    return struct.unpack_from(">I", data, offset)[0]


def u16be(data, offset=0):
    return struct.unpack_from(">H", data, offset)[0]


def u8(data, offset=0):
    return data[offset]


@dataclass
class GNSSPVT:
    itow: Optional[int] = None
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    second: Optional[int] = None
    valid_flags: Optional[int] = None
    time_accuracy: Optional[int] = None
    t_acc: Optional[int] = None
    nano: Optional[int] = None
    fix_type: Optional[int] = None
    flags: Optional[int] = None
    num_sv: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    altitude_msl: Optional[float] = None
    horizontal_accuracy: Optional[float] = None
    vertical_accuracy: Optional[float] = None
    velocity_north: Optional[float] = None
    velocity_east: Optional[float] = None
    velocity_down: Optional[float] = None
    ground_speed: Optional[float] = None
    heading: Optional[float] = None
    heading_vehicle: Optional[float] = None
    speed_accuracy: Optional[float] = None
    heading_accuracy: Optional[float] = None
    gdop: Optional[float] = None
    pdop: Optional[float] = None
    tdop: Optional[float] = None
    vdop: Optional[float] = None
    hdop: Optional[float] = None
    ndop: Optional[float] = None
    edop: Optional[float] = None
    utc: Optional[str] = None


def is_valid_pvt(pvt):
    if pvt is None:
        return False
    if pvt.latitude is not None and pvt.longitude is not None:
        if abs(pvt.latitude) < 1e-8 and abs(pvt.longitude) < 1e-8:
            return False
        if not (-90 <= pvt.latitude <= 90) or not (-180 <= pvt.longitude <= 180):
            return False
    if pvt.horizontal_accuracy is not None and pvt.horizontal_accuracy > 500:
        return False
    if pvt.fix_type is not None and pvt.fix_type == 0:
        return False
    if pvt.fix_type is not None and pvt.fix_type == 5:
        return False
    return True


def decode_gnss_pvt(data_id, field):
    if len(field) >= 84:
        return _parse_ubx(field)
    if len(field) >= 52:
        return _parse_fp4(field)
    return None


def _parse_ubx(field):
    pvt = GNSSPVT()
    pvt.itow = u32be(field, 0)

    pvt.year = u16be(field, 4)
    pvt.month = u8(field, 6)
    pvt.day = u8(field, 7)
    pvt.hour = u8(field, 8)
    pvt.minute = u8(field, 9)
    pvt.second = u8(field, 10)

    pvt.valid_flags = u8(field, 11)
    pvt.time_accuracy = u32be(field, 12)
    pvt.t_acc = pvt.time_accuracy
    pvt.nano = i32be(field, 16)

    pvt.fix_type = u8(field, 20)
    pvt.flags = u8(field, 21)
    pvt.num_sv = u8(field, 22)

    pvt.longitude = i32be(field, 24) / 1e7
    pvt.latitude = i32be(field, 28) / 1e7
    pvt.altitude = i32be(field, 32) / 1000.0
    pvt.altitude_msl = i32be(field, 36) / 1000.0

    pvt.horizontal_accuracy = u32be(field, 40) / 1000.0
    pvt.vertical_accuracy = u32be(field, 44) / 1000.0

    pvt.velocity_north = i32be(field, 48) / 1000.0
    pvt.velocity_east = i32be(field, 52) / 1000.0
    pvt.velocity_down = i32be(field, 56) / 1000.0
    pvt.ground_speed = i32be(field, 60) / 1000.0
    pvt.heading = i32be(field, 64) / 1e5

    pvt.speed_accuracy = u32be(field, 68) / 1000.0
    pvt.heading_accuracy = u32be(field, 72) / 1e5

    if len(field) >= 80:
        pvt.heading_vehicle = i32be(field, 76) / 1e5
    if len(field) >= 82:
        pvt.gdop = u16be(field, 80) / 100.0
    if len(field) >= 84:
        pvt.pdop = u16be(field, 82) / 100.0
    if len(field) >= 86:
        pvt.tdop = u16be(field, 84) / 100.0
    if len(field) >= 88:
        pvt.vdop = u16be(field, 86) / 100.0
    if len(field) >= 90:
        pvt.hdop = u16be(field, 88) / 100.0
    if len(field) >= 92:
        pvt.ndop = u16be(field, 90) / 100.0
    if len(field) >= 94:
        pvt.edop = u16be(field, 92) / 100.0

    if pvt.valid_flags is not None:
        parts = []
        if pvt.valid_flags & 0x01:
            parts.append("DateValid")
        if pvt.valid_flags & 0x02:
            parts.append("TimeValid")
        if pvt.valid_flags & 0x04:
            parts.append("FullyResolved")
        y, mo, d, h, mi, s = (pvt.year, pvt.month, pvt.day,
                               pvt.hour, pvt.minute, pvt.second)
        if all(v is not None for v in (y, mo, d, h, mi, s)):
            pvt.utc = f"{y:04d}-{mo:02d}-{d:02d} {h:02d}:{mi:02d}:{s:02d}"

    return pvt


def _parse_fp4(field):
    pvt = GNSSPVT()
    pvt.latitude = f32(field, 0)
    pvt.longitude = f32(field, 4)
    pvt.altitude = f32(field, 8)
    pvt.altitude_msl = f32(field, 12)
    pvt.horizontal_accuracy = f32(field, 16)
    pvt.vertical_accuracy = f32(field, 20)
    pvt.velocity_north = f32(field, 24)
    pvt.velocity_east = f32(field, 28)
    pvt.velocity_down = f32(field, 32)
    pvt.ground_speed = f32(field, 36)
    pvt.heading = f32(field, 40)
    pvt.speed_accuracy = f32(field, 44)
    pvt.heading_accuracy = f32(field, 48)
    pvt.fix_type = 3
    pvt.num_sv = 0
    return pvt
