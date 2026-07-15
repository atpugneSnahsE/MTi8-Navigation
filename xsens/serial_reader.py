"""
Serial Reader

Reads raw MTData2 packets from the MTi-8 and updates
XbusParser state in-place. Latest NavigationState is
exposed via atomic reference swap — no queue overhead.
"""

import threading
import time
import serial
from serial.tools import list_ports

import config

from xsens.xbus_parser import XbusParser


class SerialReader(threading.Thread):

    def __init__(self, port=None):

        super().__init__(daemon=True)

        self.serial = None
        self.port = port or config.SERIAL_PORT
        self.last_error = None
        self.available_ports = []

        self.parser = XbusParser()

        self.buffer = bytearray()

        self.running = False

        self._latest = None

        self.bytes_received = 0

        self.frames_received = 0

        self.baud_rates = [
            config.BAUD_RATE,
            115200,
            230400,
            460800,
            921600,
            3000000,
        ]

        self._active_baudrate = None

    @staticmethod
    def scan_ports():

        return list(list_ports.comports())

    @classmethod
    def detect_port(cls):

        ports = cls.scan_ports()

        for port in ports:

            if port.vid == 0x2639:

                return port.device, ports

            description = port.description or ""

            if "Motion Tracker" in description or "MTi" in description:

                return port.device, ports

        return None, ports

    def _port_exists(self, port_name):

        return any(port.device == port_name for port in self.available_ports)

    def resolve_port(self):

        self.available_ports = self.scan_ports()

        if self.port and self._port_exists(self.port):

            return self.port

        detected, ports = self.detect_port()

        self.available_ports = ports

        if detected is not None:

            self.port = detected

            return self.port

        if self.port and self.port != config.SERIAL_PORT:

            return self.port

        return None

    def open(self):

        port = self.resolve_port()

        if port is None:

            available = ", ".join(p.device for p in self.available_ports) or "none"

            raise serial.SerialException(

                f"No MTi-8 serial port found. Configured port is "

                f"{config.SERIAL_PORT}; available serial ports: {available}"

            )

        for baudrate in self.baud_rates:

            try:
                self.serial = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    timeout=config.SERIAL_TIMEOUT,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                )

            except (serial.SerialException, OSError):
                continue

            if self.serial.is_open:

                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                time.sleep(0.1)

                initial = self.serial.read(64)

                if initial:
                    self.buffer.extend(initial)
                    print(
                        f"Detected serial activity on {port} at {baudrate} bps"
                    )

                self._active_baudrate = baudrate

                self.running = True

                print(f"Connected to {port} at {baudrate} bps")

                return self.serial.is_open

            self.serial.close()

        raise serial.SerialException(
            f"Could not open {port} with any supported baud rate. Tried: "
            f"{', '.join(str(b) for b in self.baud_rates)}"
        )

    def close(self):

        self.running = False

        time.sleep(0.1)

        if self.serial is not None:

            try:

                self.serial.close()

            except Exception:

                pass

    def latest(self):
        return self._latest

    def run(self):

        try:

            self.open()

        except Exception as e:

            self.last_error = e

            self.running = False

            return

        while self.running:

            try:

                waiting = self.serial.in_waiting

                if waiting:

                    data = self.serial.read(waiting)

                    self.bytes_received += len(data)

                    self.buffer.extend(data)

                while True:

                    state = self.parser.parse_buffer(self.buffer)

                    if state is None:

                        break

                    self.parser.update_history()

                    self._latest = state

                    self.frames_received += 1

                time.sleep(0.001)

            except serial.SerialException as e:

                self.last_error = e

                print()

                print("Serial Error")

                print(e)

                self.running = False

            except Exception as e:

                self.last_error = e

                print()

                print("Reader Error")

                print(e)

                self.running = False

        self.close()

    def parser_instance(self):

        return self.parser

    def statistics(self):

        return {

            "bytes_received": self.bytes_received,

            "frames_received": self.frames_received,

            "trajectory_points":

                len(

                    self.parser.get_trajectory()

                )

        }

    def print_statistics(self):

        stats = self.statistics()

        print()

        print("=" * 60)

        print("Serial Reader Statistics")

        print("=" * 60)

        print("Bytes Received :", stats["bytes_received"])

        print("Frames Parsed  :", stats["frames_received"])

        print("Trajectory     :", stats["trajectory_points"])

        print("=" * 60)

    def wait_until_ready(self, timeout=10):

        start = time.time()

        while time.time() - start < timeout:

            if self.last_error is not None:

                return False

            if self.latest() is not None:

                return True

            time.sleep(0.05)

        return False

    def is_connected(self):

        if self.serial is None:

            return False

        return self.serial.is_open

    def reconnect(self):

        self.close()

        time.sleep(1)

        self.buffer.clear()

        self._latest = None

        self.bytes_received = 0

        self.frames_received = 0

        self.open()

    def stop(self):

        self.running = False

    def __repr__(self):

        return (

            f"SerialReader("

            f"Connected={self.is_connected()}, "

            f"Frames={self.frames_received}, "

            f"Bytes={self.bytes_received})"

        )


if __name__ == "__main__":

    reader = SerialReader()

    reader.start()

    print("Waiting for MTi-8...")

    if reader.wait_until_ready():

        print("Connected")

    else:

        print("No data received")

        exit()

    try:

        while True:

            state = reader.latest()

            if state is None:

                continue

            print(

                f"\r"

                f"Pkt {state.packet_counter:6d} | "

                f"Roll {state.orientation.roll:7.2f} | "

                f"Pitch {state.orientation.pitch:7.2f} | "

                f"Yaw {state.orientation.yaw:7.2f}",

                end="",

                flush=True

            )

            time.sleep(0.02)

    except KeyboardInterrupt:

        print()

        reader.print_statistics()

        reader.stop()
