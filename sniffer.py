"""
===============================================================
MTi-8 Linux MTData2 Sniffer
Part 1/4

Author : Eshan Sengupta

Linux compatible
Python >=3.10

===============================================================
"""

import time
import struct
import serial

from serial.tools import list_ports


# ===============================================================
# Configuration
# ===============================================================

BAUD_CANDIDATES = [

    2000000,
    921600,
    460800,
    230400,
    115200

]

CAPTURE_TIME = 10

GO_TO_MEASUREMENT = bytes([

    0xFA,
    0xFF,
    0x10,
    0x00,
    0xF1

])

# ===============================================================
# Known MTData2 IDs
# ===============================================================

XDI_NAMES = {

    0x0810: "Temperature",

    0x1010: "UTC Time",
    0x1020: "Packet Counter",
    0x1060: "Sample Time Fine",

    0x2010: "Quaternion",
    0x2020: "Rotation Matrix",
    0x2030: "Euler Angles",

    0x3010: "Barometer",

    0x4010: "Delta V",

    0x4020: "Acceleration",
    0x4030: "Free Acceleration",

    0x5020: "Altitude",
    0x5030: "ECEF Position",
    0x5040: "Latitude/Longitude",

    0x7010: "GNSS PVT",
    0x7050: "GNSS Satellites",
    0x7060: "GNSS DOP",
    0x7070: "GNSS SOL",
    0x7080: "GNSS Clock",

    0x8020: "Rate of Turn",
    0x8030: "RateOfTurn HR",
    0x8040: "Delta Q",

    0xC020: "Magnetic Field",

    0xD010: "Velocity",

    0xE010: "Status Byte",
    0xE020: "Status Word",
    0xE040: "RSSI",

}

# ===============================================================
# Utility Functions
# ===============================================================

def checksum_ok(frame):

    return (sum(frame[1:]) & 0xFF) == 0


# ===============================================================

def find_mti():

    print()

    print("Searching for MTi-8...")

    ports = list_ports.comports()

    for port in ports:

        print(

            f"Found {port.device:12s}"

            f"  {port.description}"

        )

        if port.vid == 0x2639:

            print()

            print("MTi-8 detected.")

            return port.device

        if "Motion Tracker" in port.description:

            print()

            print("MTi-8 detected.")

            return port.device

    return None


# ===============================================================

def open_serial(port, baud):

    try:

        ser = serial.Serial(

            port=port,

            baudrate=baud,

            timeout=0.1

        )

        ser.reset_input_buffer()

        ser.reset_output_buffer()

        return ser

    except PermissionError:

        print()

        print("Permission denied.")

        print()

        print(

            "Make sure your user belongs "

            "to the dialout group."

        )

        print()

        raise

    except Exception:

        return None


# ===============================================================

class MTDataStatistics:

    def __init__(self):

        self.total_bytes = 0

        self.good_frames = 0

        self.bad_frames = 0

        self.first_frame = None

        self.mids = {}

        self.xdis = {}

        self.printed = set()

    # ----------------------------------------------------------

    def add_mid(self, mid):

        self.mids[mid] = self.mids.get(mid, 0) + 1

    # ----------------------------------------------------------

    def add_xdi(self, xdi):

        self.xdis[xdi] = self.xdis.get(xdi, 0) + 1
    # ===============================================================
# Frame Sniffer
# Part 2/4
# ===============================================================

def sniff(port, baud, seconds=CAPTURE_TIME):

    ser = open_serial(

        port,

        baud

    )

    if ser is None:

        return None

    print()

    print("=" * 70)

    print(f"Trying baud rate : {baud}")

    print("=" * 70)

    ser.write(

        GO_TO_MEASUREMENT

    )

    time.sleep(0.20)

    ser.reset_input_buffer()

    buffer = bytearray()

    stats = MTDataStatistics()

    start = time.time()

    while time.time() - start < seconds:

        waiting = ser.in_waiting

        if waiting:

            chunk = ser.read(waiting)

            buffer.extend(chunk)

            stats.total_bytes += len(chunk)

        while len(buffer) >= 4:

            if buffer[0] != 0xFA:

                del buffer[0]

                continue

            mid = buffer[2]

            length = buffer[3]

            if length == 0xFF:

                if len(buffer) < 6:

                    break

                length = struct.unpack(

                    ">H",

                    buffer[4:6]

                )[0]

                header_size = 6

            else:

                header_size = 4

            frame_size = (

                header_size +

                length +

                1

            )

            if len(buffer) < frame_size:

                break

            frame = bytes(

                buffer[:frame_size]

            )

            if stats.good_frames == 0:

                print()

                print("FIRST FRAME")

                print(frame.hex())

                print()

            if checksum_ok(frame):

                stats.good_frames += 1

                stats.add_mid(mid)

                if stats.first_frame is None:

                    stats.first_frame = frame

                    print()

                    print("First valid frame:")

                    print(

                        frame.hex()

                    )

                    print()

                print()

                print(f"MID = 0x{mid:02X}")

                if mid == 0x36:

                    payload = frame[

                        header_size:

                        header_size + length

                    ]

                    print()

                    print("-" * 70)

                    print(

                        f"MTData2 Frame "

                        f"{stats.good_frames}"

                    )

                    print("-" * 70)

                    parse_mtdata2(

                        payload,

                        stats

                    )

                else:

                    print(

                        f"Unknown MID "

                        f"0x{mid:02X}"

                    )

            else:

                stats.bad_frames += 1

            del buffer[:frame_size]

        time.sleep(

            0.002

        )

    ser.close()

    return stats

    # ===============================================================
# Packet Parser
# Part 3/4
# ===============================================================

