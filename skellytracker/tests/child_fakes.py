"""Targets for the `spawn` children of `verification.spawn_child()` in the tests. A child imports each one by its module name."""

import os
import time


def result_then_hang(key, settings, device_key, connection):
    for step in ("download", "cpu", "ep"):
        connection.send(step)
    connection.send({"ran": True, "ok": True, "reason_code": None})
    time.sleep(300)


def crash_in_the_ep_step(key, settings, device_key, connection):
    connection.send("cpu")
    connection.send("ep")
    os._exit(5)


def crash(*args):
    os._exit(5)


def hang(*args):
    time.sleep(300)


def verify_result_then_hang(job, connection):
    connection.send({"level": "L3", "ok": True, "reason": None, "max_abs_diff": 0.0})
    time.sleep(300)
