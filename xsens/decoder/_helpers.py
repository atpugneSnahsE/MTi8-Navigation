import struct

def f32(data, offset=0):
    return struct.unpack_from(">f", data, offset)[0]

def f64(data, offset=0):
    return struct.unpack_from(">d", data, offset)[0]

def i32(data, offset=0):
    return struct.unpack_from(">i", data, offset)[0]

def u32(data, offset=0):
    return struct.unpack_from(">I", data, offset)[0]

def u16(data, offset=0):
    return struct.unpack_from(">H", data, offset)[0]

def u8(data, offset=0):
    return data[offset]

def fp12_20(data, offset=0):
    return i32(data, offset) / (1 << 20)

def fp16_32(data, offset=0):
    return struct.unpack_from(">q", data, offset)[0] / (1 << 32)

def vec3_f32(data, offset=0):
    return struct.unpack_from(">fff", data, offset)

def vec3_f64(data, offset=0):
    return struct.unpack_from(">ddd", data, offset)

def decode_vector3(field):
    ln = len(field)
    if ln >= 24:
        return vec3_f64(field)
    elif ln >= 12:
        return vec3_f32(field)
    return None

def decode_scalar(field):
    ln = len(field)
    if ln >= 8:
        return f64(field)
    elif ln >= 4:
        return f32(field)
    return None
