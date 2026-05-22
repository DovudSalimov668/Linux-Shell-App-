"""SysInfoScreen — full hardware and OS deep-dive with tabbed detail panels."""

from __future__ import annotations

import asyncio
import os
import platform
import socket
import subprocess
import time
from pathlib import Path

import psutil
from rich.markup import escape as mu_escape

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.containers import Horizontal
from textual.widgets import Button, Label, Static, TabbedContent, TabPane


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run(cmd: list[str], timeout: int = 5) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _read(path: str) -> str:
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


def _bar(pct: float, width: int = 20) -> str:
    pct = max(0.0, min(100.0, pct))
    filled = int(pct / 100 * width)
    colour = "green" if pct < 60 else ("yellow" if pct < 85 else "red")
    return f"[{colour}]{'█' * filled}[/][dim]{'░' * (width - filled)}[/]"


# ── Data collectors ───────────────────────────────────────────────────────────

def _collect_overview() -> list[str]:
    lines: list[str] = []

    # OS
    os_name = platform.system()
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("PRETTY_NAME="):
                os_name = line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass

    lines += [
        "[bold cyan]  System Overview[/bold cyan]",
        "",
        f"[bold]Hostname     :[/]  [cyan]{socket.gethostname()}[/]",
        f"[bold]OS           :[/]  {os_name}",
        f"[bold]Kernel       :[/]  {platform.release()}",
        f"[bold]Architecture :[/]  {platform.machine()}",
        f"[bold]Python       :[/]  {platform.python_version()}",
    ]

    # Uptime
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

    shell = os.environ.get("SHELL", "unknown")
    term = os.environ.get("TERM", "unknown")
    lines += [
        f"[bold]Shell        :[/]  {shell}",
        f"[bold]Terminal     :[/]  {term}",
    ]

    # Load average + IO wait
    try:
        la = psutil.getloadavg()
        ct = psutil.cpu_times_percent(interval=None)
        iowait = getattr(ct, "iowait", 0.0)
        steal  = getattr(ct, "steal", 0.0)
        lines += [
            "",
            "[bold cyan]  CPU Load[/bold cyan]",
            f"  Load avg : [green]{la[0]:.2f}[/] (1m)  [yellow]{la[1]:.2f}[/] (5m)  [red]{la[2]:.2f}[/] (15m)",
            f"  IO wait  : [{'yellow' if iowait > 10 else 'dim'}]{iowait:.1f}%[/]",
            f"  Steal    : [{'red' if steal > 5 else 'dim'}]{steal:.1f}%[/]  [dim](VM overhead)[/]",
        ]
    except Exception:
        pass

    # Live snapshot
    try:
        cpu_pct = psutil.cpu_percent(interval=None)
        vm = psutil.virtual_memory()
        cores = psutil.cpu_count(logical=True)
        lines += [
            "",
            "[bold cyan]  Live Snapshot[/bold cyan]",
            f"  CPU      : {_bar(cpu_pct, 18)} [bold]{cpu_pct:.1f}%[/]  ({cores} threads)",
            f"  RAM      : {_bar(vm.percent, 18)} [bold]{vm.percent:.1f}%[/]"
            f"  [dim]{_fmt_bytes(vm.used)} / {_fmt_bytes(vm.total)}[/]",
        ]
        sw = psutil.swap_memory()
        if sw.total:
            lines.append(
                f"  Swap     : {_bar(sw.percent, 18)} [bold]{sw.percent:.1f}%[/]"
                f"  [dim]{_fmt_bytes(sw.used)} / {_fmt_bytes(sw.total)}[/]"
            )
    except Exception:
        pass

    # Logged-in users
    try:
        users = psutil.users()
        lines += ["", "[bold cyan]  Logged-in Users[/bold cyan]"]
        if users:
            for u in users:
                started = time.strftime("%H:%M", time.localtime(u.started))
                lines.append(f"  [cyan]{u.name:<12}[/]  tty:{u.terminal or '?':<8}  since {started}")
        else:
            lines.append("  [dim]none[/]")
    except Exception:
        pass

    # Runtime versions
    lines += ["", "[bold cyan]  Runtime Versions[/bold cyan]"]
    runtimes = [
        (["python3", "--version"], "Python"),
        (["python",  "--version"], "Python (alt)"),
        (["node",    "--version"], "Node.js"),
        (["npm",     "--version"], "npm"),
        (["java",    "-version"],  "Java"),
        (["go",      "version"],   "Go"),
        (["rustc",   "--version"], "Rust"),
        (["ruby",    "--version"], "Ruby"),
        (["php",     "--version"], "PHP"),
        (["docker",  "--version"], "Docker"),
        (["git",     "--version"], "Git"),
    ]
    found_any = False
    for cmd, label in runtimes:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            out = (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr) else ""
            if out:
                lines.append(f"  {label:<14}  [dim]{out[:70]}[/]")
                found_any = True
        except Exception:
            pass
    if not found_any:
        lines.append("  [dim]No runtimes detected[/]")

    return lines


