"""
=========================================================
MTi-8 MTData2 Packet Statistics Analyzer

Author : Eshan Sengupta

Purpose

    • Shows every XDI transmitted
    • Counts occurrence frequency
    • Estimates output rate (Hz)
    • Detects GNSS packets
    • Helps verify Output Configuration

Press Ctrl+C to stop.
=========================================================
"""

import time
import serial

PORT = "/dev/ttyUSB0"
BAUD = 2000000

PREAMBLE = 0xFA
BID = 0xFF
MID_MTDATA2 = 0x36

XDI_NAMES = {
    0x0810: "Temperature",
    0x1010: "UTC Time",
    0x1020: "Packet Counter",
    0x1050: "iTOW",
    0x1060: "Sample Time Fine",

    0x2010: "Quaternion",
    0x2020: "Quaternion F64",
    0x2030: "Euler",
    0x2040: "Euler F64",

    0x3010: "Baro Pressure",

    0x4010: "Delta V",
    0x4020: "Acceleration",
    0x4030: "Free Acceleration",
    0x4040: "Acceleration HR",

    0x7010: "GNSS PVT",
    0x7020: "GNSS Satellites",
    0x7030: "GNSS DOP",

    0x8020: "Rate Of Turn",
    0x8030: "Delta Q",
    0x8040: "Rate Of Turn HR",

    0x9010: "Temperature Legacy",

    0xC020: "Magnetic Field",

    0xE010: "Status Byte",
    0xE020: "Status Word",
}


def read_packet(ser):

    while True:

        if ser.read(1) != bytes([PREAMBLE]):
            continue

        if ser.read(1) != bytes([BID]):
            continue

        mid = ser.read(1)

        if not mid:
            continue

        if mid[0] != MID_MTDATA2:
            continue

        length = ser.read(1)[0]

        if length == 0xFF:
            length = int.from_bytes(ser.read(2), "big")

        payload = ser.read(length)
        ser.read(1)

        return payload


def main():

    print("=" * 70)
    print(" MTi-8 Packet Statistics Analyzer")
    print("=" * 70)

    ser = serial.Serial(
        PORT,
        BAUD,
        timeout=1
    )

    counts = {}
    sizes = {}

    packet_count = 0

    start = time.time()
    last_print = time.time()

    while True:

        payload = read_packet(ser)

        packet_count += 1

        i = 0

        while i < len(payload):

            if i + 3 > len(payload):
                break

            xdi = int.from_bytes(payload[i:i+2], "big")
            size = payload[i+2]

            counts[xdi] = counts.get(xdi, 0) + 1
            sizes[xdi] = size

            i += 3 + size

        now = time.time()

        if now - last_print >= 1.0:

            elapsed = now - start

            print("\n" + "=" * 90)
            print(f"Elapsed : {elapsed:.1f} s")
            print(f"Packets : {packet_count}")
            print("=" * 90)

            print(
                f"{'XDI':<10}"
                f"{'Name':<25}"
                f"{'Size':<8}"
                f"{'Count':<10}"
                f"{'Rate (Hz)':<10}"
            )

            print("-" * 90)

            for xdi in sorted(counts.keys()):

                rate = counts[xdi] / elapsed

                name = XDI_NAMES.get(xdi, "UNKNOWN")

                print(
                    f"0x{xdi:04X}   "
                    f"{name:<25}"
                    f"{sizes[xdi]:<8}"
                    f"{counts[xdi]:<10}"
                    f"{rate:>8.2f}"
                )

            print("-" * 90)

            print("\nGNSS Summary")

            for xdi in (0x7010, 0x7020, 0x7030):

                if xdi in counts:
                    print(
                        f"  FOUND : 0x{xdi:04X} "
                        f"{XDI_NAMES[xdi]}"
                    )
                else:
                    print(
                        f"  MISSING : 0x{xdi:04X} "
                        f"{XDI_NAMES[xdi]}"
                    )

            print("=" * 90)

            last_print = now


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:

        print("\nStopped.")
        