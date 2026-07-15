import struct
from xsens.decoder._helpers import decode_vector3

def decode_delta_v(data_id, field):
    return decode_vector3(field)

def decode_delta_q(data_id, field):
    ln = len(field)
    if ln >= 32:
        return struct.unpack_from(">dddd", field)
    elif ln >= 16:
        return struct.unpack_from(">ffff", field)
    return None
