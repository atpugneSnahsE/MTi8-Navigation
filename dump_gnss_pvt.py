#!/usr/bin/env python3

import struct
from datetime import datetime

import serial

PORT = "/dev/ttyUSB0"
BAUD = 2000000

PREAMBLE = 0xFA
BID = 0xFF
MID_MTDATA2 = 0x36

XDI_GNSS_PVT = 0x7010
XDI_STATUS_WORD = 0xE020

FIX_NAMES = {
    0: "No Fix",
    1: "Dead Reckoning",
    2: "2D",
    3: "3D",
    4: "GNSS+DR",
    5: "Time Only",
}


def checksum(msg):
    s = sum(msg) & 0xFF
    return ((256 - s) & 0xFF)


def read_packet(ser):
    while True:
        if ser.read(1) != bytes([PREAMBLE]):
            continue
        if ser.read(1) != bytes([BID]):
            continue
        mid = ser.read(1)[0]
        if mid != MID_MTDATA2:
            continue
        length = ser.read(1)[0]
        if length == 0xFF:
            length = int.from_bytes(ser.read(2), "big")
        payload = ser.read(length)
        ser.read(1)
        return payload


def decode_status_word(data):
    if len(data) < 4:
        return
    sw = struct.unpack(">I", data)[0]

    orientation_valid = bool(sw & (1 << 0))
    gnss_valid = bool(sw & (1 << 1))
    no_gnss_fix = bool(sw & (1 << 2))
    filter_valid = bool(sw & (1 << 4))
    clock_sync = bool(sw & (1 << 10))
    pps = bool(sw & (1 << 14))
    differential = bool(sw & (1 << 23))
    rtk_bits = (sw >> 27) & 0x03
    rtk_text = ["None", "Float", "Fixed"][rtk_bits] if rtk_bits < 3 else "?"

    print(f"  Status Word     : 0x{sw:08X}  {sw:032b}")
    print(f"  Orientation     : {orientation_valid}")
    print(f"  GNSS Valid      : {gnss_valid}")
    print(f"  GNSS Fix        : {not no_gnss_fix}")
    print(f"  Filter Valid    : {filter_valid}")
    print(f"  Clock Sync      : {clock_sync}")
    print(f"  PPS             : {pps}")
    print(f"  Differential    : {differential}")
    print(f"  RTK             : {rtk_text} (bits {rtk_bits})")


