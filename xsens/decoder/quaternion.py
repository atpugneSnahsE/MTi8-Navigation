import struct
from xsens.quaternion import Quaternion

def decode_quaternion(data_id, field):
    ln = len(field)
    if ln >= 32:
        w, x, y, z = struct.unpack_from(">dddd", field)
    elif ln >= 16:
        w, x, y, z = struct.unpack_from(">ffff", field)
    else:
        return None
    return Quaternion(w, x, y, z).normalize()
