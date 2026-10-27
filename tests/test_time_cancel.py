"""time cancel stops a wait/alarm timer and nothing else (task:e0ce873e).

Runs against real processes: a mocked ps could not show that the timer's
command line still matches, or that killpg empties the group.
"""
import os
import subprocess
import time
from datetime import datetime, timedelta

import pytest

from tools import time_tools


def _gone(pid, timeout=2.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        out = subprocess.run(["/bin/ps", "-o", "pid=", "-g", str(pid)],
                             capture_output=True, text=True).stdout
        if not out.strip():
            return True
        time.sleep(0.05)
    return False


def test_cancel_stops_a_running_timer_and_its_group():
    pid = time_tools._schedule("true", datetime.now() + timedelta(hours=1))
    try:
        time.sleep(0.2)  # let sh start its first `sleep 5`, so the group has two members
        assert time_tools.handle_cancel(pid) == f"Timer {pid} cancelled"
        assert _gone(pid)
    finally:
        try:
            os.killpg(pid, 15)
        except ProcessLookupError:
            pass


def test_cancel_of_a_finished_timer_is_a_plain_success():
    pid = time_tools._schedule("true", datetime.now() - timedelta(seconds=1))
    assert _gone(pid)
    assert time_tools.handle_cancel(pid) == f"Timer {pid} already finished"
    # Running it twice, as a repeated cleanup would, stays harmless.
    assert time_tools.handle_cancel(pid) == f"Timer {pid} already finished"


def test_cancel_refuses_a_pid_that_is_not_a_timer():
    child = subprocess.Popen(["sleep", "300"], start_new_session=True)
    try:
        with pytest.raises(ValueError, match="Not a timer"):
            time_tools.handle_cancel(child.pid)
        assert child.poll() is None
    finally:
        child.kill()
        child.wait()


@pytest.mark.parametrize("pid", [0, 1, -5])
def test_cancel_refuses_low_and_negative_pids(pid):
    with pytest.raises(ValueError, match="Not a timer"):
        time_tools.handle_cancel(pid)
