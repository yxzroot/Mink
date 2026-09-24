"""Lightweight system status helpers used by the optional status bar."""

from dataclasses import dataclass
import os
import socket
import time


@dataclass(frozen=True)
class SystemStatus:
    hostname: str
    uptime: str
    cpu: str
    memory: str


def _duration(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m {seconds:02d}s"


def _memory() -> str:
    try:
        values = {}
        with open("/proc/meminfo", encoding="ascii") as stream:
            for line in stream:
                key, value = line.split(":", 1)
                values[key] = int(value.split()[0])
        total = values["MemTotal"]
        available = values.get("MemAvailable", values.get("MemFree", total))
        used = max(0, total - available)
        return f"RAM {used * 100 // total}%"
    except (OSError, KeyError, ValueError, ZeroDivisionError):
        return "RAM n/a"


def _cpu() -> str:
    try:
        with open("/proc/loadavg", encoding="ascii") as stream:
            load = float(stream.read().split()[0])
        return f"CPU {load:.1f}"
    except (OSError, ValueError, IndexError):
        return "CPU n/a"


def read_status(started: float) -> SystemStatus:
    return SystemStatus(
        hostname=socket.gethostname().split(".", 1)[0],
        uptime=_duration(time.monotonic() - started),
        cpu=_cpu(),
        memory=_memory(),
    )
