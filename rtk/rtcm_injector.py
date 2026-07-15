"""
=========================================================
RTCM Injector

Author : Eshan Sengupta

Receives RTCM correction messages from NTRIPClient and
injects them into the MTi-8 serial interface.

All GGA generation is handled by NTRIPClient.
This module only writes corrections to the serial port.
=========================================================
"""

import threading
import time

import config


class RTCMInjector(threading.Thread):

    def __init__(self, serial_reader, ntrip_client):

        super().__init__(daemon=True)

        self.serial_reader = serial_reader

        self.ntrip = ntrip_client

        self.running = False

        self.injected_bytes = 0

        self.injected_packets = 0

        self.write_failures = 0

        self.last_injection_time = 0.0

        self.injection_rate = 0.0

        self._rate_start = 0.0

        self._rate_count = 0

    # -----------------------------------------------------

    def stop(self):

        self.running = False

    # -----------------------------------------------------

    def inject_rtcm(self):

        while self.ntrip.has_data():

            packet = self.ntrip.get_rtcm()

            if packet is None:
                return

            try:

                self.serial_reader.serial.write(packet)

                self.injected_packets += 1

                self.injected_bytes += len(packet)

                self.last_injection_time = time.time()

                self._rate_count += 1
                if self._rate_start == 0:
                    self._rate_start = time.time()
                    self._rate_count = 0
                elapsed = time.time() - self._rate_start
                if elapsed >= 1.0:
                    self.injection_rate = self._rate_count / elapsed
                    self._rate_start = time.time()
                    self._rate_count = 0

            except Exception:

                self.write_failures += 1

    # -----------------------------------------------------

    def run(self):

        self.running = True

        while self.running:

            try:

                self.inject_rtcm()

                time.sleep(0.001)

            except Exception as e:

                print()

                print("RTCM Injector:", e)

                time.sleep(1)

    # -----------------------------------------------------

    def statistics(self):

        return {

            "packets":

                self.injected_packets,

            "write_failures":

                self.write_failures,

            "bytes":

                self.injected_bytes,

            "ntrip_connected":

                self.ntrip.connected,

            "rate":

                self.injection_rate,

            "last_injection":

                self.last_injection_time,

        }

    # -----------------------------------------------------

    def print_statistics(self):

        s = self.statistics()

        print()

        print("=" * 60)

        print("RTCM INJECTOR")

        print("=" * 60)

        print(

            "Injected Packets :",

            s["packets"]

        )

        print(

            "Injected Bytes   :",

            s["bytes"]

        )

        print(

            "NTRIP Connected  :",

            s["ntrip_connected"]

        )

        print("=" * 60)


# ==========================================================
# Standalone Test
# ==========================================================

if __name__ == "__main__":

    from xsens.serial_reader import SerialReader
    from rtk.ntrip_client import NTRIPClient

    reader = SerialReader()

    reader.start()

    reader.wait_until_ready()

    ntrip = NTRIPClient()

    ntrip.start()

    injector = RTCMInjector(

        reader,

        ntrip

    )

    injector.start()

    try:

        while True:

            stats = injector.statistics()

            print(

                f"\rInjected "

                f"{stats['packets']} RTCM packets | "

                f"{stats['bytes']} bytes",

                end="",

                flush=True

            )

            time.sleep(0.25)

    except KeyboardInterrupt:

        injector.stop()

        ntrip.stop()

        reader.stop()

        injector.print_statistics()
