"""SysInfoScreen — full hardware and OS deep-dive with tabbed detail panels."""

from __future__ import annotations

import asyncio
import os
import platform
import re
import socket
import subprocess
import time
from pathlib import Path

import psutil

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Label, Static, TabbedContent, TabPane


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run(cmd: list[str], timeout: int = 5) -> str:
    """Run a shell command, return stdout or '' on failure."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _read(path: str) -> str:
    """Read a /proc or /sys file, return '' on failure."""
    try:
        return Path(path).read_text(errors="replace").strip()
    except Exception:
        return ""


def _fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024.0
    return f"{n:.1f} PB"


# ── Data collectors ───────────────────────────────────────────────────────────

def _collect_overview() -> list[str]:
    lines: list[str] = []

    # ── OS ────────────────────────────────────────────────────────────────────
    os_name = ""
    os_version = ""
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("PRETTY_NAME="):
                os_name = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("VERSION_ID="):
                os_version = line.split("=", 1)[1].strip().strip('"')
    except Exception:
        os_name = platform.system()

    lines += [
        "[bold cyan]  System Overview[/bold cyan]",
        "",
        f"[bold]Hostname     :[/]  [cyan]{socket.gethostname()}[/]",
        f"[bold]OS           :[/]  {os_name}",
        f"[bold]Kernel       :[/]  {platform.release()}",
        f"[bold]Architecture :[/]  {platform.machine()}",
        f"[bold]Python       :[/]  {platform.python_version()}",
    ]

    # ── Uptime ────────────────────────────────────────────────────────────────
    try:
        boot_ts = psutil.boot_time()
        uptime_s = int(time.time() - boot_ts)
        d = uptime_s // 86400
        h = (uptime_s % 86400) // 3600
        m = (uptime_s % 3600) // 60
        s = uptime_s % 60
        boot_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(boot_ts))
        lines += [
            f"[bold]Uptime       :[/]  [green]{d}d {h}h {m}m {s}s[/]",
            f"[bold]Boot time    :[/]  [dim]{boot_str}[/]",
        ]
    except Exception:
        pass

    # ── Shell / terminal ──────────────────────────────────────────────────────
    shell = os.environ.get("SHELL", "unknown")
    term = os.environ.get("TERM", "unknown")
    lines += [
        f"[bold]Shell        :[/]  {shell}",
        f"[bold]Terminal     :[/]  {term}",
    ]

    # ── Load average ──────────────────────────────────────────────────────────
    try:
        la = psutil.getloadavg()
        lines += [
            "",
            "[bold cyan]  Load Average[/bold cyan]",
            f"  1 min  : [green]{la[0]:.2f}[/]",
            f"  5 min  : [yellow]{la[1]:.2f}[/]",
            f"  15 min : [red]{la[2]:.2f}[/]",
        ]
    except Exception:
        pass

    # ── Logged-in users ───────────────────────────────────────────────────────
    try:
        users = psutil.users()
        if users:
            lines += ["", "[bold cyan]  Logged-in Users[/bold cyan]"]
            for u in users:
                started = time.strftime("%H:%M", time.localtime(u.started))
                lines.append(
                    f"  [cyan]{u.name:<12}[/]  tty:{u.terminal or '?':<8}  since {started}"
                )
        else:
            lines += ["", "[bold cyan]  Logged-in Users[/bold cyan]", "  [dim]none[/]"]
    except Exception:
        pass

    # ── CPU quick summary ─────────────────────────────────────────────────────
    try:
        cpu_pct = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        cores = psutil.cpu_count(logical=True)
        lines += [
            "",
            "[bold cyan]  Live Snapshot[/bold cyan]",
            f"  CPU Usage    : [bold]{cpu_pct:.1f}%[/]  ({cores} logical cores)",
            f"  RAM Usage    : [bold]{vm.percent:.1f}%[/]  "
            f"({_fmt_bytes(vm.used)} / {_fmt_bytes(vm.total)})",
        ]
        sw = psutil.swap_memory()
        if sw.total:
            lines.append(
                f"  Swap Usage   : [bold]{sw.percent:.1f}%[/]  "
                f"({_fmt_bytes(sw.used)} / {_fmt_bytes(sw.total)})"
            )
    except Exception:
        pass

    return lines


def _collect_cpu() -> list[str]:
    lines: list[str] = ["[bold cyan]  CPU Details[/bold cyan]", ""]

    # /proc/cpuinfo
    model = ""
    vendor = ""
    cache_size = ""
    flags: list[str] = []
    stepping = ""
    family = ""
    cpu_mhz = ""

    try:
        cpuinfo = Path("/proc/cpuinfo").read_text()
        for line in cpuinfo.splitlines():
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if k == "model name" and not model:
                model = v
            elif k == "vendor_id" and not vendor:
                vendor = v
            elif k == "cache size" and not cache_size:
                cache_size = v
            elif k == "flags" and not flags:
                flags = v.split()
            elif k == "stepping" and not stepping:
                stepping = v
            elif k == "cpu family" and not family:
                family = v
            elif k == "cpu MHz" and not cpu_mhz:
                cpu_mhz = v
    except Exception:
        pass

    if model:
        lines.append(f"[bold]Model        :[/]  [yellow]{model}[/]")
    if vendor:
        lines.append(f"[bold]Vendor       :[/]  {vendor}")

    # psutil counts
    try:
        logical = psutil.cpu_count(logical=True) or 0
        physical = psutil.cpu_count(logical=False) or 0
        lines += [
            f"[bold]Physical     :[/]  {physical} cores",
            f"[bold]Logical      :[/]  {logical} threads",
        ]
    except Exception:
        pass

    if cache_size:
        lines.append(f"[bold]Cache        :[/]  {cache_size}")
    if family:
        lines.append(f"[bold]Family       :[/]  {family}  Stepping: {stepping}")

    # Frequency
    try:
        freq = psutil.cpu_freq()
        if freq:
            lines += [
                "",
                "[bold cyan]  Frequency[/bold cyan]",
                f"  Current : [green]{freq.current:.0f} MHz[/]  ({freq.current/1000:.2f} GHz)",
                f"  Min     : {freq.min:.0f} MHz",
                f"  Max     : {freq.max:.0f} MHz",
            ]
        elif cpu_mhz:
            lines += ["", f"[bold]Frequency    :[/]  {float(cpu_mhz):.0f} MHz"]
    except Exception:
        pass

    # Per-core usage
    try:
        per_core: list[float] = psutil.cpu_percent(interval=None, percpu=True)  # type: ignore[assignment]
        lines += ["", "[bold cyan]  Per-Core Usage[/bold cyan]"]
        for i, pct in enumerate(per_core):
            bar_w = 20
            filled = int(pct / 100 * bar_w)
            colour = "green" if pct < 60 else ("yellow" if pct < 85 else "red")
            bar = f"[{colour}]{'█' * filled}[/][dim]{'░' * (bar_w - filled)}[/]"
            lines.append(f"  Core {i:>2}  {bar} [{colour}]{pct:5.1f}%[/]")
    except Exception:
        pass

    # Notable flags
    notable = {
        "sse4_2": "SSE 4.2", "avx": "AVX", "avx2": "AVX2", "avx512f": "AVX-512",
        "aes": "AES-NI", "vmx": "Intel VT-x", "svm": "AMD-V",
        "hypervisor": "Hypervisor", "ht": "Hyper-Threading",
        "lm": "64-bit", "nx": "NX/XD bit", "rdrand": "RDRAND",
    }
    found = [label for flag, label in notable.items() if flag in flags]
    if found:
        lines += ["", "[bold cyan]  CPU Features[/bold cyan]", "  " + "  ".join(f"[cyan]{f}[/]" for f in found)]

    if flags:
        lines += [
            "",
            "[bold cyan]  All Flags[/bold cyan]",
            "  [dim]" + "  ".join(flags[:60]) + ("[/]\n  [dim]…" if len(flags) > 60 else "[/]"),
        ]

    return lines


def _collect_memory() -> list[str]:
    lines: list[str] = ["[bold cyan]  Memory Details[/bold cyan]", ""]

    # psutil virtual memory
    try:
        vm = psutil.virtual_memory()
        total = vm.total
        lines += [
            f"[bold]Total        :[/]  [cyan]{_fmt_bytes(total)}[/]",
            f"[bold]Available    :[/]  [green]{_fmt_bytes(vm.available)}[/]",
            f"[bold]Used         :[/]  {_fmt_bytes(vm.used)}  ({vm.percent:.1f}%)",
            f"[bold]Free         :[/]  {_fmt_bytes(vm.free)}",
        ]
        if hasattr(vm, "buffers"):
            lines.append(f"[bold]Buffers      :[/]  [dim]{_fmt_bytes(vm.buffers)}[/]")
        if hasattr(vm, "cached"):
            lines.append(f"[bold]Cached       :[/]  [dim]{_fmt_bytes(vm.cached)}[/]")
        if hasattr(vm, "shared"):
            lines.append(f"[bold]Shared       :[/]  [dim]{_fmt_bytes(vm.shared)}[/]")
    except Exception:
        pass

    # Swap
    try:
        sw = psutil.swap_memory()
        lines += [
            "",
            "[bold cyan]  Swap[/bold cyan]",
            f"[bold]Total        :[/]  {_fmt_bytes(sw.total)}",
            f"[bold]Used         :[/]  {_fmt_bytes(sw.used)}  ({sw.percent:.1f}%)",
            f"[bold]Free         :[/]  {_fmt_bytes(sw.free)}",
        ]
    except Exception:
        pass

    # /proc/meminfo for extra detail
    try:
        meminfo: dict[str, str] = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, _, v = line.partition(":")
            meminfo[k.strip()] = v.strip()

        extra_keys = [
            ("Dirty", "Dirty pages"), ("Writeback", "Writeback"),
            ("AnonPages", "Anonymous pages"), ("Mapped", "Mapped"),
            ("Shmem", "Shared memory"), ("Slab", "Kernel slab"),
            ("VmallocTotal", "Vmalloc total"), ("VmallocUsed", "Vmalloc used"),
            ("HugePages_Total", "HugePages total"), ("HugePages_Free", "HugePages free"),
        ]
        detail_lines = []
        for k, label in extra_keys:
            if k in meminfo:
                detail_lines.append(f"  {label:<20}  [dim]{meminfo[k]}[/]")
        if detail_lines:
            lines += ["", "[bold cyan]  /proc/meminfo Extras[/bold cyan]"] + detail_lines
    except Exception:
        pass

    # Top 10 memory consumers
    try:
        procs = []
        for p in psutil.process_iter(["pid", "name", "memory_info", "memory_percent"]):
            try:
                info = p.info
                procs.append(info)
            except Exception:
                pass
        procs.sort(key=lambda x: x.get("memory_percent") or 0, reverse=True)
        lines += ["", "[bold cyan]  Top Memory Consumers[/bold cyan]"]
        for p in procs[:10]:
            mem_mb = (p.get("memory_info") or type("", (), {"rss": 0})()).rss / 1024 / 1024
            pct = p.get("memory_percent") or 0
            name = (p.get("name") or "")[:25]
            colour = "red" if pct > 10 else ("yellow" if pct > 5 else "green")
            lines.append(
                f"  [{colour}]{pct:5.1f}%[/]  {_fmt_bytes(mem_mb * 1024 * 1024):<10}  {name}"
            )
    except Exception:
        pass

    return lines


def _collect_storage() -> list[str]:
    lines: list[str] = ["[bold cyan]  Storage[/bold cyan]", ""]

    try:
        parts = psutil.disk_partitions(all=False)
        for p in parts:
            try:
                usage = psutil.disk_usage(p.mountpoint)
            except (PermissionError, OSError):
                continue
            pct = usage.percent
            colour = "green" if pct < 70 else ("yellow" if pct < 90 else "red")
            bar_w = 22
            filled = int(pct / 100 * bar_w)
            bar = f"[{colour}]{'█' * filled}[/][dim]{'░' * (bar_w - filled)}[/]"
            lines += [
                f"[bold]{p.mountpoint}[/]  [dim]{p.fstype}[/]  [dim]{p.device}[/]",
                f"  {bar} [{colour}]{pct:.1f}%[/]",
                f"  Used: [cyan]{_fmt_bytes(usage.used)}[/]  "
                f"Free: [green]{_fmt_bytes(usage.free)}[/]  "
                f"Total: {_fmt_bytes(usage.total)}",
                "",
            ]
    except Exception:
        pass

    # I/O stats per disk
    try:
        io_all = psutil.disk_io_counters(perdisk=True)
        if io_all:
            lines += ["[bold cyan]  Disk I/O Counters[/bold cyan]"]
            for disk, io in list(io_all.items())[:8]:
                lines += [
                    f"  [cyan]{disk}[/]",
                    f"    Read : {_fmt_bytes(io.read_bytes)}  ({io.read_count:,} ops)",
                    f"    Write: {_fmt_bytes(io.write_bytes)}  ({io.write_count:,} ops)",
                ]
    except Exception:
        pass

    # /proc/partitions
    try:
        raw = Path("/proc/partitions").read_text()
        lines += ["", "[bold cyan]  /proc/partitions[/bold cyan]"]
        for line in raw.splitlines()[2:]:
            parts_raw = line.split()
            if len(parts_raw) == 4:
                _, _, blocks, name = parts_raw
                size_mb = int(blocks) / 1024
                if size_mb >= 1:
                    lines.append(
                        f"  [cyan]{name:<12}[/]  {size_mb / 1024:.1f} GB" if size_mb >= 1024
                        else f"  [cyan]{name:<12}[/]  {size_mb:.0f} MB"
                    )
    except Exception:
        pass

    return lines


def _collect_network() -> list[str]:
    lines: list[str] = ["[bold cyan]  Network Interfaces[/bold cyan]", ""]

    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        io = psutil.net_io_counters(pernic=True)

        for iface in sorted(addrs.keys()):
            s = stats.get(iface)
            is_up = s.isup if s else False
            speed = f"{s.speed} Mbps" if s and s.speed else "?"
            mtu = str(s.mtu) if s else "?"
            status = "[green]UP[/]" if is_up else "[red]DOWN[/]"

            lines.append(f"[bold cyan]{iface}[/]  {status}  speed={speed}  MTU={mtu}")

            for addr in addrs[iface]:
                import socket as _socket
                if addr.family == _socket.AF_INET:
                    lines.append(f"  IPv4  : [green]{addr.address}[/]  mask={addr.netmask}")
                elif addr.family == _socket.AF_INET6:
                    lines.append(f"  IPv6  : [cyan]{addr.address}[/]")
                elif addr.family == _socket.AF_PACKET if hasattr(_socket, "AF_PACKET") else -1:  # type: ignore[attr-defined]
                    lines.append(f"  MAC   : [dim]{addr.address}[/]")

            if iface in io:
                nic_io = io[iface]
                lines += [
                    f"  Sent  : {_fmt_bytes(nic_io.bytes_sent)}  "
                    f"({nic_io.packets_sent:,} pkts  errs={nic_io.errout}  drop={nic_io.dropout})",
                    f"  Recv  : {_fmt_bytes(nic_io.bytes_recv)}  "
                    f"({nic_io.packets_recv:,} pkts  errs={nic_io.errin}  drop={nic_io.dropin})",
                ]
            lines.append("")
    except Exception as exc:
        lines.append(f"[red]{exc}[/]")

    # Active connections count
    try:
        conns = psutil.net_connections()
        est = sum(1 for c in conns if c.status == "ESTABLISHED")
        listen = sum(1 for c in conns if c.status == "LISTEN")
        lines += [
            "[bold cyan]  Connections[/bold cyan]",
            f"  Established : [green]{est}[/]",
            f"  Listening   : [cyan]{listen}[/]",
            f"  Total       : {len(conns)}",
        ]
    except Exception:
        pass

    return lines


def _collect_sensors() -> list[str]:
    lines: list[str] = ["[bold cyan]  Hardware Sensors[/bold cyan]", ""]

    # Temperatures
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            lines.append("[bold]Temperatures[/bold]")
            for sensor, entries in temps.items():
                lines.append(f"  [cyan]{sensor}[/]")
                for e in entries:
                    label = e.label or "—"
                    t = e.current
                    high = e.high or 0
                    colour = "green" if t < 60 else ("yellow" if t < 80 else "red")
                    bar = f"[{colour}]{t:.1f}°C[/]"
                    crit_str = f"  [dim](high={e.high}°C  crit={e.critical}°C)[/]" if e.high else ""
                    lines.append(f"    {label:<20}  {bar}{crit_str}")
        else:
            lines.append("[dim]No temperature sensors found[/]")
    except Exception:
        lines.append("[dim]Temperature sensors unavailable[/]")

    # Fans
    try:
        fans = psutil.sensors_fans()
        if fans:
            lines += ["", "[bold]Fans[/bold]"]
            for sensor, entries in fans.items():
                lines.append(f"  [cyan]{sensor}[/]")
                for e in entries:
                    label = e.label or "fan"
                    colour = "green" if e.current > 0 else "red"
                    lines.append(f"    {label:<20}  [{colour}]{e.current} RPM[/]")
        else:
            lines.append("\n[dim]No fan sensors found[/]")
    except Exception:
        pass

    # Battery
    try:
        batt = psutil.sensors_battery()
        if batt:
            pct = batt.percent
            colour = "green" if pct > 40 else ("yellow" if pct > 20 else "red")
            plug = "⚡ Plugged in" if batt.power_plugged else "🔋 On battery"
            lines += [
                "",
                "[bold]Battery[/bold]",
                f"  Charge  : [{colour}]{pct:.1f}%[/]  {plug}",
            ]
            if batt.secsleft and batt.secsleft > 0:
                h, m = divmod(batt.secsleft // 60, 60)
                lines.append(f"  Time left: {h}h {m}m")
        else:
            lines.append("\n[dim]No battery detected (desktop)[/]")
    except Exception:
        pass

    # GPU (try nvidia-smi, then AMD, then /proc)
    lines += ["", "[bold]GPU[/bold]"]
    gpu_info = _get_gpu_info()
    lines.extend(gpu_info)

    return lines


def _get_gpu_info() -> list[str]:
    # NVIDIA
    nv = _run(["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits"])
    if nv:
        result = []
        for line in nv.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                name, temp, util, mem_used, mem_total = parts[:5]
                colour = "green" if int(util) < 60 else ("yellow" if int(util) < 85 else "red")
                result += [
                    f"  [cyan]{name}[/]  (NVIDIA)",
                    f"  Temp     : [yellow]{temp}°C[/]",
                    f"  Usage    : [{colour}]{util}%[/]",
                    f"  VRAM     : {mem_used} / {mem_total} MB",
                ]
        return result if result else ["  [dim]NVIDIA driver present but no data[/]"]

    # AMD ROCm
    amd = _run(["rocm-smi", "--showtemp", "--showuse", "--showmeminfo", "vram"])
    if amd:
        return ["  [cyan]AMD GPU detected (ROCm)[/]", f"  [dim]{amd[:200]}[/]"]

    # /proc/driver/nvidia
    if Path("/proc/driver/nvidia/version").exists():
        ver = _read("/proc/driver/nvidia/version").split("\n")[0]
        return [f"  [cyan]NVIDIA driver:[/] {ver}"]

    # Generic DRI check
    dri = list(Path("/dev/dri").iterdir()) if Path("/dev/dri").exists() else []
    if dri:
        return [f"  [dim]GPU device(s) found: {', '.join(d.name for d in dri)}[/]",
                "  [dim]Install nvidia-smi or ROCm for detailed info[/]"]

    return ["  [dim]No dedicated GPU detected[/]"]


def _collect_processes() -> list[str]:
    lines: list[str] = ["[bold cyan]  Top Processes[/bold cyan]", ""]

    try:
        procs = []
        attrs = ["pid", "name", "cpu_percent", "memory_percent", "status",
                 "username", "num_threads", "create_time"]
        for p in psutil.process_iter(attrs):
            try:
                procs.append(p.info)
            except Exception:
                pass

        # By CPU
        by_cpu = sorted(procs, key=lambda x: x.get("cpu_percent") or 0, reverse=True)
        lines.append("[bold]Top 15 by CPU[/bold]")
        lines.append(f"  [dim]{'PID':>7}  {'Name':<22}  {'CPU%':>5}  {'MEM%':>5}  {'Threads':>7}  Status[/]")
        for p in by_cpu[:15]:
            cpu = p.get("cpu_percent") or 0
            mem = p.get("memory_percent") or 0
            cpu_colour = "green" if cpu < 20 else ("yellow" if cpu < 60 else "red")
            mem_colour = "green" if mem < 5 else ("yellow" if mem < 20 else "red")
            lines.append(
                f"  {p.get('pid',''):>7}  {(p.get('name','') or '')[:22]:<22}  "
                f"[{cpu_colour}]{cpu:>5.1f}[/]  [{mem_colour}]{mem:>5.1f}[/]  "
                f"{p.get('num_threads', 0):>7}  [dim]{p.get('status','')}[/]"
            )

        # By memory
        by_mem = sorted(procs, key=lambda x: x.get("memory_percent") or 0, reverse=True)
        lines += ["", "[bold]Top 10 by Memory[/bold]"]
        lines.append(f"  [dim]{'PID':>7}  {'Name':<22}  {'MEM%':>5}[/]")
        for p in by_mem[:10]:
            mem = p.get("memory_percent") or 0
            colour = "green" if mem < 5 else ("yellow" if mem < 20 else "red")
            lines.append(
                f"  {p.get('pid',''):>7}  {(p.get('name','') or '')[:22]:<22}  "
                f"[{colour}]{mem:>5.1f}[/]"
            )

        # Counts
        total = len(procs)
        running = sum(1 for p in procs if p.get("status") == psutil.STATUS_RUNNING)
        sleeping = sum(1 for p in procs if p.get("status") == psutil.STATUS_SLEEPING)
        lines += [
            "",
            "[bold cyan]  Process Summary[/bold cyan]",
            f"  Total    : [cyan]{total}[/]",
            f"  Running  : [green]{running}[/]",
            f"  Sleeping : [dim]{sleeping}[/]",
        ]
    except Exception as exc:
        lines.append(f"[red]{exc}[/]")

    return lines


def _collect_hardware() -> list[str]:
    lines: list[str] = ["[bold cyan]  Hardware Info[/bold cyan]", ""]

    # uname
    uname = _run(["uname", "-a"])
    if uname:
        lines += ["[bold]uname -a[/bold]", f"  [dim]{uname}[/]", ""]

    # /proc/version
    kernel_ver = _read("/proc/version")
    if kernel_ver:
        lines += ["[bold]Kernel Build[/bold]", f"  [dim]{kernel_ver[:200]}[/]", ""]

    # DMI info from /sys/class/dmi/id/
    dmi_fields = [
        ("product_name", "Product"),
        ("product_version", "Version"),
        ("sys_vendor", "Vendor"),
        ("board_name", "Board"),
        ("board_vendor", "Board Vendor"),
        ("chassis_type", "Chassis"),
        ("bios_vendor", "BIOS Vendor"),
        ("bios_version", "BIOS Version"),
        ("bios_date", "BIOS Date"),
    ]
    dmi_lines = []
    for fname, label in dmi_fields:
        val = _read(f"/sys/class/dmi/id/{fname}")
        if val and val not in ("None", "OEM", "To be filled by O.E.M."):
            dmi_lines.append(f"  {label:<15}  [cyan]{val}[/]")
    if dmi_lines:
        lines += ["[bold]System Board (DMI)[/bold]"] + dmi_lines + [""]

    # lspci
    lspci = _run(["lspci"])
    if lspci:
        lines += ["[bold]PCI Devices (lspci)[/bold]"]
        for ln in lspci.splitlines()[:40]:
            lines.append(f"  [dim]{ln}[/]")
        if len(lspci.splitlines()) > 40:
            lines.append(f"  [dim]… {len(lspci.splitlines()) - 40} more[/]")
        lines.append("")
    else:
        lines += ["[bold]PCI Devices[/bold]", "  [dim]lspci not available[/]", ""]

    # lsusb
    lsusb = _run(["lsusb"])
    if lsusb:
        lines += ["[bold]USB Devices (lsusb)[/bold]"]
        for ln in lsusb.splitlines()[:30]:
            lines.append(f"  [dim]{ln}[/]")
        lines.append("")
    else:
        lines += ["[bold]USB Devices[/bold]", "  [dim]lsusb not available[/]", ""]

    # /proc/modules (kernel modules count)
    try:
        mods = Path("/proc/modules").read_text().strip().splitlines()
        lines += [f"[bold]Kernel Modules[/bold]", f"  [cyan]{len(mods)}[/] modules loaded", ""]
    except Exception:
        pass

    # CPU vulnerabilities
    vuln_dir = Path("/sys/devices/system/cpu/vulnerabilities")
    if vuln_dir.exists():
        lines.append("[bold]CPU Vulnerabilities[/bold]")
        for f in sorted(vuln_dir.iterdir()):
            val = _read(str(f))
            colour = "green" if "Not affected" in val or "Mitigation" in val else "red"
            lines.append(f"  {f.name:<25}  [{colour}]{val[:60]}[/]")
        lines.append("")

    return lines


# ── Screen ────────────────────────────────────────────────────────────────────

class SysInfoScreen(Screen):
    """Full hardware and OS info screen with live-refreshing tabs."""

    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
        Binding("ctrl+d", "app.navigate('dashboard')", "Dashboard"),
        Binding("ctrl+r", "refresh_all", "Refresh"),
    ]

    DEFAULT_CSS = """
    SysInfoScreen {
        background: $background;
    }
    #si-header {
        height: 3;
        background: $panel;
        padding: 0 2;
        color: $primary;
        text-style: bold;
        content-align: left middle;
    }
    #si-tabs {
        height: 1fr;
    }
    #si-footer {
        height: 1;
        background: $surface;
        content-align: center middle;
        color: $foreground;
    }
    .si-content {
        height: 100%;
        overflow-y: auto;
        padding: 0 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label(" System Information", id="si-header")
        with TabbedContent(id="si-tabs"):
            with TabPane("Overview", id="tab-overview"):
                yield Static("Loading...", classes="si-content", id="content-overview")
            with TabPane("CPU", id="tab-cpu"):
                yield Static("Loading...", classes="si-content", id="content-cpu")
            with TabPane("Memory", id="tab-mem"):
                yield Static("Loading...", classes="si-content", id="content-mem")
            with TabPane("Storage", id="tab-storage"):
                yield Static("Loading...", classes="si-content", id="content-storage")
            with TabPane("Network", id="tab-net"):
                yield Static("Loading...", classes="si-content", id="content-net")
            with TabPane("Sensors", id="tab-sensors"):
                yield Static("Loading...", classes="si-content", id="content-sensors")
            with TabPane("Processes", id="tab-procs"):
                yield Static("Loading...", classes="si-content", id="content-procs")
            with TabPane("Hardware", id="tab-hw"):
                yield Static("Loading...", classes="si-content", id="content-hw")
        yield Label(
            "Ctrl+R Refresh  Ctrl+D Dashboard  Esc Back",
            id="si-footer",
        )

    def on_mount(self) -> None:
        self._load_all()
        self.set_interval(5.0, self._refresh_live)

    @work(exclusive=False)
    async def _load_all(self) -> None:
        """Load all tabs in background workers."""
        await asyncio.gather(
            asyncio.to_thread(self._update_tab, "content-overview", _collect_overview),
            asyncio.to_thread(self._update_tab, "content-cpu",      _collect_cpu),
            asyncio.to_thread(self._update_tab, "content-mem",      _collect_memory),
            asyncio.to_thread(self._update_tab, "content-storage",  _collect_storage),
            asyncio.to_thread(self._update_tab, "content-net",      _collect_network),
            asyncio.to_thread(self._update_tab, "content-sensors",  _collect_sensors),
            asyncio.to_thread(self._update_tab, "content-procs",    _collect_processes),
            asyncio.to_thread(self._update_tab, "content-hw",       _collect_hardware),
        )

    def _update_tab(self, widget_id: str, collector) -> None:
        lines = collector()
        text = "\n".join(lines)
        try:
            self.query_one(f"#{widget_id}", Static).update(text)
        except Exception:
            pass

    def _refresh_live(self) -> None:
        """Refresh fast-changing tabs every 5 seconds."""
        self._update_tab("content-overview", _collect_overview)
        self._update_tab("content-cpu",      _collect_cpu)
        self._update_tab("content-mem",      _collect_memory)
        self._update_tab("content-procs",    _collect_processes)

    def action_refresh_all(self) -> None:
        self._load_all()
        self.app.notify("Refreshing all tabs…", timeout=2)

    def action_go_back(self) -> None:
        self.app.pop_screen()
