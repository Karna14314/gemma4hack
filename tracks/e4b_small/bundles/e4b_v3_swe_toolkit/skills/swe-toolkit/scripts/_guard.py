"""Bounded execution helpers for the swe-toolkit scripts.

Every operation in `swe.py` is wrapped so that a slow repository cannot burn the
agent's whole tool budget. Two layers:

* `deadline_after` / `expired` give the callers a cooperative budget. `locate`
  checks it between files and returns a partial ranking instead of nothing.
* `run` is the hard backstop. It runs the work in a daemon thread and gives up
  after `seconds`, so a pathological input can never hang the process.

The important property is that a timeout still produces a report. A
`STATUS: DEGRADED` line with no body is a wasted tool call, which is exactly
what this module exists to prevent.
"""

from __future__ import annotations

import threading
import time


def deadline_after(seconds: float) -> float:
    """Return a `time.monotonic()` deadline `seconds` from now."""
    return time.monotonic() + float(seconds)


def expired(deadline: float | None) -> bool:
    """True when `deadline` has passed. `None` never expires."""
    return deadline is not None and time.monotonic() > deadline


def remaining(deadline: float | None) -> float | None:
    """Seconds left before `deadline`, or `None` when unbounded."""
    if deadline is None:
        return None
    return max(0.0, deadline - time.monotonic())


def run(seconds: float, fn, *args, **kwargs):
    """Run `fn(*args, **kwargs)` with a hard `seconds` limit.

    Returns `(value, error)`. On timeout returns `(None, TimeoutError)` and
    leaves the worker thread to die with the process.
    """
    box: dict[str, object] = {"value": None, "error": None}

    def worker() -> None:
        try:
            box["value"] = fn(*args, **kwargs)
        except BaseException as exc:  # noqa: BLE001 - reported to the caller
            box["error"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(float(seconds))
    if thread.is_alive():
        return None, TimeoutError("watchdog")
    if box["error"] is not None:
        return None, box["error"]
    return box["value"], None
