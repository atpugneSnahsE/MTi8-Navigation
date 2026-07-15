from xsens.decoder._helpers import decode_scalar

def decode_pressure(data_id, field):
    return decode_scalar(field)
