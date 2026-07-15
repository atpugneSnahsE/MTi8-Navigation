"""
=========================================================
NTRIP Client

Author : Eshan Sengupta

Connects to an NTRIP caster, sends GGA at 1 Hz for VRS
mountpoints, and receives RTCM correction messages.

    1. Connect to caster
    2. HTTP 200 OK
    3. Loop:
         Send GGA (1 Hz)
         Receive RTCM
         Queue RTCM

=========================================================
"""

import base64
import queue
import select
import socket
import threading
import time

import config


class NTRIPClient(threading.Thread):

    def __init__(self, serial_reader=None):

        super().__init__(daemon=True)

        self.serial_reader = serial_reader

        self.running = False

        self.socket = None

        self.queue = queue.Queue()

        self.connected = False

        self.total_bytes = 0
        self.total_packets = 0

        self.last_packet_time = None
        self.last_packet_size = 0
        self.last_rtcm_message = None

        self.connection_attempts = 0
        self.last_error = None

        self.last_gga = 0

    # ----------------------------------------------------

    def connect(self):

        self.connection_attempts += 1

        self.socket = socket.socket(

            socket.AF_INET,

            socket.SOCK_STREAM

        )

        self.socket.settimeout(10)

        self.socket.connect(

            (

                config.NTRIP_CASTER,

                config.NTRIP_PORT

            )

        )

        auth = base64.b64encode(

            f"{config.NTRIP_USERNAME}:{config.NTRIP_PASSWORD}".encode()

        ).decode()

        request = (

            f"GET /{config.NTRIP_MOUNTPOINT} HTTP/1.1\r\n"

            f"User-Agent: MTi8-NTRIP\r\n"

            f"Authorization: Basic {auth}\r\n"

            f"Ntrip-Version: Ntrip/2.0\r\n"

            f"\r\n"

        )

        self.socket.sendall(

            request.encode()

        )

        response = b""

        while b"\r\n\r\n" not in response:

            response += self.socket.recv(1024)

        response_text = response.decode(

            errors="ignore"

        )

        if (

            "200 OK" not in response_text and

            "ICY 200" not in response_text

        ):

            raise RuntimeError(

                response_text

            )

        self.socket.setblocking(True)

        self.connected = True

        self.last_gga = 0  # Force immediate GGA

        print()

        print("Connected to NTRIP caster")

    # ----------------------------------------------------

    @staticmethod
    def rtcm_message_type(packet):
        if len(packet) < 6:
            return None
        for i in range(len(packet) - 5):
            if packet[i] != 0xD3:
                continue
            length = ((packet[i + 1] & 0x03) << 8) | packet[i + 2]
            if i + 3 + length + 3 > len(packet) or length < 2:
                continue
            return (packet[i + 3] << 4) | (packet[i + 4] >> 4)
        return None

    # ----------------------------------------------------

    def disconnect(self):

        self.connected = False

        if self.socket is not None:

            try:

                self.socket.close()

            except Exception:

                pass

    # ----------------------------------------------------

    def checksum(self, sentence):

        checksum = 0

        for c in sentence:

            checksum ^= ord(c)

        return checksum

    # ----------------------------------------------------

    def build_gga(self):

        if self.serial_reader is not None:

            parser = self.serial_reader.parser

            s = parser.get_state() if parser else None

            has_gnss = s is not None and s.position.is_valid()

        else:

            has_gnss = False

        if not has_gnss:

            lat = config.APPROX_LATITUDE

            lon = config.APPROX_LONGITUDE

            alt = config.APPROX_ALTITUDE

        else:

            lat = s.position.latitude

            lon = s.position.longitude

            alt = s.position.altitude

        hhmmss = time.strftime(

            "%H%M%S",

            time.gmtime()

        )

        lat_deg = int(abs(lat))

        lat_min = (abs(lat) - lat_deg) * 60

        lon_deg = int(abs(lon))

        lon_min = (abs(lon) - lon_deg) * 60

        ns = "N" if lat >= 0 else "S"

        ew = "E" if lon >= 0 else "W"

        body = (

            f"GPGGA,"

            f"{hhmmss}.00,"

            f"{lat_deg:02d}"

            f"{lat_min:07.4f},"

            f"{ns},"

            f"{lon_deg:03d}"

            f"{lon_min:07.4f},"

            f"{ew},"

            f"1,"

            f"12,"

            f"0.8,"

            f"{alt:.2f},M,"

            f"0.0,M,,"

        )

        cs = self.checksum(body)

        return f"${body}*{cs:02X}\r\n".encode()

    # ----------------------------------------------------

    def send_gga(self):

        if not self.connected:

            return

        try:

            gga = self.build_gga()

            self.socket.sendall(gga)

            if config.DEBUG_RTK:

                print("GGA sent")

        except Exception as e:

            if config.DEBUG_RTK:

                print("Failed to send GGA:", e)

    # ----------------------------------------------------

    def stop(self):

        self.running = False

        self.disconnect()

    # ----------------------------------------------------

    def run(self):

        self.running = True

        while self.running:

            try:

                if not self.connected:

                    self.connect()

                now = time.time()

                if now - self.last_gga >= config.GGA_INTERVAL:

                    if config.SEND_GGA:

                        self.send_gga()

                        self.last_gga = now

                readable, _, _ = select.select(

                    [self.socket], [], [], 0.1

                )

                if readable:

                    data = self.socket.recv(4096)

                    if len(data) == 0:

                        raise RuntimeError(

                            "Caster disconnected."

                        )

                    self.total_bytes += len(data)
                    self.total_packets += 1

                    self.last_packet_time = time.time()
                    self.last_packet_size = len(data)
                    msg_type = self.rtcm_message_type(data)
                    if msg_type is not None:
                        self.last_rtcm_message = msg_type

                    self.queue.put(data)

                    if config.DEBUG_RTK:

                        print(f"Received RTCM packet ({len(data)} bytes)")

            except Exception as e:

                self.connected = False
                self.last_error = str(e)

                self.disconnect()

                print()

                print("NTRIP:", e)

                time.sleep(5)

    # ----------------------------------------------------

    def has_data(self):

        return not self.queue.empty()

    # ----------------------------------------------------

    def get_rtcm(self):

        try:

            return self.queue.get_nowait()

        except queue.Empty:

            return None

    # ----------------------------------------------------

    def bytes_received(self):

        return self.total_bytes

    # ----------------------------------------------------

    def status(self):
        now = time.time()
        age = None
        if self.last_packet_time is not None:
            age = now - self.last_packet_time
        reconnecting = self.running and not self.connected and self.connection_attempts > 0

        return {

            "connected":

                self.connected,

            "state":

                "Connected" if self.connected else (
                    "Reconnecting" if reconnecting else "Disconnected"
                ),

            "bytes":

                self.total_bytes,

            "packets":

                self.total_packets,

            "attempts":

                self.connection_attempts,

            "queue":

                self.queue.qsize(),

            "last_packet":

                self.last_packet_time,

            "age":

                age,

            "last_packet_size":

                self.last_packet_size,

            "last_rtcm_message":

                self.last_rtcm_message,

            "last_error":

                self.last_error

        }

    # ----------------------------------------------------

    def print_status(self):

        s = self.status()

        print()

        print("=" * 60)

        print("NTRIP STATUS")

        print("=" * 60)

        print(

            "Connected :", s["connected"]

        )

        print(

            "Bytes     :", s["bytes"]

        )

        print(

            "Queue      :", s["queue"]

        )

        print(

            "Attempts   :", s["attempts"]

        )

        print("=" * 60)


# ==========================================================
# Standalone Test
# ==========================================================

if __name__ == "__main__":

    client = NTRIPClient()

    client.start()

    try:

        while True:

            if client.has_data():

                packet = client.get_rtcm()

                print(

                    f"Received RTCM "

                    f"{len(packet)} bytes"

                )

            time.sleep(0.05)

    except KeyboardInterrupt:

        client.stop()

        client.print_status()
