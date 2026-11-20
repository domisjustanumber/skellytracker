"""Targets for the `spawn` children of `verification.spawn_child()` in the tests. A child imports each one by its module name."""

import os
import time


def crash(*args):
    os._exit(5)


def hang(*args):
    time.sleep(300)


def verify_result_then_hang(job, connection):
    connection.send({"level": "L3", "ok": True, "reason": None, "max_abs_diff": 0.0})
    time.sleep(300)
