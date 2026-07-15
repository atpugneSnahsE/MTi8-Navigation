import struct
from xsens.decoder._helpers import u32, u16, u8

def decode_utc_time(data_id, field):
    if len(field) < 12:
        return None
    ns, year, month, day, hour, minute, second, flags = \
        struct.unpack_from(">IHBBBBBB", field)
    if not (2000 <= year <= 2100) or not (1 <= month <= 12) or not (1 <= day <= 31):
        return None
    return (
        f"{year:04d}-{month:02d}-{day:02d} "
        f"{hour:02d}:{minute:02d}:{second:02d}.{ns // 1000000:03d}"
    )

def decode_packet_counter(data_id, field):
    if len(field) >= 2:
        return u16(field)
    return None

def decode_sample_time(data_id, field):
    if len(field) >= 4:
        return u32(field)
    return None
