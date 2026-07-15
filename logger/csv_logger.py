import csv
import os
import queue
import threading
import time

import config


class CSVLogger(threading.Thread):

    def __init__(self):

        super().__init__(daemon=True)

        self.file = None
        self.writer = None

        self.running = False

        self.rows_written = 0

        self.filename = config.CSV_FILENAME

        self._queue = queue.Queue(maxsize=config.QUEUE_SIZE)

        self._sentinel = None

        self.create_file()

    def create_file(self):

        directory = os.path.dirname(self.filename)

        if directory != "":
            os.makedirs(directory, exist_ok=True)

        self.file = open(self.filename, "w", newline="")

        self.writer = csv.writer(self.file)

        self.writer.writerow([
            "SystemTime",
            "UTC",
            "Packet",
            "SampleTime",
            "Roll", "Pitch", "Yaw",
            "Qw", "Qx", "Qy", "Qz",
            "AccX", "AccY", "AccZ",
            "FreeAccX", "FreeAccY", "FreeAccZ",
            "DeltaVX", "DeltaVY", "DeltaVZ",
            "GyroX", "GyroY", "GyroZ",
            "DeltaQ0", "DeltaQ1", "DeltaQ2", "DeltaQ3",
            "MagX", "MagY", "MagZ",
            "Pressure", "Temperature",
            "Latitude", "Longitude", "Altitude", "HeightMSL",
            "VelN", "VelE", "VelD",
            "GroundSpeed", "HeadingMotion", "HeadingVehicle",
            "HorizAccuracy", "VertAccuracy", "SpeedAccuracy", "HeadingAccuracy",
            "Satellites", "FixType",
            "Flags", "ValidFlags",
            "GDOP", "PDOP", "TDOP", "VDOP", "HDOP", "NDOP", "EDOP",
            "StatusWord", "StatusByte",
            "RTKState", "CarrierState",
            "Differential", "ClockSync",
            "FilterValid", "GNSSValid",
            "NavQuality",
        ])

        self.file.flush()

    def log(self, state, parser):
        s = state
        q = s.quaternion

        row = [
            time.time(),
            s.utc,
            s.packet_counter,
            s.sample_time,
            s.roll, s.pitch, s.yaw,
            q.w if q else None, q.x if q else None,
            q.y if q else None, q.z if q else None,
            *(s.acceleration if s.acceleration else (None, None, None)),
            *(s.free_acceleration if s.free_acceleration else (None, None, None)),
            *(s.delta_v if s.delta_v else (None, None, None)),
            *(s.gyro if s.gyro else (None, None, None)),
            *(s.delta_q if s.delta_q else (None, None, None, None)),
            *(s.magnetic if s.magnetic else (None, None, None)),
            s.pressure,
            s.temperature,
            s.latitude,
            s.longitude,
            s.altitude,
            s.height_msl,
            s.velocity_n,
            s.velocity_e,
            s.velocity_d,
            s.ground_speed,
            s.heading_motion,
            s.heading_vehicle,
            s.horizontal_accuracy,
            s.vertical_accuracy,
            s.speed_accuracy,
            s.heading_accuracy,
            s.num_sv,
            s.fix_type,
            s.flags,
            s.valid_flags,
            s.gdop, s.pdop, s.tdop, s.vdop, s.hdop, s.ndop, s.edop,
            s.status_word,
            s.status_byte,
            s.rtk_state,
            s.carrier_state,
            s.differential,
            s.clock_sync,
            s.filter_valid,
            s.gnss_valid,
            s.nav_quality,
        ]

        try:
            self._queue.put_nowait(row)
        except queue.Full:
            if config.DEBUG_GUI:
                print("[CSVLogger] Queue full, dropping row")

    def _write_row(self, row):

        self.writer.writerow(row)

        self.rows_written += 1

    def flush(self):

        if self.file is not None:
            self.file.flush()

    def close(self):

        self.flush()

        if self.file is not None:
            self.file.close()

    def run(self):

        self.running = True

        last_flush = time.time()

        while self.running:

            try:
                row = self._queue.get(timeout=0.1)
                if row is self._sentinel:
                    break
                self._write_row(row)
                now = time.time()
                if now - last_flush >= 1.0:
                    self.flush()
                    last_flush = now
            except queue.Empty:
                pass

        self.flush()

    def stop(self):

        self.running = False

        self._queue.put(self._sentinel)

    def statistics(self):

        return {
            "rows": self.rows_written,
            "filename": self.filename,
            "queue_size": self._queue.qsize()
        }

    def print_statistics(self):

        stats = self.statistics()

        print()
        print("=" * 60)
        print("CSV LOGGER")
        print("=" * 60)
        print("File :", stats["filename"])
        print("Rows :", stats["rows"])
        print("=" * 60)

    def __repr__(self):

        return f"CSVLogger({self.rows_written} rows)"


if __name__ == "__main__":

    logger = CSVLogger()

    logger.start()

    print("CSV Logger initialized.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.stop()
        logger.print_statistics()
