from dataclasses import dataclass, field
from typing import Dict

from xsens.decoder._helpers import u8, u32
import config


STATUS_WORD_BITS = {
    "orientation_valid": 0,
    "gnss_valid": 1,
    "no_gnss_fix": 2,
    "filter_valid": 4,
    "clock_sync": 10,
    "pps": 14,
    "sync_in": 18,
    "sync_out": 19,
    "differential": 23,
    "external_gnss": 24,
    "representative_motion": 25,
    "clipping": 26,
}


@dataclass
class StatusWord:
    raw: int
    raw_hex: str
    raw_binary: str
    firmware_profile: str = "mti_8_typical"
    bits: Dict[str, bool] = field(default_factory=dict)
    rtk_phase: int = 0
    rtk_float: bool = False
    rtk_fixed: bool = False

    def __int__(self):
        return self.raw

    def __index__(self):
        return self.raw

    def __and__(self, other):
        return self.raw & other

    def __rshift__(self, other):
        return self.raw >> other

    def get(self, name, default=False):
        return self.bits.get(name, default)

def decode_status_byte(data_id, field):
    if len(field) < 1:
        return None
    return u8(field)

def decode_status_word(data_id, field):
    if len(field) < 4:
        return None
    raw = u32(field)
    rtk_phase = (raw >> config.STATUS_BIT_RTK_SHIFT) & config.STATUS_BIT_RTK_MASK
    return StatusWord(
        raw=raw,
        raw_hex=f"0x{raw:08X}",
        raw_binary=f"{raw:032b}",
        bits={name: bool(raw & (1 << bit)) for name, bit in STATUS_WORD_BITS.items()},
        rtk_phase=rtk_phase,
        rtk_float=rtk_phase == 1,
        rtk_fixed=rtk_phase == 2,
    )