def decode_gnss_pvt(data):
    if len(data) != 94:
        print(f"  Unexpected GNSS PVT length: {len(data)} bytes (expected 94)")
        print(f"  Raw: {data.hex()}")
        return

    itow = struct.unpack_from(">I", data, 0)[0]
    year = struct.unpack_from(">H", data, 4)[0]
    month = data[6]
    day = data[7]
    hour = data[8]
    minute = data[9]
    second = data[10]
    valid = data[11]
    tAcc = struct.unpack_from(">I", data, 12)[0]
    nano = struct.unpack_from(">i", data, 16)[0]
    fixType = data[20]
    flags = data[21]
    numSV = data[22]
    lon = struct.unpack_from(">i", data, 24)[0] / 1e7
    lat = struct.unpack_from(">i", data, 28)[0] / 1e7
    height = struct.unpack_from(">i", data, 32)[0] / 1000.0
    hMSL = struct.unpack_from(">i", data, 36)[0] / 1000.0
    hAcc = struct.unpack_from(">I", data, 40)[0] / 1000.0
    vAcc = struct.unpack_from(">I", data, 44)[0] / 1000.0
    velN = struct.unpack_from(">i", data, 48)[0] / 1000.0
    velE = struct.unpack_from(">i", data, 52)[0] / 1000.0
    velD = struct.unpack_from(">i", data, 56)[0] / 1000.0
    gSpeed = struct.unpack_from(">i", data, 60)[0] / 1000.0
    headMot = struct.unpack_from(">i", data, 64)[0] / 1e5
    sAcc = struct.unpack_from(">I", data, 68)[0] / 1000.0
    headAcc = struct.unpack_from(">I", data, 72)[0] / 1e5
    headVeh = struct.unpack_from(">i", data, 76)[0] / 1e5
    gDOP = struct.unpack_from(">H", data, 80)[0] / 100.0
    pDOP = struct.unpack_from(">H", data, 82)[0] / 100.0
    tDOP = struct.unpack_from(">H", data, 84)[0] / 100.0
    vDOP = struct.unpack_from(">H", data, 86)[0] / 100.0
    hDOP = struct.unpack_from(">H", data, 88)[0] / 100.0
    nDOP = struct.unpack_from(">H", data, 90)[0] / 100.0
    eDOP = struct.unpack_from(">H", data, 92)[0] / 100.0

    print(f"  UTC          : {year:04d}-{month:02d}-{day:02d} "
          f"{hour:02d}:{minute:02d}:{second:02d}")
    print(f"  iTOW         : {itow}")
    print(f"  tAcc         : {tAcc} ns")
    print(f"  nano         : {nano} ns")

    print()
    fix_name = FIX_NAMES.get(fixType, f"Unknown ({fixType})")
    print(f"  Fix Type     : {fix_name} ({fixType})")
    if fixType == 0:
        print("  *** GNSS HAS NO FIX ***")
    print(f"  Flags        : 0x{flags:02X}  {flags:08b}")
    print(f"    Valid Fix      : {bool(flags & 0x01)}")
    print(f"    Differential   : {bool(flags & 0x02)}")
    print(f"    Heading Valid  : {bool(flags & 0x20)}")
    print(f"  Satellites   : {numSV}")
    if numSV == 0:
        print("    *** No satellites used ***")

    print()
    print(f"  Valid Flags  : 0x{valid:02X}  {valid:08b}")
    print(f"    Date           : {bool(valid & 0x01)}")
    print(f"    Time           : {bool(valid & 0x02)}")
    print(f"    Fully Resolved : {bool(valid & 0x04)}")

    print()
    print(f"  Latitude     : {lat:.8f}")
    print(f"  Longitude    : {lon:.8f}")
    if abs(lat) < 1e-6 and abs(lon) < 1e-6:
        print("    *** Lat/Lon may be invalid (both near zero) ***")
    print(f"  Height       : {height:.3f} m")
    print(f"  MSL Height   : {hMSL:.3f} m")

    print()
    print(f"  H Accuracy   : {hAcc:.3f} m")
    print(f"  V Accuracy   : {vAcc:.3f} m")

    print()
    print(f"  Vel North    : {velN:.3f} m/s")
    print(f"  Vel East     : {velE:.3f} m/s")
    print(f"  Vel Down     : {velD:.3f} m/s")
    print(f"  Ground Speed : {gSpeed:.3f} m/s")

    print()
    print(f"  Heading Mot  : {headMot:.3f} deg")
    print(f"  Heading Veh  : {headVeh:.3f} deg")
    print(f"  S Accuracy   : {sAcc:.3f} m/s")
    print(f"  Hdg Accuracy : {headAcc:.5f} deg")

    print()
    print(f"  GDOP         : {gDOP:.2f}")
    print(f"  PDOP         : {pDOP:.2f}")
    print(f"  TDOP         : {tDOP:.2f}")
    print(f"  VDOP         : {vDOP:.2f}")
    print(f"  HDOP         : {hDOP:.2f}")
    print(f"  NDOP         : {nDOP:.2f}")
    print(f"  EDOP         : {eDOP:.2f}")


def dump_payload(payload):
    i = 0
    n = len(payload)

    while i < n:
        if i + 3 > n:
            print(f"[{i:04d}] Truncated: need 3 bytes, have {n - i}")
            break

        data_id = int.from_bytes(payload[i:i+2], "big")
        size = payload[i + 2]

        if size == 0xFF:
            if i + 5 > n:
                print(f"[{i:04d}] Truncated extended length")
                break
            size = int.from_bytes(payload[i+3:i+5], "big")
            offset = 5
        else:
            offset = 3

        field_start = i + offset
        field_end = field_start + size
        if field_end > n:
            print(f"[{i:04d}] Truncated: XDI 0x{data_id:04X} size={size}, "
                  f"only {n - field_start} bytes remain")
            break

        data = payload[field_start:field_end]

        if len(data) != size:
            print(f"[{i:04d}] Length mismatch: expected {size}, got {len(data)}")
            break

        if data_id == XDI_GNSS_PVT:
            print()
            print("=" * 80)
            print(f"  [{i:04d}] XDI 0x{data_id:04X}  GNSS PVT  Size={size}")
            print("=" * 80)
            decode_gnss_pvt(data)

        elif data_id == XDI_STATUS_WORD:
            print()
            print("=" * 80)
            print(f"  [{i:04d}] XDI 0x{data_id:04X}  Status Word  Size={size}")
            print("=" * 80)
            decode_status_word(data)

        else:
            print(f"  [{i:04d}] XDI 0x{data_id:04X}  Size={size}")

        print()
        i = field_end


def main():
    print("Opening serial...")
    ser = serial.Serial(PORT, BAUD, timeout=1)
    print("Connected.\n")

    while True:
        print(datetime.now())
        print("-" * 80)
        payload = read_packet(ser)
        dump_payload(payload)


if __name__ == "__main__":
    main()
