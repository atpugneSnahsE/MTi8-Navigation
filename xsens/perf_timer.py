"""
Per-thread performance timer.

Usage:
    from xsens.perf_timer import PerfTimer

    with PerfTimer("parse"):
        parse(frame)

Prints elapsed time if config.DEBUG_PERF is True.
"""

import time
import threading

import config


class PerfTimer:
    _tls = threading.local()

    def __init__(self, label, enabled=None):
        self.label = label
        self.enabled = enabled if enabled is not None else config.DEBUG_PERF

    def __enter__(self):
        if self.enabled:
            self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        if self.enabled:
            elapsed = time.perf_counter() - self.start
            tid = threading.get_ident()
            print(f"[PERF][{tid:#x}] {self.label}: {elapsed*1000:.1f} ms")
