"""
=========================================================
MTi-8 Navigation System Configuration
Author : Eshan Sengupta
Platform : Ubuntu 22.04+
=========================================================
"""

# ==========================================================
# SERIAL CONFIGURATION
# ==========================================================

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 2000000
SERIAL_TIMEOUT = 0.01

# ==========================================================
# XSENS XBUS
# ==========================================================

PREAMBLE = 0xFA
MID_MTDATA2 = 0x36

# ==========================================================
# XDI BASE MASK
# ==========================================================

XDI_BASE_MASK = 0xFFF0

# ==========================================================
# OUTPUT DATA IDS
# ==========================================================

# Group 0x10xx: Timestamp / Time
XDI_UTC_TIME = 0x1010
XDI_PACKET_COUNTER = 0x1020
XDI_ITOW = 0x1050
XDI_SAMPLE_TIME_FINE = 0x1060
XDI_SAMPLE_TIME_COARSE = 0x10E0

# Group 0x20xx: Orientation
XDI_QUATERNION = 0x2010
XDI_QUATERNION_FLOAT64 = 0x2020
XDI_EULER = 0x2030
XDI_EULER_FLOAT64 = 0x2040

# Group 0x30xx: Pressure / Barometer
XDI_BARO_PRESSURE = 0x3010

# Group 0x40xx: Acceleration
XDI_DELTA_V = 0x4010
XDI_ACCELERATION = 0x4020
XDI_FREE_ACCELERATION = 0x4030
XDI_ACCELERATION_HR = 0x4040

# Group 0x70xx: GNSS
XDI_GNSS_PVT = 0x7010
XDI_GNSS_SATELLITES = 0x7020
XDI_GNSS_DOP = 0x7030

# Group 0x80xx: Angular Velocity
XDI_RATE_OF_TURN = 0x8020
XDI_DELTA_Q = 0x8030
XDI_RATE_OF_TURN_HR = 0x8040

# Group 0x08xx: Temperature
XDI_TEMPERATURE = 0x0810
XDI_TEMPERATURE_LEGACY = 0x9010

# Group 0xC0xx: Magnetic Field
XDI_MAGNETIC_FIELD = 0xC020

# Group 0xE0xx: Status
XDI_STATUS_BYTE = 0xE010
XDI_STATUS_WORD = 0xE020

# ==========================================================
# XDI NAME MAP
# ==========================================================

XDI_NAMES = {
    XDI_UTC_TIME: "UTC Time",
    XDI_PACKET_COUNTER: "Packet Counter",
    XDI_ITOW: "iTOW",
    XDI_SAMPLE_TIME_FINE: "Sample Time Fine",
    XDI_SAMPLE_TIME_COARSE: "Sample Time Coarse",
    XDI_QUATERNION: "Quaternion",
    XDI_QUATERNION_FLOAT64: "Quaternion F64",
    XDI_EULER: "Euler",
    XDI_EULER_FLOAT64: "Euler F64",
    XDI_BARO_PRESSURE: "Baro Pressure",
    XDI_DELTA_V: "Delta V",
    XDI_ACCELERATION: "Acceleration",
    XDI_FREE_ACCELERATION: "Free Acceleration",
    XDI_ACCELERATION_HR: "Acceleration HR",
    XDI_GNSS_PVT: "GNSS PVT",
    XDI_GNSS_SATELLITES: "GNSS Satellites",
    XDI_GNSS_DOP: "GNSS DOP",
    XDI_RATE_OF_TURN: "Rate of Turn",
    XDI_DELTA_Q: "Delta Q",
    XDI_RATE_OF_TURN_HR: "Rate of Turn HR",
    XDI_TEMPERATURE: "Temperature",
    XDI_TEMPERATURE_LEGACY: "Temperature",
    XDI_MAGNETIC_FIELD: "Magnetic Field",
    XDI_STATUS_BYTE: "Status Byte",
    XDI_STATUS_WORD: "Status Word",
}

# ==========================================================
# NTRIP SETTINGS
# ==========================================================

RTK_ENABLED = True

NTRIP_CASTER = "195.182.72.152"
NTRIP_PORT = 2111

NTRIP_MOUNTPOINT = "VRS_RTCM31"