def _collect_cpu() -> list[str]:
    lines: list[str] = ["[bold cyan]  CPU Details[/bold cyan]", ""]

    model = vendor = cache_size = stepping = family = cpu_mhz = ""
    flags: list[str] = []

    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if   k == "model name"  and not model:      model = v
            elif k == "vendor_id"   and not vendor:     vendor = v
            elif k == "cache size"  and not cache_size: cache_size = v
            elif k == "flags"       and not flags:      flags = v.split()
            elif k == "stepping"    and not stepping:   stepping = v
            elif k == "cpu family"  and not family:     family = v
            elif k == "cpu MHz"     and not cpu_mhz:    cpu_mhz = v
    except Exception:
        pass

    if model:      lines.append(f"[bold]Model        :[/]  [yellow]{model}[/]")
    if vendor:     lines.append(f"[bold]Vendor       :[/]  {vendor}")
    try:
        logical  = psutil.cpu_count(logical=True) or 0
        physical = psutil.cpu_count(logical=False) or 0
        lines += [
            f"[bold]Physical     :[/]  {physical} cores",
            f"[bold]Logical      :[/]  {logical} threads",
        ]
    except Exception:
        pass
    if cache_size: lines.append(f"[bold]Cache        :[/]  {cache_size}")
    if family:     lines.append(f"[bold]Family       :[/]  {family}  Stepping: {stepping}")

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

    # CPU governor
    gov = _read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    if gov:
        lines.append(f"[bold]Governor     :[/]  [cyan]{gov}[/]")

    # CPU times breakdown
    try:
        ct = psutil.cpu_times_percent(interval=None)
        lines += [
            "",
            "[bold cyan]  CPU Time Breakdown[/bold cyan]",
            f"  User     : [cyan]{ct.user:.1f}%[/]",
            f"  System   : [yellow]{ct.system:.1f}%[/]",
            f"  Idle     : [green]{ct.idle:.1f}%[/]",
            f"  IO wait  : [{'yellow' if ct.iowait > 10 else 'dim'}]{getattr(ct, 'iowait', 0.0):.1f}%[/]",
            f"  Steal    : [{'red' if getattr(ct, 'steal', 0) > 5 else 'dim'}]{getattr(ct, 'steal', 0.0):.1f}%[/]",
            f"  Nice     : [dim]{ct.nice:.1f}%[/]",
        ]
    except Exception:
        pass

    # Context switches and interrupts from /proc/stat
    try:
        for line in Path("/proc/stat").read_text().splitlines():
            if line.startswith("ctxt "):
                ctx = int(line.split()[1])
                lines.append(f"  Context switches since boot: [dim]{ctx:,}[/]")
            elif line.startswith("intr "):
                intr = int(line.split()[1])
                lines.append(f"  Interrupts since boot      : [dim]{intr:,}[/]")
    except Exception:
        pass

    # Per-core usage
    try:
        per_core: list[float] = psutil.cpu_percent(interval=None, percpu=True)  # type: ignore[assignment]
        lines += ["", "[bold cyan]  Per-Core Usage[/bold cyan]"]
        for i, pct in enumerate(per_core):
            lines.append(f"  Core {i:>2}  {_bar(pct, 20)} [{('green' if pct < 60 else 'yellow' if pct < 85 else 'red')}]{pct:5.1f}%[/]")
    except Exception:
        pass

    # Notable CPU features
    notable = {
        "sse4_2": "SSE4.2", "avx": "AVX", "avx2": "AVX2", "avx512f": "AVX-512",
        "aes": "AES-NI", "vmx": "VT-x", "svm": "AMD-V",
        "hypervisor": "Hypervisor", "ht": "HT",
        "lm": "64-bit", "nx": "NX-bit", "rdrand": "RDRAND",
        "tsc": "TSC", "pse": "PSE", "pae": "PAE",
    }
    found = [label for flag, label in notable.items() if flag in flags]
    if found:
        lines += ["", "[bold cyan]  CPU Features[/bold cyan]",
                  "  " + "  ".join(f"[cyan]{f}[/]" for f in found)]
    if flags:
        lines += ["", "[bold cyan]  All Flags[/bold cyan]",
                  "  [dim]" + "  ".join(flags[:80]) + ("[/]\n  [dim]…" if len(flags) > 80 else "[/]")]

    # Vulnerabilities
    vuln_dir = Path("/sys/devices/system/cpu/vulnerabilities")
    if vuln_dir.exists():
        lines += ["", "[bold cyan]  Vulnerability Mitigations[/bold cyan]"]
        for f in sorted(vuln_dir.iterdir()):
            val = _read(str(f))
            colour = "green" if "Not affected" in val or "Mitigation" in val else "red"
            lines.append(f"  {f.name:<25}  [{colour}]{val[:60]}[/]")

    return lines


