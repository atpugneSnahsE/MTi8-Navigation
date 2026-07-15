from xsens.decoder._helpers import decode_vector3, decode_scalar

def decode_acceleration(data_id, field):
    return decode_vector3(field)

def decode_free_acceleration(data_id, field):
    return decode_vector3(field)

def decode_gyro(data_id, field):
    return decode_vector3(field)

def decode_gyro_hr(data_id, field):
    return decode_vector3(field)

def decode_magnetic(data_id, field):
    return decode_vector3(field)

def decode_temperature(data_id, field):
    return decode_scalar(field)