NTRIP_USERNAME = "2976shns"
NTRIP_PASSWORD = "stu9ofro"

# ==========================================================
# INITIAL APPROXIMATE LOCATION
# Used for VRS GGA generation
# ==========================================================

APPROX_LATITUDE = 54.7215335
APPROX_LONGITUDE = 25.3376687
APPROX_ALTITUDE = 202.164

SEND_GGA = True
GGA_INTERVAL = 1.0

# ==========================================================
# FILTER SETTINGS
#
# NOTE: EMA on position/GNSS data destroys RTK accuracy.
# Only apply smoothing to attitude (roll/pitch/yaw) and IMU.
# POSITION_ALPHA = 1.0 means no filtering.
# ==========================================================

ATTITUDE_ALPHA = 0.2
POSITION_ALPHA = 1.0
MEDIAN_WINDOW = 5

# ==========================================================
# CSV LOGGER
# ==========================================================

ENABLE_CSV_LOGGING = True

CSV_FILENAME = "logs/mti8_log.csv"

# ==========================================================
# GUI
# ==========================================================

GUI_UPDATE_RATE = 120

ENABLE_SCENE_VIEWER = False

WINDOW_WIDTH = 2000
WINDOW_HEIGHT = 900

# ==========================================================
# TRAJECTORY
# ==========================================================

MAX_TRAJECTORY_POINTS = 10000

TRAJECTORY_POINT_SIZE = 4

# ==========================================================
# VEHICLE MODEL
# ==========================================================

VEHICLE_SCALE = 0.5

# ==========================================================
# CAMERA
# ==========================================================

CAMERA_DISTANCE = 8.0

CAMERA_ELEVATION = 25

CAMERA_AZIMUTH = 45

# ==========================================================
# COLORS
# ==========================================================

BACKGROUND_COLOR = (0.05, 0.05, 0.05)

TRAJECTORY_COLOR = (0.0, 1.0, 0.0)

VEHICLE_COLOR = (0.85, 0.15, 0.15)

AXIS_LENGTH = 2.0

# ==========================================================
# STATUS WORD BIT DEFINITIONS (XDI 0xE020)
#
# IMPORTANT: The Status Word bit layout is firmware version
# dependent (see MT Low Level Communication Protocol §9.6).
# The positions below are TYPICAL for recent MTi-8 firmware
# but MUST be verified experimentally for your specific unit.
# ==========================================================

STATUS_BIT_RTK_SHIFT = 27
STATUS_BIT_RTK_MASK   = 0x03

STATUS_BIT_ORIENTATION_VALID = 0
STATUS_BIT_GNSS_VALID = 1
STATUS_BIT_NO_GNSS_FIX = 2
STATUS_BIT_FILTER_VALID = 4
STATUS_BIT_CLOCK_SYNC = 10
STATUS_BIT_PPS = 14
STATUS_BIT_SYNC_IN = 18
STATUS_BIT_SYNC_OUT = 19
STATUS_BIT_DIFFERENTIAL = 23
STATUS_BIT_EXTERNAL_GNSS = 24
STATUS_BIT_REPRESENTATIVE_MOTION = 25
STATUS_BIT_CLIPPING = 26

# Typical unverified positions (comment/uncomment after verification):
# STATUS_BIT_ORIENTATION_VALID = 0
# STATUS_BIT_GNSS_VALID        = 1
# STATUS_BIT_NO_GNSS_FIX       = 2
# STATUS_BIT_FILTER_VALID      = 4
# STATUS_BIT_CLOCK_SYNC        = 10
# STATUS_BIT_PPS               = 14
# STATUS_BIT_DIFFERENTIAL      = 23

# ==========================================================
# RTK PHASE STATES (from StatusWord bits 27-28)
# ==========================================================

RTK_PHASE_NONE  = 0
RTK_PHASE_FLOAT = 1
RTK_PHASE_FIXED = 2

RTK_PHASE_NAMES = {
    0: "No Phase",
    1: "Float",
    2: "Fixed",
}

# ==========================================================
# GNSS FIX TYPES (UBX NAV-PVT fixType field)
# ==========================================================