def _collect_memory() -> list[str]:
    lines: list[str] = ["[bold cyan]  Memory Details[/bold cyan]", ""]

    try:
        vm = psutil.virtual_memory()
        lines += [
            f"[bold]Total        :[/]  [cyan]{_fmt_bytes(vm.total)}[/]",
            f"[bold]Available    :[/]  [green]{_fmt_bytes(vm.available)}[/]",
            f"[bold]Used         :[/]  {_fmt_bytes(vm.used)}  ({vm.percent:.1f}%)",
            f"[bold]Free         :[/]  {_fmt_bytes(vm.free)}",
        ]
        for attr, label in [("buffers","Buffers"), ("cached","Cached"), ("shared","Shared")]:
            v = getattr(vm, attr, None)
            if v is not None:
                lines.append(f"[bold]{label:<13}:[/]  [dim]{_fmt_bytes(v)}[/]")
        lines += ["", f"  {_bar(vm.percent, 40)} {vm.percent:.1f}%"]
    except Exception:
        pass

    try:
        sw = psutil.swap_memory()
        lines += [
            "",
            "[bold cyan]  Swap[/bold cyan]",
            f"  Total  : {_fmt_bytes(sw.total)}",
            f"  Used   : {_fmt_bytes(sw.used)}  ({sw.percent:.1f}%)",
            f"  Free   : {_fmt_bytes(sw.free)}",
        ]
        if sw.total:
            lines.append(f"  {_bar(sw.percent, 40)} {sw.percent:.1f}%")
    except Exception:
        pass

    # /proc/meminfo extras
    try:
        meminfo: dict[str, str] = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, _, v = line.partition(":")
            meminfo[k.strip()] = v.strip()

        lines += ["", "[bold cyan]  /proc/meminfo Detail[/bold cyan]"]
        for k, label in [
            ("Dirty",          "Dirty"),
            ("Writeback",      "Writeback"),
            ("AnonPages",      "Anonymous"),
            ("Mapped",         "Mapped"),
            ("Shmem",          "Shared mem"),
            ("Slab",           "Kernel slab"),
            ("KReclaimable",   "K-reclaimable"),
            ("SReclaimable",   "Slab reclaimable"),
            ("SUnreclaim",     "Slab unreclaim"),
            ("PageTables",     "Page tables"),
            ("VmallocTotal",   "Vmalloc total"),
            ("VmallocUsed",    "Vmalloc used"),
            ("HugePages_Total","HugePages total"),
            ("HugePages_Free", "HugePages free"),
            ("Hugepagesize",   "HugePage size"),
            ("MemAvailable",   "Available"),
            ("CommitLimit",    "Commit limit"),
            ("Committed_AS",   "Committed"),
        ]:
            if k in meminfo:
                lines.append(f"  {label:<20}  [dim]{meminfo[k]}[/]")
    except Exception:
        pass

    # Top memory consumers
    try:
        procs = []
        for p in psutil.process_iter(["pid", "name", "memory_info", "memory_percent"]):
            try:
                procs.append(p.info)
            except Exception:
                pass
        procs.sort(key=lambda x: x.get("memory_percent") or 0, reverse=True)
        lines += ["", "[bold cyan]  Top Memory Consumers[/bold cyan]",
                  f"  [dim]{'PID':>7}  {'Name':<25}  {'RSS':<10}  MEM%[/]"]
        for p in procs[:12]:
            rss = (p.get("memory_info") or type("", (), {"rss": 0})()).rss
            pct = p.get("memory_percent") or 0
            name = (p.get("name") or "")[:25]
            colour = "red" if pct > 10 else ("yellow" if pct > 5 else "green")
            lines.append(f"  {p.get('pid',''):>7}  {name:<25}  {_fmt_bytes(rss):<10}  [{colour}]{pct:.1f}%[/]")
    except Exception:
        pass

    return lines


