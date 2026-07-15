import sys
import time
import numpy as np

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView
import pyqtgraph as pg

import config

import os


class Dashboard(QtWidgets.QMainWindow):

    def __init__(self, ntrip_client=None, injector=None):

        super().__init__()

        self._ntrip = ntrip_client

        self._injector = injector

        self.setWindowTitle("MTi-8 Navigation Dashboard")

        self.resize(
            config.WINDOW_WIDTH,
            config.WINDOW_HEIGHT
        )

        self.central = QtWidgets.QWidget()

        self.setCentralWidget(self.central)

        self.layout = QtWidgets.QGridLayout()

        self.central.setLayout(self.layout)

        self.status_label = QtWidgets.QLabel("Waiting for MTi-8 data...")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 8px;")
        self.fps_label = QtWidgets.QLabel("")
        self.fps_label.setStyleSheet("font-size: 11px; color: #888; margin-bottom: 8px;")
        banner = QtWidgets.QHBoxLayout()
        banner.setContentsMargins(0, 0, 0, 0)
        banner.addWidget(self.status_label, 1)
        banner.addWidget(self.fps_label, 0)
        banner_widget = QtWidgets.QWidget()
        banner_widget.setLayout(banner)
        self.layout.addWidget(banner_widget, 0, 0, 1, 4)

        self.status_widget = QtWidgets.QWidget()
        self.status_layout = QtWidgets.QGridLayout()
        self.status_layout.setHorizontalSpacing(4)
        self.status_widget.setLayout(self.status_layout)
        self.layout.addWidget(self.status_widget, 1, 0, 3, 2)

        self.status_labels = {}

        def _section_header(text):
            h = QtWidgets.QLabel(text)
            h.setStyleSheet("font-weight: bold; color: #4af; font-size: 11px; padding: 2px 0; margin-top: 4px;")
            return h

        sections = [
            ("GNSS", [
                ("Status", "gnss_state"),
                ("Sat", "num_sv"),
                ("Differential", "differential"),
                ("Carrier", "carrier_state"),
                ("Nav Qual", "nav_quality"),
            ]),
            ("TIME", [
                ("Packet", "packet_counter"),
                ("UTC", "utc"),
                ("Clock", "clock_sync"),
                ("PPS", "pps"),
            ]),
            ("POSITION", [
                ("Latitude", "latitude"),
                ("Longitude", "longitude"),
                ("Altitude", "altitude"),
                ("MSL", "height_msl"),
            ]),
            ("ACCURACY", [
                ("H Accuracy", "horizontal_accuracy"),
                ("V Accuracy", "vertical_accuracy"),
                ("S Accuracy", "speed_accuracy"),
                ("Hdg Acc", "heading_accuracy"),
                ("HDOP", "hdop"),
            ]),
            ("VELOCITY", [
                ("Vel N", "velocity_n"),
                ("Vel E", "velocity_e"),
                ("Vel D", "velocity_d"),
                ("Speed", "ground_speed"),
            ]),
            ("HEADING", [
                ("H Motion", "heading_motion"),
                ("H Vehicle", "heading_vehicle"),
            ]),
            ("ORIENTATION", [
                ("Roll", "roll"),
                ("Pitch", "pitch"),
                ("Yaw", "yaw"),
            ]),
            ("CORRECTIONS", [
                ("NTRIP", "ntrip_state"),
                ("RTCM Pkts", "rtcm_packets"),
                ("RTCM Rate", "rtcm_rate"),
                ("RTCM Age", "rtcm_age"),
                ("RTCM Writes", "rtcm_writes"),
            ]),
        ]

        row = 0
        # 20 rows each side: GNSS(6) + TIME(5) + VELOCITY(5) + ORIENTATION(4) = 20
        left_sections = [sections[0], sections[1], sections[4], sections[6]]
        # POSITION(5) + ACCURACY(6) + HEADING(3) + CORRECTIONS(6) = 20
        right_sections = [sections[2], sections[3], sections[5], sections[7]]
        for sec_name, sec_items in left_sections:
            header = _section_header("▸ " + sec_name)
            self.status_layout.addWidget(header, row, 0, 1, 2)
            row += 1
            for label, key in sec_items:
                title = QtWidgets.QLabel(label + ":")
                title.setStyleSheet("font-weight: bold;")
                value = QtWidgets.QLabel("---")
                value.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                self.status_layout.addWidget(title, row, 0)
                self.status_layout.addWidget(value, row, 1)
                self.status_labels[key] = value
                row += 1

        row = 0
        for sec_name, sec_items in right_sections:
            header = _section_header("▸ " + sec_name)
            self.status_layout.addWidget(header, row, 2, 1, 2)
            row += 1
            for label, key in sec_items:
                title = QtWidgets.QLabel(label + ":")
                title.setStyleSheet("font-weight: bold;")
                value = QtWidgets.QLabel("---")
                value.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
                self.status_layout.addWidget(title, row, 2)
                self.status_layout.addWidget(value, row, 3)
                self.status_labels[key] = value
                row += 1

        self.xy_plot = pg.PlotWidget()

        self.xy_plot.setTitle("Navigation Trajectory")

        self.xy_plot.setLabel("left", "North (m)")

        self.xy_plot.setLabel("bottom", "East (m)")

        self.xy_plot.showGrid(x=True, y=True)

        self.layout.addWidget(self.xy_plot, 1, 2, 3, 1)

        self.xy_curve = self.xy_plot.plot(
            pen=pg.mkPen(color=(0, 255, 0), width=4)
        )

        self.xy_plot.plotItem.vb.autoRange(padding=0.02)

        def _make_att_plot(title):
            pw = pg.PlotWidget()
            pw.setTitle(title)
            pw.setLabel("left", "deg")
            pw.plotItem.getAxis("left").enableAutoSIPrefix(False)
            return pw

        self.roll_plot = _make_att_plot("Roll")
        self.roll_curve = self.roll_plot.plot(pen="r")
        self.layout.addWidget(self.roll_plot, 4, 0)

        self.pitch_plot = _make_att_plot("Pitch")
        self.pitch_curve = self.pitch_plot.plot(pen="g")
        self.layout.addWidget(self.pitch_plot, 4, 1)

        self.yaw_plot = _make_att_plot("Yaw")
        self.yaw_curve = self.yaw_plot.plot(pen="b")
        self.layout.addWidget(self.yaw_plot, 4, 2)

        map_path = os.path.join(os.path.dirname(__file__), "map.html")
        self.map_view = QWebEngineView()
        self.map_view.load(QtCore.QUrl.fromLocalFile(map_path))
        self.map_view.setMinimumHeight(300)
        self.layout.addWidget(self.map_view, 1, 3, 4, 1)

        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 1)
        self.layout.setColumnStretch(2, 3)
        self.layout.setColumnStretch(3, 3)

        self.layout.setRowStretch(0, 0)
        self.layout.setRowStretch(1, 1)
        self.layout.setRowStretch(2, 1)
        self.layout.setRowStretch(3, 1)
        self.layout.setRowStretch(4, 0)
        self.layout.setRowStretch(5, 0)

        self.roll_plot.setFixedHeight(200)
        self.pitch_plot.setFixedHeight(200)
        self.yaw_plot.setFixedHeight(200)

        self._last_map_lat = None
        self._last_map_lon = None

        self.roll_history = []

        self.pitch_history = []

        self.yaw_history = []

        self.max_history = 100

        self._nav_state = None

        self._trajectory = []

        self._connection_status = "Waiting for connection"

        self._last_refresh = time.time()

        self._frame_count = 0

        self._fps = 0.0

        self._last_packet = -1

        self._throttle_counter = 0

        self._timer = QtCore.QTimer()

        self._timer.timeout.connect(self._refresh)

        self._timer.start(1000 // config.DASHBOARD_REFRESH_RATE)

    def update_navigation_state(self, state, trajectory=None):

        if state is not None:
            pc = getattr(state, 'packet_counter', -1)
            if pc == self._last_packet:
                return
            self._last_packet = pc

        self._nav_state = state

        self._frame_count += 1

        if trajectory is not None:
            self._trajectory = trajectory

        if state is None:
            self._connection_status = "Waiting for MTi-8 data"
        else:
            self._connection_status = f"Connected • Packet {getattr(state, 'packet_counter', '?')}"

    def update_trajectory(self, trajectory):

        self._trajectory = trajectory

    @staticmethod
    def _fmt(value, spec="", default="---"):
        if value is None:
            return default
        try:
            return format(value, spec)
        except (TypeError, ValueError):
            return default

    def _fix_display(self):
        s = self._nav_state
        if s is None:
            return "---"
        rtk = s.rtk_state
        fix = s.fix_type
        diff = s.differential
        if rtk == config.RTK_FIXED:
            return "RTK Fixed"
        elif rtk == config.RTK_FLOAT:
            return "RTK Float"
        elif diff:
            return "DGPS"
        elif fix == 4:
            return "GNSS+DR"
        elif fix == 3:
            return "3D"
        elif fix == 2:
            return "2D"
        elif fix == 1:
            return "DR"
        elif fix == 5:
            return "Time Only"
        else:
            return "No Fix"

    def _has_dashboard_fix(self):
        s = self._nav_state
        return s is not None and s.fix_type is not None and s.fix_type >= config.GNSS_FIX_3D

    def _refresh(self):

        state = self._nav_state

        if state is None:
            self.status_label.setText(self._connection_status)
            self.fps_label.setText("")
            for label in self.status_labels.values():
                label.setText("---")
            self.xy_curve.clear()
            self.roll_curve.clear()
            self.pitch_curve.clear()
            self.yaw_curve.clear()
            return

        now = time.time()
        dt = now - self._last_refresh
        if dt > 0:
            self._fps = self._frame_count / dt
        self._last_refresh = now
        self._frame_count = 0

        self.status_label.setText(self._connection_status)
        self.fps_label.setText(f"FPS: {self._fps:.1f}")

        for key, label in self.status_labels.items():
            if key == "gnss_state":
                label.setText(state.gnss_state or "---")
            elif key == "differential":
                label.setText("YES" if state.differential else "NO")
            elif key == "carrier_state":
                label.setText("Fixed" if state.carrier_state == 2 else ("Float" if state.carrier_state == 1 else "---"))
            elif key == "clock_sync":
                label.setText("SYNCED" if state.clock_sync else "---")
            elif key == "pps":
                label.setText("YES" if state.pps else "NO")
            elif key == "nav_quality":
                q = getattr(state, 'nav_quality', 0)
                label.setText(config.NAVQ_NAMES.get(q, "---"))
                color = {"---": "#888", "BAD": "#f44", "OK": "#ff8", "GOOD": "#4f4", "BEST": "#0ff"}
                label.setStyleSheet(f"font-weight: bold; color: {color.get(config.NAVQ_NAMES.get(q, '---'), '#fff')}")
            elif key == "heading_accuracy":
                val = getattr(state, key, None)
                label.setText("---" if val is not None and val >= 180 else self._fmt(val, ".1f"))
            elif key == "ntrip_state":
                if self._injector is not None:
                    stats = self._injector.statistics()
                    connected = stats.get("ntrip_connected", False)
                    label.setText("Connected" if connected else "Disconnected")
                    color = "#4f4" if connected else "#f44"
                    label.setStyleSheet(f"font-weight: bold; color: {color}")
                else:
                    label.setText("---")
            elif key == "rtcm_age":
                if self._injector is not None:
                    stats = self._injector.statistics()
                    last = stats.get("last_injection", 0)
                    if last > 0:
                        age = time.time() - last
                        label.setText(f"{age:.1f}s")
                        color = "#4f4" if age < 5 else ("#ff8" if age < 15 else "#f44")
                        label.setStyleSheet(f"font-weight: bold; color: {color}")
                    else:
                        label.setText("---")
                else:
                    label.setText("---")
            elif key in ("rtcm_packets", "rtcm_rate", "rtcm_writes"):
                if self._injector is not None:
                    stats = self._injector.statistics()
                    if key == "rtcm_packets":
                        label.setText(str(stats.get("packets", 0)))
                    elif key == "rtcm_rate":
                        label.setText(f"{stats.get('rate', 0):.1f}/s")
                    else:
                        success = stats.get("packets", 0)
                        fails = stats.get("write_failures", 0)
                        label.setText(f"{success}OK/{fails}FAIL")
                else:
                    label.setText("---")
            else:
                value = getattr(state, key, None)
                label.setText(self._fmt(value, '.3f') if isinstance(value, float) else str(value if value is not None else "---"))

        if state.roll is not None:
            self.roll_history.append(state.roll)
        if state.pitch is not None:
            self.pitch_history.append(state.pitch)
        if state.yaw is not None:
            self.yaw_history.append(state.yaw)

        while len(self.roll_history) > self.max_history:
            self.roll_history.pop(0)
            self.pitch_history.pop(0)
            self.yaw_history.pop(0)

        if self.roll_history:
            self.roll_curve.setData(self.roll_history)
            self.pitch_curve.setData(self.pitch_history)
            self.yaw_curve.setData(self.yaw_history)

        traj = self._trajectory

        if traj and len(traj):
            pts = np.array(traj)
            self.xy_curve.setData(pts[:, 0], pts[:, 1])
            self.xy_plot.plotItem.vb.autoRange(padding=0.02)

        lat = getattr(state, 'latitude', None)
        lon = getattr(state, 'longitude', None)
        yaw = getattr(state, 'yaw', None)
        hacc = getattr(state, 'horizontal_accuracy', None)
        if lat is not None and lon is not None:
            if lat != self._last_map_lat or lon != self._last_map_lon:
                self._last_map_lat = lat
                self._last_map_lon = lon
                yaw_val = yaw if yaw is not None else 0
                acc = hacc if hacc is not None else 1
                js = f"updatePosition({lat}, {lon}, {yaw_val}, {acc});"
                self.map_view.page().runJavaScript(js)

    def closeEvent(self, event):

        self._timer.stop()

        super().closeEvent(event)


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    dashboard = Dashboard()

    dashboard.show()

    sys.exit(app.exec_())
