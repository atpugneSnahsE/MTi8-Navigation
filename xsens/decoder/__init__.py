from xsens.decoder.quaternion import decode_quaternion
from xsens.decoder.gnss_pvt import decode_gnss_pvt
from xsens.decoder.imu import (decode_acceleration, decode_free_acceleration,
                                decode_gyro, decode_gyro_hr, decode_magnetic,
                                decode_temperature)
from xsens.decoder.status import decode_status_word, decode_status_byte
from xsens.decoder.pressure import decode_pressure
from xsens.decoder.delta import decode_delta_v, decode_delta_q
from xsens.decoder.utc import decode_utc_time, decode_packet_counter, decode_sample_time


def decode_satellites(data_id, field):
    from xsens.decoder._helpers import u8
    if len(field) < 1:
        return None
    return u8(field)

import config

_DECODER_MAP = {
    config.XDI_UTC_TIME: decode_utc_time,
    config.XDI_PACKET_COUNTER: decode_packet_counter,
    0x1050: decode_sample_time,
    config.XDI_SAMPLE_TIME_FINE: decode_sample_time,
    config.XDI_SAMPLE_TIME_COARSE: decode_sample_time,

    config.XDI_QUATERNION: decode_quaternion,
    0x2020: decode_quaternion,

    config.XDI_BARO_PRESSURE: decode_pressure,

    config.XDI_DELTA_V: decode_delta_v,
    config.XDI_ACCELERATION: decode_acceleration,
    config.XDI_FREE_ACCELERATION: decode_free_acceleration,
    config.XDI_ACCELERATION_HR: decode_acceleration,

    config.XDI_GNSS_PVT: decode_gnss_pvt,
    config.XDI_GNSS_SATELLITES: decode_satellites,

    config.XDI_RATE_OF_TURN: decode_gyro,
    config.XDI_DELTA_Q: decode_delta_q,
    config.XDI_RATE_OF_TURN_HR: decode_gyro_hr,

    config.XDI_TEMPERATURE: decode_temperature,
    config.XDI_TEMPERATURE_LEGACY: decode_temperature,

    config.XDI_MAGNETIC_FIELD: decode_magnetic,

    config.XDI_STATUS_BYTE: decode_status_byte,
    config.XDI_STATUS_WORD: decode_status_word,
}

def decoder_for(data_id):
    dec = _DECODER_MAP.get(data_id)
    if dec is not None:
        return dec
    return _DECODER_MAP.get(data_id & config.XDI_BASE_MASK)

def all_decoders():
    return dict(_DECODER_MAP)