def _collect_storage() -> list[str]:
    lines: list[str] = ["[bold cyan]  Storage[/bold cyan]", ""]

    # Mount options from /proc/mounts
    mount_opts: dict[str, str] = {}
    try:
        for line in Path("/proc/mounts").read_text().splitlines():
            parts = line.split()
            if len(parts) >= 4:
                mount_opts[parts[1]] = parts[3]
    except Exception:
        pass

    try:
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
            except (PermissionError, OSError):
                continue
            pct = usage.percent
            colour = "green" if pct < 70 else ("yellow" if pct < 90 else "red")
            lines += [
                f"[bold]{p.mountpoint}[/]  [dim]{p.fstype}[/]  [dim]{p.device}[/]",
                f"  {_bar(pct, 24)} [{colour}]{pct:.1f}%[/]",
                f"  Used: [cyan]{_fmt_bytes(usage.used)}[/]  "
                f"Free: [green]{_fmt_bytes(usage.free)}[/]  "
                f"Total: {_fmt_bytes(usage.total)}",
            ]
            if p.mountpoint in mount_opts:
                lines.append(f"  Options: [dim]{mount_opts[p.mountpoint][:80]}[/]")
            lines.append("")
    except Exception:
        pass

    # Inode usage (df -i)
    df_i = _run(["df", "-i", "-h"])
    if df_i:
        lines += ["[bold cyan]  Inode Usage  (df -i)[/bold cyan]"]
        for ln in df_i.splitlines()[:20]:
            lines.append(f"  [dim]{ln}[/]")
        lines.append("")

    # Per-disk I/O counters
    try:
        io_all = psutil.disk_io_counters(perdisk=True)
        if io_all:
            lines += ["[bold cyan]  Disk I/O Counters[/bold cyan]"]
            for disk, io in list(io_all.items())[:10]:
                lines += [
                    f"  [cyan]{disk}[/]",
                    f"    Read  : {_fmt_bytes(io.read_bytes):<12} {io.read_count:>8,} ops"
                    + (f"  {io.read_time:,} ms" if hasattr(io, "read_time") else ""),
                    f"    Write : {_fmt_bytes(io.write_bytes):<12} {io.write_count:>8,} ops"
                    + (f"  {io.write_time:,} ms" if hasattr(io, "write_time") else ""),
                ]
    except Exception:
        pass

    # /proc/partitions
    try:
        raw = Path("/proc/partitions").read_text()
        lines += ["", "[bold cyan]  Block Devices  (/proc/partitions)[/bold cyan]"]
        for line in raw.splitlines()[2:]:
            parts_raw = line.split()
            if len(parts_raw) == 4:
                _, _, blocks, name = parts_raw
                size_mb = int(blocks) / 1024
                if size_mb >= 1:
                    size_str = f"{size_mb/1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.0f} MB"
                    lines.append(f"  [cyan]{name:<12}[/]  {size_str}")
    except Exception:
        pass

    return lines