def list_xdi_ids(payload):
    ids = []
    i = 0
    n = len(payload)
    while i + 3 <= n:
        xdi = int.from_bytes(payload[i:i+2], "big")
        size = payload[i + 2]
        if size == 0xFF:
            if i + 5 > n:
                break
            size = int.from_bytes(payload[i+3:i+5], "big")
            offset = 5
        else:
            offset = 3
        i += offset + size
        ids.append(f"0x{xdi:04X}")
    return ids


def parse_mtdata2(payload, stats):

    ids = list_xdi_ids(payload)

    print(f"    XDI IDs: {ids}")

    print()

    index = 0

    while index + 3 <= len(payload):

        try:

            data_id = struct.unpack(

                ">H",

                payload[index:index + 2]

            )[0]

            size = payload[index + 2]

            data = payload[

                index + 3:

                index + 3 + size

            ]

            base = data_id & 0xFFF0

            stats.add_xdi(data_id)

            name = XDI_NAMES.get(

                base,

                f"UNKNOWN (0x{base:04X})"

            )

            if data_id not in stats.printed:

                stats.printed.add(data_id)

                print(
                    f"    XDI=0x{data_id:04X}  "
                    f"Base=0x{base:04X}  "
                    f"Size={size}"
                )

                print(data.hex())

                print()

            # --------------------------------------------
            # Euler Angles
            # --------------------------------------------

            if base == 0x2030 and size == 12:

                roll, pitch, yaw = struct.unpack(

                    ">fff",

                    data

                )

                print(

                    f"       Roll  : {roll:.3f}"

                )

                print(

                    f"       Pitch : {pitch:.3f}"

                )

                print(

                    f"       Yaw   : {yaw:.3f}"

                )

            # --------------------------------------------
            # Quaternion
            # --------------------------------------------

            elif base == 0x2010 and size == 16:

                q = struct.unpack(

                    ">ffff",

                    data

                )

                print(

                    "       Quaternion:",

                    q

                )

            # --------------------------------------------
            # Acceleration
            # --------------------------------------------

            elif base == 0x4020 and size == 12:

                ax, ay, az = struct.unpack(

                    ">fff",

                    data

                )

                print(

                    f"       Acc : "

                    f"{ax:.4f}, "

                    f"{ay:.4f}, "

                    f"{az:.4f}"

                )

            # --------------------------------------------
            # Rate of Turn
            # --------------------------------------------

            elif base == 0x8020 and size == 12:

                gx, gy, gz = struct.unpack(

                    ">fff",

                    data

                )

                print(

                    f"       Gyro : "

                    f"{gx:.4f}, "

                    f"{gy:.4f}, "

                    f"{gz:.4f}"

                )

            # --------------------------------------------
            # Magnetic Field
            # --------------------------------------------

            elif base == 0xC020 and size == 12:

                mx, my, mz = struct.unpack(

                    ">fff",

                    data

                )

                print(

                    f"       Mag : "

                    f"{mx:.4f}, "

                    f"{my:.4f}, "

                    f"{mz:.4f}"

                )

            # --------------------------------------------
            # Packet Counter
            # --------------------------------------------

            elif base == 0x1020 and size == 2:

                packet = struct.unpack(

                    ">H",

                    data

                )[0]

                print(

                    f"       Packet Counter : {packet}"

                )

            # --------------------------------------------
            # Sample Time Fine
            # --------------------------------------------

            elif base == 0x1060 and size == 4:

                ticks = struct.unpack(

                    ">I",

                    data

                )[0]

                print(

                    f"       Sample Time : {ticks}"

                )

            # --------------------------------------------
            # Status Word
            # --------------------------------------------

            elif base == 0xE020:

                print(

                    "       Status Raw :",

                    data.hex()

                )

            # --------------------------------------------
            # UTC
            # --------------------------------------------

            elif base == 0x1010:

                print(

                    "       UTC Raw:",

                    data.hex()

                )

            else:

                print("       Raw:", data.hex())

            index += 3 + size

        except Exception as e:

            print()

            print("Parser Error:", e)

            break

        # ===============================================================
# Main
# Part 4/4
# ===============================================================

def print_summary(stats):

    print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(f"Total Bytes      : {stats.total_bytes}")
    print(f"Good Frames      : {stats.good_frames}")
    print(f"Bad Frames       : {stats.bad_frames}")

    print()

    print("MIDs Detected")

    if len(stats.mids) == 0:

        print("  None")

    else:

        for mid, count in sorted(stats.mids.items()):

            print(

                f"  MID 0x{mid:02X}    {count} frames"

            )

    print()

    print("Exact Data IDs")

    if len(stats.xdis) == 0:

        print("  None")

    else:

        for xdi in sorted(stats.xdis):

            print(hex(xdi))

    print()

    print("=" * 70)

    if 0x7010 in stats.xdis:

        print("GNSS PVT FOUND")

    else:

        print("GNSS PVT NOT FOUND")

    if 0xE020 in stats.xdis:

        print("Status Word FOUND")

    else:

        print("Status Word NOT FOUND")

    if 0x2030 in stats.xdis:

        print("Euler Angles FOUND")

    else:

        print("Euler Angles NOT FOUND")

    print("=" * 70)


# ===============================================================

def main():

    port = find_mti()

    if port is None:

        print()

        print("No MTi-8 detected.")

        return

    print()

    print(f"Using serial port : {port}")

    print()

    for baud in BAUD_CANDIDATES:

        stats = sniff(

            port,

            baud,

            CAPTURE_TIME

        )

        if stats is None:

            continue

        print_summary(stats)

        if stats.good_frames > 0:

            print()

            print("=" * 70)
            print("CORRECT BAUD RATE FOUND")
            print("=" * 70)

            break


# ===============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print()

        print("Interrupted by user.")

    except Exception as e:

        print()

        print("Fatal error:")

        print(e)