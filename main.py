"""
main.py

MTi-8 Navigation System

Zero-alloc pipeline:
  SerialReader reads → XbusParser updates state in-place → timers consume

Threads / Timers:
  - SerialReader (thread):   reads + parses at wire rate, atomic reference swap
  - _scene_timer (30 Hz):    Open3D poll_events + update_renderer
  - _process_timer (60 Hz):  pop latest state → IMU/GNSS parsers → dashboard → logger
  - Dashboard._refresh (20 Hz):  PyQtGraph redraw (internal timer)
  - NTRIPClient + RTCMInjector: independent threads
  - CSVLogger: internal write thread
"""

import os
import signal
import sys
import traceback

if os.name != "nt" and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtCore
from PyQt5 import QtWidgets

import config

from xsens.serial_reader import SerialReader
from xsens.imu_parser import IMUParser
from xsens.gnss_parser import GNSSParser

from rtk.ntrip_client import NTRIPClient
from rtk.rtcm_injector import RTCMInjector
from rtk.gps_status import GPSStatus

try:
    from visualization.scene_manager import SceneManager
except Exception as exc:
    print(f"Scene manager unavailable: {exc}")

    class SceneManager:
        def __init__(self):
            self.vis = None
            self._scene_available = False

        def update(self, *args, **kwargs):
            return True

        def destroy(self):
            return None

try:
    from visualization.dashboard import Dashboard
except Exception as exc:
    print(f"Dashboard unavailable: {exc}")

    class Dashboard:
        def __init__(self, *args, **kwargs):
            self._ntrip = None
            self._injector = None

        def update_navigation_state(self, *args, **kwargs):
            return None

        def update_trajectory(self, *args, **kwargs):
            return None

        def show(self):
            return None

from logger.csv_logger import CSVLogger


def preflight_serial_port():

    reader = SerialReader()

    port = reader.resolve_port()

    if port is not None:

        if port != config.SERIAL_PORT:

            print(f"MTi-8 serial port auto-detected: {port}")

        return True

    available = ", ".join(p.device for p in reader.available_ports) or "none"

    print("No MTi-8 serial port found.")

    print(f"Configured port : {config.SERIAL_PORT}")

    print(f"Available ports : {available}")

    print("Connect the MTi-8, then run `python main.py` again.")

    return False


class NavigationSystem:

    def __init__(self):

        self.reader = SerialReader()

        self.imu = IMUParser()

        self.gnss = GNSSParser()

        self.gps_status = GPSStatus()

        self.scene = SceneManager()

        self.logger = CSVLogger()

        if config.RTK_ENABLED:

            self.ntrip = NTRIPClient(serial_reader=self.reader)

            self.injector = RTCMInjector(

                self.reader,

                self.ntrip

            )

        else:

            self.ntrip = None

            self.injector = None

        try:
            self.dashboard = Dashboard(

                ntrip_client=self.ntrip,

                injector=self.injector

            )
        except Exception as exc:
            print(f"Dashboard initialization failed: {exc}")
            self.dashboard = None

        self._latest_state = None

        self._last_counter = -1

        self._latest_trajectory = []

        self._process_timer = QtCore.QTimer()

        self._process_timer.timeout.connect(self._process_queue)

        self._process_timer.start(1000 // config.GUI_UPDATE_RATE)

        self._scene_timer = QtCore.QTimer()

        self._scene_timer.timeout.connect(self._update_scene)

        self._scene_timer.start(1000 // config.SCENE_REFRESH_RATE)

    def _process_queue(self):

        state = self.reader.latest()

        if state is None:
            return

        if state.packet_counter == self._last_counter:
            return

        self._last_counter = state.packet_counter

        self._latest_state = state

        self._latest_trajectory = self.reader.parser.get_trajectory()

        self.imu.update(state)

        self.gnss.update(state)

        self.gps_status.update(state)

        if self.dashboard is not None:
            self.dashboard.update_navigation_state(state, self._latest_trajectory)

        if config.ENABLE_CSV_LOGGING:

            self.logger.log(state, self.reader.parser)

    def _update_scene(self):

        if self.scene is not None:

            running = self.scene.update(self._latest_state, self.reader.parser)

            if not running:

                self.stop()

                QtWidgets.QApplication.quit()

    def start(self):

        self.reader.start()

        print("Waiting for MTi-8...")

        if not self.reader.wait_until_ready():

            error = self.reader.last_error

            if error is not None:

                print()

                print("No MTi-8 detected.")

                print(error)

            else:

                print()

                print("No MTData2 packets received from MTi-8.")

                print(
                    "Check baud rate, output configuration, cable, and "
                    "whether another program is using the serial port."
                )

            self.stop()

            QtWidgets.QApplication.quit()

            return

        print("MTi-8 Connected.")

        self.logger.start()

        if config.RTK_ENABLED:

            self.ntrip.start()

            self.injector.start()

        if self.dashboard is not None:
            self.dashboard.show()

    def stop(self):

        print("\nStopping Navigation System...")

        self._process_timer.stop()

        self._scene_timer.stop()

        self.reader.stop()

        self.logger.stop()

        if config.RTK_ENABLED:

            self.injector.stop()

            self.ntrip.stop()

        self.logger.close()

        if self.scene is not None:
            self.scene.destroy()

        print("Done.")

    def cleanup(self):

        self.stop()


def main():

    if not preflight_serial_port():

        return

    app = QtWidgets.QApplication(sys.argv)

    nav = NavigationSystem()

    def shutdown(*args):

        nav.stop()

        QtWidgets.QApplication.quit()

    signal.signal(signal.SIGINT, shutdown)

    signal.signal(signal.SIGTERM, shutdown)

    def start_nav():

        try:

            nav.start()

        except Exception:

            traceback.print_exc()

            nav.stop()

            QtWidgets.QApplication.quit()

    QtCore.QTimer.singleShot(100, start_nav)

    sys.exit(app.exec_())


if __name__ == "__main__":

    main()
