# MTi-8 Navigation System

Real-time navigation system for the [Xsens MTi-8](https://www.xsens.com/mti-8) IMU/GNSS sensor. Reads sensor data over serial, decodes the Xsens Xbus/MTData2 binary protocol, fuses GNSS with inertial navigation, and presents everything in a live dashboard.

## Capabilities

- **Full Xsens Xbus/MTData2 protocol decoding** -- quaternion, Euler, acceleration, gyro, magnetic, barometric, temperature, delta-v/q, UTC time, packet counter
- **UBX NAV-PVT GNSS decoding** -- position, velocity, accuracy, DOP, heading, fix type, satellite count, carrier phase
- **RTK correction pipeline** -- NTRIP v2 client + RTCM injection into the MTi-8 serial stream
- **Live PyQt5 dashboard** -- status cards, roll/pitch/yaw strip charts, Leaflet map with position marker and trail
- **Optional Open3D 3D scene** -- vehicle mesh, coordinate frames, trajectory point cloud
- **CSV logging** -- 65+ columns via background thread, zero missed writes
- **Serial auto-detection** -- scans USB ports for Xsens VID, tries all standard baud rates
- **Standalone diagnostic tools** -- baud rate sniffer, packet frequency analyzer, raw GNSS hex dumper

## Architecture

```
MTi-8 Hardware (USB-serial)
       │
  SerialReader (thread)
       │
  XbusParser ──► NavigationState (50+ fields, zero-alloc)
       │
       ├──► IMUParser ──────── attitude, accel, gyro
       ├──► GNSSParser ─────── position, velocity, accuracy
       ├──► GPSStatus ──────── health score, RTK status
       ├──► Dashboard ──────── PyQt5 labels, plots, map
       ├──► CSVLogger ──────── 65+ column CSV
       └──► SceneManager ───── Open3D vehicle + trajectory

NTRIPClient (thread)
       │
  RTCMInjector (thread) ──► MTi-8 serial port
```

**Threading:** SerialReader, NTRIP, RTCMInjector, and CSVLogger each run in their own thread. The Qt main loop handles dashboard redraw at 60 Hz and scene update at 30 Hz.

## Project Structure

```
mti8_navigation/
  main.py                  Entry point
  config.py                All configuration constants

  xsens/                   Sensor protocol layer
    serial_reader.py       Threaded serial reader (auto-detect port/baud)
    xbus_parser.py         Xbus frame parser, updates NavigationState
    navigation_state.py    @dataclass, single source of truth
    quaternion.py          Pure-Python quaternion math
    imu_parser.py          IMU field accessor
    gnss_parser.py         GNSS field accessor
    decoder/               XDI field decoders (one per data type)

  rtk/                     RTK correction pipeline
    ntrip_client.py        NTRIP v2 client
    rtcm_injector.py       Injects RTCM into serial stream
    gps_status.py          GPS/RTK health aggregator

  visualization/           GUI layer
    dashboard.py           PyQt5 main window
    map.html               Leaflet.js map
    scene_manager.py       Open3D 3D scene
    vehicle3d.py           Procedural vehicle mesh
    trajectory.py          ENU trajectory management
    coordinate_frames.py   ECEF/ENU/NED transforms

  logger/
    csv_logger.py          Threaded CSV writer

  logs/
    mti8_log.csv           Sample log output
```

## Setup

```bash
# Install dependencies
pip install pyserial PyQt5 pyqtgraph numpy open3d

# Add user to dialout group (Linux)
sudo usermod -aG dialout $USER
# Log out and back in for group to take effect

# Connect MTi-8 via USB, then run
python main.py
```

## Configuration

All settings live in `config.py`. Key sections:

| Section | Defaults |
|---|---|
| Serial | `/dev/ttyUSB0` @ 2M baud (auto-detected) |
| NTRIP | Caster `195.182.72.152:2111`, mountpoint `VRS_RTCM31` |
| Approx. Location | 54.7215N, 25.3377E, alt 202m |
| Filters | Attitude EMA alpha=0.2, median window=5 |
| GUI | 2000x900, 60Hz refresh, 30Hz scene |
| Debug | Off by default -- enable per subsystem |

## Diagnostic Tools

Standalone scripts for hardware debugging (no GUI needed):

```bash
# Auto-detect baud rate by counting valid frames
python sniffer.py

# Show per-XDI packet frequency and estimated Hz
python packet_analyser.py

# Raw hex dump of GNSS PVT and Status Word fields
python dump_gnss_pvt.py
```

## Requirements

- Xsens MTi-8 connected via USB-to-serial adapter
- Python 3.7+
- MTi-8 configured to output MTData2 with quaternion, GNSS PVT, and status word XDI fields