def _collect_network() -> list[str]:
    lines: list[str] = ["[bold cyan]  Network Interfaces[/bold cyan]", ""]

    import socket as _socket

    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        io    = psutil.net_io_counters(pernic=True)

        for iface in sorted(addrs.keys()):
            s = stats.get(iface)
            is_up  = s.isup if s else False
            speed  = f"{s.speed} Mbps" if s and s.speed else "?"
            mtu    = str(s.mtu) if s else "?"
            status = "[green]UP[/]" if is_up else "[red]DOWN[/]"
            lines.append(f"[bold cyan]{iface}[/]  {status}  speed={speed}  MTU={mtu}")

            for addr in addrs[iface]:
                if addr.family == _socket.AF_INET:
                    lines.append(f"  IPv4   : [green]{addr.address}[/]  mask={addr.netmask}")
                elif addr.family == _socket.AF_INET6:
                    a = addr.address.split("%")[0]
                    lines.append(f"  IPv6   : [cyan]{a}[/]")
                elif hasattr(_socket, "AF_PACKET") and addr.family == _socket.AF_PACKET:  # type: ignore[attr-defined]
                    lines.append(f"  MAC    : [dim]{addr.address}[/]")

            if iface in io:
                n = io[iface]
                lines += [
                    f"  Sent   : {_fmt_bytes(n.bytes_sent)}  "
                    f"({n.packets_sent:,} pkts  err={n.errout}  drop={n.dropout})",
                    f"  Recv   : {_fmt_bytes(n.bytes_recv)}  "
                    f"({n.packets_recv:,} pkts  err={n.errin}  drop={n.dropin})",
                ]
            lines.append("")
    except Exception as exc:
        lines.append(f"[red]{mu_escape(str(exc))}[/]")

    # DNS servers
    lines += ["[bold cyan]  DNS Servers  (/etc/resolv.conf)[/bold cyan]"]
    try:
        for line in Path("/etc/resolv.conf").read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(f"  [dim]{line}[/]")
    except Exception:
        lines.append("  [dim]unavailable[/]")
    lines.append("")

    # Default gateway
    lines.append("[bold cyan]  Routing[/bold cyan]")
    gw = _run(["ip", "route", "show", "default"])
    if gw:
        for ln in gw.splitlines()[:5]:
            lines.append(f"  [dim]{ln}[/]")
    else:
        try:
            for line in Path("/proc/net/route").read_text().splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 3 and parts[1] == "00000000":
                    gw_hex = parts[2]
                    gw_ip = ".".join(str(int(gw_hex[i:i+2], 16)) for i in (6, 4, 2, 0))
                    lines.append(f"  Default gateway: [green]{gw_ip}[/]  iface: [cyan]{parts[0]}[/]")
                    break
        except Exception:
            lines.append("  [dim]route info unavailable[/]")
    lines.append("")

    # Listening ports with owning process
    lines.append("[bold cyan]  Listening Ports[/bold cyan]")
    try:
        pid_names: dict[int, str] = {}
        for p in psutil.process_iter(["pid", "name"]):
            try:
                pid_names[p.info["pid"]] = p.info["name"] or ""
            except Exception:
                pass

        conns = psutil.net_connections(kind="inet")
        listening = sorted(
            [c for c in conns if c.status == "LISTEN"],
            key=lambda c: c.laddr.port,
        )
        if listening:
            lines.append(f"  [dim]{'Port':>6}  {'Proto':<6}  {'Address':<22}  Process[/]")
            for c in listening[:40]:
                proto = "TCP"
                addr  = f"{c.laddr.ip}:{c.laddr.port}"
                pname = pid_names.get(c.pid or -1, "?")[:20]
                pid_s = str(c.pid) if c.pid else "?"
                lines.append(f"  [cyan]{c.laddr.port:>6}[/]  {proto:<6}  {addr:<22}  [dim]{pname}[/] ({pid_s})")
        else:
            lines.append("  [dim]no listening sockets[/]")
    except Exception as exc:
        lines.append(f"  [dim]{mu_escape(str(exc))}[/]")
    lines.append("")

    # Connection summary
    try:
        conns = psutil.net_connections()
        by_status: dict[str, int] = {}
        for c in conns:
            by_status[c.status or "?"] = by_status.get(c.status or "?", 0) + 1
        lines += ["[bold cyan]  Connection Summary[/bold cyan]"]
        for status, count in sorted(by_status.items(), key=lambda x: -x[1]):
            colour = "green" if status == "ESTABLISHED" else ("cyan" if status == "LISTEN" else "dim")
            lines.append(f"  {status:<16}  [{colour}]{count}[/]")
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
                    colour = "green" if t < 60 else ("yellow" if t < 80 else "red")
                    crit   = f"  [dim](high={e.high}  crit={e.critical})[/]" if e.high else ""
                    lines.append(f"    {label:<22}  {_bar(t, 10)} [{colour}]{t:.1f}°C[/]{crit}")
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
                    label  = e.label or "fan"
                    colour = "green" if e.current > 0 else "red"
                    lines.append(f"    {label:<22}  [{colour}]{e.current} RPM[/]")
    except Exception:
        pass

    # Battery
    try:
        batt = psutil.sensors_battery()
        if batt:
            pct    = batt.percent
            colour = "green" if pct > 40 else ("yellow" if pct > 20 else "red")
            plug   = "⚡ Plugged in" if batt.power_plugged else "🔋 On battery"
            lines += [
                "",
                "[bold]Battery[/bold]",
                f"  Charge    : {_bar(pct, 20)} [{colour}]{pct:.1f}%[/]  {plug}",
            ]
            if batt.secsleft and batt.secsleft > 0:
                h, m = divmod(batt.secsleft // 60, 60)
                lines.append(f"  Time left : {h}h {m}m")
        else:
            lines.append("\n[dim]No battery (desktop)[/]")
    except Exception:
        pass

    # GPU
    lines += ["", "[bold]GPU[/bold]"]
    lines.extend(_get_gpu_info())

    # Power supply via /sys
    lines += ["", "[bold]Power Supply  (/sys/class/power_supply)[/bold]"]
    ps_dir = Path("/sys/class/power_supply")
    found_ps = False
    if ps_dir.exists():
        for ps in sorted(ps_dir.iterdir()):
            status   = _read(str(ps / "status"))
            capacity = _read(str(ps / "capacity"))
            ptype    = _read(str(ps / "type"))
            if status or capacity:
                found_ps = True
                lines.append(
                    f"  [cyan]{ps.name:<12}[/]  type={ptype or '?'}  "
                    f"status={status or '?'}  capacity={capacity or '?'}%"
                )
    if not found_ps:
        lines.append("  [dim]no power supply info[/]")

    return lines


def _get_gpu_info() -> list[str]:
    nv = _run(["nvidia-smi",
               "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total",
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
                    f"  Temp   : [yellow]{temp}°C[/]",
                    f"  Usage  : {_bar(float(util), 20)} [{colour}]{util}%[/]",
                    f"  VRAM   : {_fmt_bytes(int(mem_used)*1024*1024)} / {_fmt_bytes(int(mem_total)*1024*1024)}",
                ]
        return result if result else ["  [dim]NVIDIA driver present but no data[/]"]

    amd = _run(["rocm-smi", "--showtemp", "--showuse"])
    if amd:
        return ["  [cyan]AMD GPU (ROCm)[/]", f"  [dim]{amd[:300]}[/]"]

    if Path("/proc/driver/nvidia/version").exists():
        ver = _read("/proc/driver/nvidia/version").split("\n")[0]
        return [f"  [cyan]NVIDIA driver:[/] {ver}"]

    dri = list(Path("/dev/dri").iterdir()) if Path("/dev/dri").exists() else []
    if dri:
        return [
            f"  [dim]DRI devices: {', '.join(d.name for d in dri)}[/]",
            "  [dim]Install nvidia-smi or ROCm tools for details[/]",
        ]
    return ["  [dim]No dedicated GPU detected[/]"]


def _collect_processes() -> list[str]:
    lines: list[str] = ["[bold cyan]  Top Processes[/bold cyan]", ""]

    try:
        procs = []
        attrs = ["pid", "ppid", "name", "cpu_percent", "memory_percent",
                 "status", "username", "num_threads", "create_time", "cmdline"]
        for p in psutil.process_iter(attrs):
            try:
                procs.append(p.info)
            except Exception:
                pass

        # Summary counts
        total    = len(procs)
        running  = sum(1 for p in procs if p.get("status") == psutil.STATUS_RUNNING)
        sleeping = sum(1 for p in procs if p.get("status") == psutil.STATUS_SLEEPING)
        zombie   = sum(1 for p in procs if p.get("status") == psutil.STATUS_ZOMBIE)
        stopped  = sum(1 for p in procs if p.get("status") == psutil.STATUS_STOPPED)
        threads  = sum(p.get("num_threads") or 0 for p in procs)
        lines += [
            "[bold cyan]  Process Summary[/bold cyan]",
            f"  Total    : [cyan]{total}[/]  Threads: [dim]{threads:,}[/]",
            f"  Running  : [green]{running}[/]  Sleeping: [dim]{sleeping}[/]"
            + (f"  Zombie: [red]{zombie}[/]" if zombie else "")
            + (f"  Stopped: [yellow]{stopped}[/]" if stopped else ""),
        ]

        # Top by CPU
        by_cpu = sorted(procs, key=lambda x: x.get("cpu_percent") or 0, reverse=True)
        lines += ["", "[bold]Top 15 by CPU[/bold]",
                  f"  [dim]{'PID':>7}  {'Name':<22}  {'CPU%':>5}  {'MEM%':>5}  {'Thr':>4}  {'User':<12}  Status[/]"]
        for p in by_cpu[:15]:
            cpu = p.get("cpu_percent") or 0
            mem = p.get("memory_percent") or 0
            cc  = "green" if cpu < 20 else ("yellow" if cpu < 60 else "red")
            mc  = "green" if mem < 5  else ("yellow" if mem < 20 else "red")
            lines.append(
                f"  {p.get('pid',''):>7}  {(p.get('name','') or '')[:22]:<22}  "
                f"[{cc}]{cpu:>5.1f}[/]  [{mc}]{mem:>5.1f}[/]  "
                f"{p.get('num_threads',0):>4}  "
                f"{(p.get('username','') or '')[:12]:<12}  [dim]{p.get('status','')}[/]"
            )

        # Top by Memory
        by_mem = sorted(procs, key=lambda x: x.get("memory_percent") or 0, reverse=True)
        lines += ["", "[bold]Top 10 by Memory[/bold]",
                  f"  [dim]{'PID':>7}  {'Name':<22}  {'MEM%':>5}[/]"]
        for p in by_mem[:10]:
            mem    = p.get("memory_percent") or 0
            colour = "green" if mem < 5 else ("yellow" if mem < 20 else "red")
            lines.append(
                f"  {p.get('pid',''):>7}  {(p.get('name','') or '')[:22]:<22}  [{colour}]{mem:>5.1f}[/]"
            )

        # Most threads
        by_thr = sorted(procs, key=lambda x: x.get("num_threads") or 0, reverse=True)
        lines += ["", "[bold]Most Threads[/bold]"]
        for p in by_thr[:8]:
            thr = p.get("num_threads") or 0
            if thr < 2:
                break
            lines.append(
                f"  {p.get('pid',''):>7}  {(p.get('name','') or '')[:22]:<22}  [cyan]{thr}[/] threads"
            )

        # Zombies (if any)
        if zombie:
            lines += ["", f"[bold][red]Zombie Processes ({zombie})[/red][/bold]"]
            for p in procs:
                if p.get("status") == psutil.STATUS_ZOMBIE:
                    lines.append(
                        f"  PID {p.get('pid','')}  {(p.get('name','') or '')[:30]}  "
                        f"[dim]parent={p.get('ppid','')}[/]"
                    )

    except Exception as exc:
        lines.append(f"[red]{mu_escape(str(exc))}[/]")

    return lines


def _collect_services() -> list[str]:
    lines: list[str] = ["[bold cyan]  System Services[/bold cyan]", ""]

    # systemd
    systemd_ok = False
    running_svcs = _run(
        ["systemctl", "list-units", "--type=service", "--state=running",
         "--no-pager", "--no-legend"], timeout=8
    )
    if running_svcs:
        systemd_ok = True
        lines += ["[bold]Running Services[/bold]"]
        for ln in running_svcs.splitlines()[:30]:
            name = ln.split()[0] if ln.split() else ln
            lines.append(f"  [green]●[/]  [dim]{name}[/]")
        if len(running_svcs.splitlines()) > 30:
            lines.append(f"  [dim]… {len(running_svcs.splitlines())-30} more[/]")
        lines.append("")

    failed_svcs = _run(
        ["systemctl", "list-units", "--type=service", "--state=failed",
         "--no-pager", "--no-legend"], timeout=8
    )
    if failed_svcs:
        systemd_ok = True
        lines += ["[bold]Failed Services[/bold]"]
        for ln in failed_svcs.splitlines():
            lines.append(f"  [red]✗[/]  [red]{ln.split()[0] if ln.split() else ln}[/]")
        lines.append("")

    if not systemd_ok:
        lines.append("[dim]systemd not available on this system[/]")
        lines.append("")

    # Cron jobs
    lines += ["[bold cyan]  Cron Jobs[/bold cyan]"]
    for cron_path in ["/etc/crontab", "/var/spool/cron/crontabs"]:
        p = Path(cron_path)
        if p.is_file():
            lines.append(f"[bold]{cron_path}[/bold]")
            for ln in p.read_text(errors="replace").splitlines()[:20]:
                if ln.strip() and not ln.startswith("#"):
                    lines.append(f"  [dim]{ln[:100]}[/]")
        elif p.is_dir():
            for f in sorted(p.iterdir())[:5]:
                try:
                    lines.append(f"  [cyan]{f.name}[/]")
                    for ln in f.read_text(errors="replace").splitlines()[:10]:
                        if ln.strip() and not ln.startswith("#"):
                            lines.append(f"    [dim]{ln[:80]}[/]")
                except Exception:
                    pass
    lines.append("")

    # Open files count per process (top 10)
    lines += ["[bold cyan]  Open File Descriptors (top 10)[/bold cyan]"]
    try:
        fd_counts = []
        for p in psutil.process_iter(["pid", "name"]):
            try:
                fds = p.num_fds()
                fd_counts.append((fds, p.info["pid"], p.info["name"] or "?"))
            except Exception:
                pass
        fd_counts.sort(reverse=True)
        for fds, pid, name in fd_counts[:10]:
            colour = "red" if fds > 500 else ("yellow" if fds > 100 else "green")
            lines.append(f"  [{colour}]{fds:>6}[/] fds  pid={pid}  {name[:30]}")
    except Exception:
        lines.append("  [dim]unavailable[/]")

    return lines


def _collect_hardware() -> list[str]:
    lines: list[str] = ["[bold cyan]  Hardware Info[/bold cyan]", ""]

    # uname / kernel
    uname = _run(["uname", "-a"])
    if uname:
        lines += ["[bold]uname -a[/bold]", f"  [dim]{uname}[/]", ""]

    # Kernel cmdline
    cmdline = _read("/proc/cmdline")
    if cmdline:
        lines += ["[bold]Kernel Boot Parameters[/bold]", f"  [dim]{cmdline[:300]}[/]", ""]

    # /proc/version
    kver = _read("/proc/version")
    if kver:
        lines += ["[bold]Kernel Build[/bold]", f"  [dim]{kver[:200]}[/]", ""]

    # DMI / SMBIOS
    dmi_fields = [
        ("product_name",   "Product"),
        ("product_version","Version"),
        ("sys_vendor",     "Vendor"),
        ("board_name",     "Board"),
        ("board_vendor",   "Board Vendor"),
        ("chassis_type",   "Chassis"),
        ("bios_vendor",    "BIOS Vendor"),
        ("bios_version",   "BIOS Version"),
        ("bios_date",      "BIOS Date"),
    ]
    dmi_lines = []
    for fname, label in dmi_fields:
        val = _read(f"/sys/class/dmi/id/{fname}")
        if val and val not in ("None", "OEM", "To be filled by O.E.M."):
            dmi_lines.append(f"  {label:<15}  [cyan]{val}[/]")
    if dmi_lines:
        lines += ["[bold]System Board (DMI/SMBIOS)[/bold]"] + dmi_lines + [""]

    # lspci
    lspci = _run(["lspci", "-v"], timeout=8) or _run(["lspci"])
    if lspci:
        lines += ["[bold]PCI Devices  (lspci)[/bold]"]
        for ln in lspci.splitlines()[:50]:
            lines.append(f"  [dim]{ln}[/]")
        extra = len(lspci.splitlines()) - 50
        if extra > 0:
            lines.append(f"  [dim]… {extra} more lines[/]")
        lines.append("")
    else:
        lines += ["[bold]PCI Devices[/bold]", "  [dim]lspci not installed[/]", ""]

    # lsusb
    lsusb = _run(["lsusb"])
    if lsusb:
        lines += ["[bold]USB Devices  (lsusb)[/bold]"]
        for ln in lsusb.splitlines()[:30]:
            lines.append(f"  [dim]{ln}[/]")
        lines.append("")
    else:
        lines += ["[bold]USB Devices[/bold]", "  [dim]lsusb not installed[/]", ""]

    # Kernel modules
    try:
        mods = Path("/proc/modules").read_text().strip().splitlines()
        lines += [f"[bold]Loaded Kernel Modules[/bold]", f"  [cyan]{len(mods)}[/] modules loaded"]
        for ln in mods[:15]:
            name = ln.split()[0]
            size = int(ln.split()[1])
            lines.append(f"  [dim]{name:<25}  {_fmt_bytes(size)}[/]")
        if len(mods) > 15:
            lines.append(f"  [dim]… {len(mods)-15} more[/]")
        lines.append("")
    except Exception:
        pass

    # CPU vulnerabilities
    vuln_dir = Path("/sys/devices/system/cpu/vulnerabilities")
    if vuln_dir.exists():
        lines += ["[bold]CPU Vulnerability Mitigations[/bold]"]
        for f in sorted(vuln_dir.iterdir()):
            val    = _read(str(f))
            colour = "green" if "Not affected" in val or "Mitigation" in val else "red"
            lines.append(f"  {f.name:<25}  [{colour}]{val[:60]}[/]")
        lines.append("")

    return lines


# ── Screen ────────────────────────────────────────────────────────────────────

class SysInfoScreen(Screen):
    """Full hardware and OS info screen with 9 live-refreshing tabs."""

    BINDINGS = [
        Binding("escape,q", "go_back", "Back"),
        Binding("ctrl+d", "app.navigate('dashboard')", "Dashboard"),
        Binding("ctrl+r", "refresh_all", "Refresh"),
    ]

    DEFAULT_CSS = """
    SysInfoScreen { background: $background; }
    #si-header {
        height: 3;
        background: $panel;
        padding: 0 2;
        layout: horizontal;
        align: left middle;
        border-bottom: solid $border;
    }
    #si-header-title {
        width: 1fr;
        color: $primary;
        text-style: bold;
        content-align: left middle;
    }
    #si-back-btn {
        width: auto;
        min-width: 12;
        height: 3;
    }
    #si-tabs  { height: 1fr; }
    #si-footer {
        height: 1;
        background: $surface;
        content-align: center middle;
        color: $foreground;
    }
    .si-content {
        height: 1fr;
        overflow-y: auto;
        padding: 0 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="si-header"):
            yield Label("⚡ System Information", id="si-header-title")
            yield Button("← Back", id="si-back-btn", variant="default")
        with TabbedContent(id="si-tabs"):
            with TabPane("Overview",  id="tab-overview"):
                yield Static("Loading…", classes="si-content", id="content-overview")
            with TabPane("CPU",       id="tab-cpu"):
                yield Static("Loading…", classes="si-content", id="content-cpu")
            with TabPane("Memory",    id="tab-mem"):
                yield Static("Loading…", classes="si-content", id="content-mem")
            with TabPane("Storage",   id="tab-storage"):
                yield Static("Loading…", classes="si-content", id="content-storage")
            with TabPane("Network",   id="tab-net"):
                yield Static("Loading…", classes="si-content", id="content-net")
            with TabPane("Sensors",   id="tab-sensors"):
                yield Static("Loading…", classes="si-content", id="content-sensors")
            with TabPane("Processes", id="tab-procs"):
                yield Static("Loading…", classes="si-content", id="content-procs")
            with TabPane("Services",  id="tab-services"):
                yield Static("Loading…", classes="si-content", id="content-services")
            with TabPane("Hardware",  id="tab-hw"):
                yield Static("Loading…", classes="si-content", id="content-hw")
        yield Label(
            "Tab/Shift+Tab Switch tabs  Ctrl+R Refresh  Ctrl+D Dashboard  Esc Back",
            id="si-footer",
        )

    def on_mount(self) -> None:
        self._load_all()
        self.set_interval(5.0, self._refresh_live)

    @work(exclusive=False)
    async def _load_all(self) -> None:
        async def _load_one(widget_id: str, collector) -> None:
            lines = await asyncio.to_thread(collector)
            try:
                self.query_one(f"#{widget_id}", Static).update("\n".join(lines))
            except Exception:
                pass

        await asyncio.gather(
            _load_one("content-overview",  _collect_overview),
            _load_one("content-cpu",       _collect_cpu),
            _load_one("content-mem",       _collect_memory),
            _load_one("content-storage",   _collect_storage),
            _load_one("content-net",       _collect_network),
            _load_one("content-sensors",   _collect_sensors),
            _load_one("content-procs",     _collect_processes),
            _load_one("content-services",  _collect_services),
            _load_one("content-hw",        _collect_hardware),
        )

    @work(exclusive=False)
    async def _refresh_live(self) -> None:
        async def _load_one(widget_id: str, collector) -> None:
            lines = await asyncio.to_thread(collector)
            try:
                self.query_one(f"#{widget_id}", Static).update("\n".join(lines))
            except Exception:
                pass

        await asyncio.gather(
            _load_one("content-overview", _collect_overview),
            _load_one("content-cpu",      _collect_cpu),
            _load_one("content-mem",      _collect_memory),
            _load_one("content-procs",    _collect_processes),
        )

    def action_refresh_all(self) -> None:
        self._load_all()
        self.app.notify("Refreshing all tabs…", timeout=2)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "si-back-btn":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