GNSS_FIX_NO_FIX = 0
GNSS_FIX_DEAD_RECKONING = 1
GNSS_FIX_2D = 2
GNSS_FIX_3D = 3
GNSS_FIX_GNSS_DR = 4
GNSS_FIX_TIME_ONLY = 5

GNSS_FIX_NAMES = {
    0: "No Fix",
    1: "Dead Reckoning",
    2: "2D",
    3: "3D",
    4: "GNSS+DR",
    5: "Time Only",
}

# ==========================================================
# GNSS VALIDITY FLAGS (from GNSS PVT valid byte, Table 25)
# ==========================================================

VALID_DATE            = 0x01
VALID_TIME            = 0x02
VALID_FULLY_RESOLVED  = 0x04

# ==========================================================
# GNSS PVT FLAGS (from GNSS PVT flags byte, Table 25)
# ==========================================================

FLAG_VALID_FIX       = 0x01
FLAG_DIFFERENTIAL    = 0x02
FLAG_HEADING_VALID   = 0x20

# ==========================================================
# INVALID / SENTINEL VALUES (defined in UBX protocol)
# ==========================================================

INVALID_DOP = 99.99
INVALID_U32 = 0xFFFFFFFF
INVALID_I32 = 0x7FFFFFFF

# ==========================================================
# NAVIGATION SOLUTION QUALITY
# ==========================================================

NAV_UNKNOWN = 0
NAV_SINGLE  = 1
NAV_DGNSS   = 2
NAV_FLOAT   = 3
NAV_FIXED   = 4

NAV_NAMES = {
    0: "Unknown",
    1: "Single",
    2: "DGNSS",
    3: "RTK Float",
    4: "RTK Fixed",
}

# ==========================================================
# NAVIGATION QUALITY STATES (for dashboard / status output)
# ==========================================================

NAVQ_NONE  = 0
NAVQ_BAD   = 1
NAVQ_OK    = 2
NAVQ_GOOD  = 3
NAVQ_BEST  = 4

NAVQ_NAMES = {
    0: "---",
    1: "BAD",
    2: "OK",
    3: "GOOD",
    4: "BEST",
}

NAVQ_HACC_BAD_THRESH  = 10.0
NAVQ_HACC_GOOD_THRESH = 1.0
NAVQ_HACC_BEST_THRESH = 0.05

NAVQ_HACC_BAD   = 10.0
NAVQ_HACC_GOOD  = 1.0
NAVQ_HACC_BEST  = 0.05

# ==========================================================
# RTK STATUS (from StatusWord bits 27-28)
# ==========================================================

RTK_NONE = 0
RTK_FLOAT = 1
RTK_FIXED = 2

RTK_NAMES = {
    0: "No Fix",
    1: "RTK Float",
    2: "RTK Fixed",
}

# ==========================================================
# DIFFERENTIAL CORRECTIONS (from GNSS PVT flags bit 1)
# ==========================================================

DIFF_SOLUTION_NO = 0
DIFF_SOLUTION_YES = 1

DIFF_NAMES = {
    0: "NO",
    1: "YES",
}

# ==========================================================
# THREAD FREQUENCIES
# ==========================================================

SERIAL_THREAD_RATE = 1000

VISUALIZATION_RATE = 60

RTK_THREAD_RATE = 10

LOGGER_RATE = 50

# ==========================================================
# UPDATE RATES (Hz)
# ==========================================================

DASHBOARD_REFRESH_RATE = 60

SCENE_REFRESH_RATE = 30

# ==========================================================
# PPS / CLOCK SYNC MONITORING
# ==========================================================

PPS_TIMEOUT = 2.0
CLOCKSYNC_TIMEOUT = 30.0

# ==========================================================
# RTCM / CORRECTIONS MONITORING
# ==========================================================

RTCM_TIMEOUT = 10.0
RTCM_PACKET_TIMEOUT = 5.0
MAX_RECONNECT = 5

# ==========================================================
# DEBUG
# ==========================================================

DEBUG_SERIAL = False

DEBUG_PARSER = False

DEBUG_GNSS = False

DEBUG_RTK = False

DEBUG_GUI = False

DEBUG_PERF = False

# ==========================================================
# DATA BUFFER
# ==========================================================

QUEUE_SIZE = 5000

MAX_SERIAL_BUFFER = 65536
