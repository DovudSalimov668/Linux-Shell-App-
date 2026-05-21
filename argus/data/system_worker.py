"""System stats collector using psutil."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import psutil


@dataclass
class SystemSnapshot:
    cpu_percent: float = 0.0
    cpu_per_core: list[float] = field(default_factory=list)
    cpu_freq: float = 0.0
    load_avg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    ram_total: int = 0
    ram_used: int = 0
    ram_percent: float = 0.0
    swap_total: int = 0
    swap_used: int = 0
    swap_percent: float = 0.0
    disk_partitions: list[dict] = field(default_factory=list)
    net_bytes_sent: int = 0
    net_bytes_recv: int = 0
    net_bytes_sent_rate: float = 0.0
    net_bytes_recv_rate: float = 0.0
    temperatures: dict[str, float] = field(default_factory=dict)
    battery_percent: float | None = None
    battery_plugged: bool = False
    uptime: int = 0
    _timestamp: float = field(default_factory=time.monotonic)


async def get_snapshot(prev: SystemSnapshot | None = None) -> SystemSnapshot:
    """Take a psutil snapshot, computing rates if prev provided."""
    snap = SystemSnapshot()
    snap._timestamp = time.monotonic()

    # CPU
    snap.cpu_percent = psutil.cpu_percent(interval=None)
    snap.cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)  # type: ignore[assignment]

    # CPU frequency
    try:
        freq = psutil.cpu_freq()
        snap.cpu_freq = freq.current if freq else 0.0
    except Exception:
        snap.cpu_freq = 0.0

    # Load average
    try:
        snap.load_avg = psutil.getloadavg()  # type: ignore[assignment]
    except AttributeError:
        # Windows doesn't have getloadavg
        snap.load_avg = (0.0, 0.0, 0.0)

    # RAM
    vm = psutil.virtual_memory()
    snap.ram_total = vm.total
    snap.ram_used = vm.used
    snap.ram_percent = vm.percent

    # Swap
    sw = psutil.swap_memory()
    snap.swap_total = sw.total
    snap.swap_used = sw.used
    snap.swap_percent = sw.percent

    # Disk partitions
    partitions = []
    try:
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append(
                    {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent,
                    }
                )
            except (PermissionError, OSError):
                pass
    except Exception:
        pass
    snap.disk_partitions = partitions

    # Network counters
    net = psutil.net_io_counters()
    snap.net_bytes_sent = net.bytes_sent
    snap.net_bytes_recv = net.bytes_recv

    # Compute rates from previous snapshot
    if prev is not None:
        elapsed = snap._timestamp - prev._timestamp
        if elapsed > 0:
            snap.net_bytes_sent_rate = max(
                0.0, (snap.net_bytes_sent - prev.net_bytes_sent) / elapsed
            )
            snap.net_bytes_recv_rate = max(
                0.0, (snap.net_bytes_recv - prev.net_bytes_recv) / elapsed
            )

    # Temperatures
    try:
        temps_raw = psutil.sensors_temperatures()
        if temps_raw:
            for sensor_name, entries in temps_raw.items():
                for entry in entries:
                    key = f"{sensor_name}/{entry.label}" if entry.label else sensor_name
                    snap.temperatures[key] = entry.current
    except (AttributeError, Exception):
        pass

    # Battery
    try:
        batt = psutil.sensors_battery()
        if batt is not None:
            snap.battery_percent = batt.percent
            snap.battery_plugged = batt.power_plugged
    except (AttributeError, Exception):
        snap.battery_percent = None
        snap.battery_plugged = False

    # Uptime
    try:
        snap.uptime = int(time.time() - psutil.boot_time())
    except Exception:
        snap.uptime = 0

    return snap
