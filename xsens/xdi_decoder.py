"""
XDI (Xsens Data Identifier) Decoder Registry

Re-exports decoders from the xsens.decoder package for
backward compatibility.

Each decoder has signature:
    decode(data_id: int, field: bytes) -> object
"""

from xsens.decoder import decoder_for, all_decoders
from xsens.decoder.quaternion import decode_quaternion
from xsens.decoder.gnss_pvt import decode_gnss_pvt
from xsens.decoder.imu import (decode_acceleration, decode_free_acceleration,
                                decode_gyro, decode_gyro_hr, decode_magnetic,
                                decode_temperature)
from xsens.decoder.status import decode_status_word, decode_status_byte
from xsens.decoder.pressure import decode_pressure
from xsens.decoder.delta import decode_delta_v, decode_delta_q
from xsens.decoder.utc import decode_utc_time, decode_packet_counter, decode_sample_time

from xsens.decoder._helpers import (f32, f64, i32, u32, u16, u8,
                                     fp12_20, fp16_32,
                                     vec3_f32, vec3_f64,
                                     decode_vector3, decode_scalar)
