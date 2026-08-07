"""
System domain, ported from local-mac-tool/Sources/LocalMacMCP/
{SleepTool,NotifyTool,ProcessTool,ClipboardTool,SystemHealthTool,
iCloudDriveTool,FoundationModelsTool}.swift, plus FinderTool.swift (backs
spotlight_search — corrects an earlier assumption that FinderTool was
unused; it's the search backend, just never exposed elsewhere).

clipboard: pbcopy/pbpaste (built-in macOS CLI, not AppleScript — NSPasteboard
has no AppleScript equivalent anyway).
spotlight_search: mdfind, ported from FinderTool.swift.
icloud_list: pathlib, ported from iCloudDriveTool.swift's FileManager use.
battery/cpu/memory_status: pmset/system_profiler/sysctl/ps/vm_stat parsing,
ported from SystemHealthTool.swift (which used Darwin's sysctlbyname —
Python shells out to `sysctl` instead of binding libc directly, same data).
foundation_models_query: KNOWN LIMITATION — the native on-device path
(Apple's FoundationModels Swift framework, macOS 26+) has no Python/PyObjC
binding; Swift's own source comments it "stays Swift permanently". Only the
HTTP fallback (localhost:8000/api/generate) Swift's tool also had is ported.

NOT live-tested: sleep_now and sleep_winddown(minutes<=0) both quit every
running app and put the Mac to sleep immediately — real, disruptive side
effects that would end the current work session. Ported faithfully from
the Swift source; verify manually when convenient, not as part of this
port's automated verification.
"""
import subprocess
import time
from pathlib import Path

from local_process import run_osascript, run_shell, LocalProcessError


def _quit_all_apps() -> None:
    script = '''
        tell application "System Events"
            set theNames to name of every application process whose background only is false and name is not in {"Code", "Finder", "SystemUIServer"}
            set output to ""
            repeat with n in theNames
                set output to output & n & linefeed
            end repeat
            return output
        end tell
        '''
    try:
        names_output = run_osascript(script, timeout=15)
    except LocalProcessError:
        names_output = ""
    app_names = [n.strip() for n in names_output.split("\n") if n.strip()]

    for app_name in app_names:
        escaped = app_name.replace('"', '\\"')
        quit_script = f'tell application "System Events" to quit (first application process whose name is "{escaped}")'
        try:
            run_osascript(quit_script, timeout=10)
        except LocalProcessError:
            pass
        time.sleep(1)
    time.sleep(5)


def handle_sleep_now() -> str:
    """Put Mac to sleep immediately."""
    _quit_all_apps()
    run_shell(["/usr/bin/pmset", "sleepnow"])
    return "Sleeping now."


def handle_sleep_in(minutes: int) -> str:
    """Schedule sleep after N minutes."""
    if minutes < 1:
        raise ValueError("Missing or invalid argument: minutes (must be ≥ 1)")
    result = subprocess.run(
        ["/bin/sh", "-c", f"echo 'pmset sleepnow' | at now + {minutes} minutes 2>&1"],
        capture_output=True, text=True, timeout=15,
    )
    return f"Sleep scheduled in {minutes} minute(s).\n{result.stdout.strip()}"


def handle_sleep_cancel() -> str:
    """Cancel scheduled sleep."""
    jobs = run_shell(["/usr/bin/atq"])
    if not jobs.strip():
        return "No scheduled sleep jobs found."
    subprocess.run(["/bin/sh", "-c", "atq | awk '{print $1}' | xargs atrm"], capture_output=True, timeout=15)
    return f"Cancelled all scheduled at jobs:\n{jobs.strip()}"


def handle_sleep_status() -> str:
    """Check scheduled sleep status."""
    jobs = run_shell(["/usr/bin/atq"])
    if not jobs.strip():
        return "No scheduled sleep (or at) jobs."
    return f"Scheduled at jobs:\n{jobs.strip()}"


def handle_sleep_winddown(minutes: int = 30) -> str:
    """Start wind-down routine before sleep."""
    if minutes <= 0:
        _quit_all_apps()
        run_shell(["/usr/bin/pmset", "sleepnow"])
        return "Wind-down complete. Sleeping now."

    script = '''#!/bin/bash
APP_NAMES=$(osascript -e '
  tell application "System Events"
    set theNames to name of every application process whose background only is false and name is not in {"Code", "Finder", "SystemUIServer"}
    set output to ""
    repeat with n in theNames
      set output to output & n & linefeed
    end repeat
    return output
  end tell
' 2>/dev/null)
while IFS= read -r appName; do
  [[ -z "$appName" ]] && continue
  osascript -e "tell application \\"System Events\\" to quit (first application process whose name is \\"$appName\\")" 2>/dev/null
  sleep 1
done <<< "$APP_NAMES"
sleep 5
pmset sleepnow
'''
    tmp_path = f"/tmp/sleep_winddown_{int(time.time())}.sh"
    with open(tmp_path, "w") as f:
        f.write(script)
    import os
    os.chmod(tmp_path, 0o755)
    result = subprocess.run(
        ["/bin/sh", "-c", f"echo 'bash {tmp_path}' | at now + {minutes} minutes 2>&1"],
        capture_output=True, text=True, timeout=15,
    )
    return f"Wind-down scheduled in {minutes} minute(s).\n{result.stdout.strip()}"


def handle_notify(title: str, body: str = "", subtitle: str = "") -> str:
    """Send a macOS notification.

    Note: `subtitle` is accepted but silently ignored — the original Swift
    tool's AppleScript notification call never used it either.
    """
    if not title:
        raise ValueError("Missing required argument: title")
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_body = body.replace("\\", "\\\\").replace('"', '\\"')
    run_osascript(f'display notification "{safe_body}" with title "{safe_title}" sound name "Ping"')
    return f"Notification sent: {title}"


def handle_process_list(name: str = "") -> str:
    """List running processes, optionally filtered by name."""
    result = subprocess.run(
        ["/bin/sh", "-c", f"ps aux | head -1; ps aux | grep -i '{name}' | grep -v grep | head -30"],
        capture_output=True, text=True, timeout=15,
    )
    return result.stdout or "No processes found."


_BLOCKED_PROCESSES = {"launchd", "kernel_task", "WindowServer", "loginwindow"}


def handle_process_kill(pid: int, force: bool = False) -> str:
    """Kill a process by PID."""
    if pid <= 100:
        raise ValueError("Cannot kill system processes (PID must be > 100).")
    name_result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "comm="], capture_output=True, text=True, timeout=10)
    process_name = name_result.stdout.strip() or "unknown"
    if process_name in _BLOCKED_PROCESSES:
        raise ValueError(f"Cannot kill system process: {process_name}")
    import os
    import signal as signal_module
    sig = signal_module.SIGKILL if force else signal_module.SIGTERM
    try:
        os.kill(pid, sig)
    except OSError as e:
        raise LocalProcessError(f"Failed to kill process {pid}: {e}")
    return f"Sent {'SIGKILL' if force else 'SIGTERM'} to process {pid} ({process_name})"


def handle_clipboard_read() -> str:
    """Read the macOS clipboard."""
    result = subprocess.run(["/usr/bin/pbpaste"], capture_output=True, text=True, timeout=10)
    return result.stdout if result.stdout else "Clipboard is empty or contains non-text content."


def handle_clipboard_write(text: str) -> str:
    """Write text to the macOS clipboard."""
    subprocess.run(["/usr/bin/pbcopy"], input=text, text=True, timeout=10)
    preview = text[:80].replace("\n", " ")
    ellipsis = "…" if len(text) > 80 else ""
    return f"Copied to clipboard ({len(text.encode())} bytes): {preview}{ellipsis}"


def handle_spotlight_search(query: str, path: str = "") -> list | str:
    """Search files with Spotlight (mdfind)."""
    if not query:
        raise ValueError("Missing required argument: query")
    if query.startswith("kMDItem") or "==" in query:
        args = [query]
    else:
        args = ["-name", query]
    if path:
        args = ["-onlyin", path] + args

    result = subprocess.run(["/usr/bin/mdfind"] + args, capture_output=True, text=True, timeout=30)
    output = result.stdout.strip()
    if not output:
        return "No files found."
    return [line for line in output.split("\n") if line]


def handle_icloud_list(path: str = "") -> list:
    """List iCloud Drive contents at a given subpath."""
    from datetime import datetime, timezone

    icloud_root = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
    target = (icloud_root / path).resolve() if path else icloud_root

    if not target.is_dir():
        raise LocalProcessError(f"Path not found or not a directory: {path}")

    entries = []
    for entry in sorted(target.iterdir(), key=lambda p: p.name):
        if entry.name.startswith("."):
            continue
        is_dir = entry.is_dir()
        stat = entry.stat()
        entries.append({
            "name": entry.name,
            "type": "folder" if is_dir else "file",
            "size": "—" if is_dir else f"{stat.st_size} bytes",
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "path": entry.name if not path else f"{path}/{entry.name}",
        })
    return entries


def handle_foundation_models_query(prompt: str, system: str = None, max_tokens: int = 256) -> str:
    """Query Apple Foundation Models (on-device LLM, macOS 26+) with a prompt.

    KNOWN LIMITATION: the native on-device path (Apple's FoundationModels
    Swift framework, macOS 26+) has no Python/PyObjC binding and cannot be
    called from here — Swift's own source comments this stays Swift
    permanently. This port only implements the HTTP fallback Swift's tool
    also had (POST localhost:8000/api/generate); if no local server is
    running there, this returns the same "unavailable" message Swift shows
    on macOS < 26 with no local server, rather than silently doing nothing.
    """
    if not prompt:
        raise ValueError("Missing required argument: prompt")
    system_prompt = system or "You are a helpful assistant. Be concise and direct."
    endpoint = "http://localhost:8000/api/generate"

    import json
    import urllib.request
    import urllib.error

    body = json.dumps({"prompt": prompt, "system": system_prompt, "max_tokens": max_tokens, "temperature": 0.3}).encode()
    req = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("result", "") or "Foundation Models returned no output."
    except (urllib.error.URLError, OSError, ValueError):
        return f"*(Foundation Models LLM unavailable — macOS < 26.0 and no local server on {endpoint})*"


def handle_battery_status() -> dict:
    """Get Mac battery status — charge percent, charging state, health, max capacity, and cycle count."""
    output = subprocess.run(["/usr/bin/pmset", "-g", "batt"], capture_output=True, text=True, timeout=10).stdout
    lines = output.split("\n")
    result: dict = {}

    if lines:
        result["source"] = "AC" if "AC Power" in lines[0] else "Battery"
        result["has_battery"] = "No batteries available" not in lines[0]

    batt_line = next((l for l in lines[1:] if "%" in l), None)
    if batt_line:
        parts = [p.strip() for p in batt_line.split(";")]
        pct_part = next((p for p in parts if "%" in p), None)
        if pct_part:
            pct_str = pct_part.split("\t")[-1].replace("%", "").strip()
            if pct_str.lstrip("-").isdigit():
                result["percent"] = int(pct_str)
        if len(parts) > 1:
            result["state"] = parts[1]
        time_part = next((p for p in parts if ":" in p and "remaining" in p), None)
        if not time_part:
            time_part = next((p for p in parts if "(no estimate)" in p or "finishing charge" in p or "charged" in p), None)
        if time_part:
            result["time_remaining"] = time_part

    health_output = subprocess.run(
        ["/usr/sbin/system_profiler", "SPPowerDataType"], capture_output=True, text=True, timeout=15
    ).stdout
    hlines = health_output.split("\n")
    cycle_line = next((l for l in hlines if "Cycle Count" in l), None)
    if cycle_line:
        val = cycle_line.split(":", 1)[-1].strip()
        if val.isdigit():
            result["cycle_count"] = int(val)
    cond_line = next((l for l in hlines if "Condition" in l), None)
    if cond_line:
        result["health"] = cond_line.split(":", 1)[-1].strip()
    max_cap_line = next((l for l in hlines if "Maximum Capacity" in l), None)
    if max_cap_line:
        result["max_capacity"] = max_cap_line.split(":", 1)[-1].strip()

    return result


def handle_cpu_status() -> dict:
    """Get Mac CPU status — load averages (1m/5m/15m), logical core count, and top processes by CPU usage."""
    result: dict = {}

    load_out = subprocess.run(["/usr/sbin/sysctl", "vm.loadavg"], capture_output=True, text=True, timeout=10).stdout
    if "{" in load_out and "}" in load_out:
        inner = load_out.split("{", 1)[1].split("}")[0].strip()
        vals = [float(v) for v in inner.split() if v]
        if len(vals) >= 3:
            result["load_avg"] = [round(v, 2) for v in vals[:3]]

    cores_out = subprocess.run(["/usr/sbin/sysctl", "-n", "hw.logicalcpu"], capture_output=True, text=True, timeout=10).stdout.strip()
    result["logical_cores"] = int(cores_out) if cores_out.isdigit() else 0

    ps_out = subprocess.run(["/bin/ps", "-Ao", "pid,pcpu,comm", "-r"], capture_output=True, text=True, timeout=10).stdout
    top_procs = []
    for line in ps_out.split("\n")[1:11]:
        cols = [c for c in line.strip().split(" ") if c]
        if len(cols) < 3:
            continue
        try:
            pid, cpu = int(cols[0]), float(cols[1])
        except ValueError:
            continue
        if cpu <= 0.1:
            continue
        cmd = cols[2].rsplit("/", 1)[-1]
        top_procs.append({"pid": pid, "name": cmd, "cpu_pct": round(cpu, 1)})
    result["top_processes"] = top_procs
    return result


def handle_memory_status() -> dict:
    """Get Mac memory status — total/used/free GB, wired, compressed, swap usage, used percent, and pressure level."""
    vm_out = subprocess.run(["/usr/bin/vm_stat"], capture_output=True, text=True, timeout=10).stdout
    stats: dict[str, int] = {}
    for line in vm_out.split("\n"):
        t = line.strip().replace(".", "")
        kv = t.split(":")
        if len(kv) == 2:
            val = kv[1].strip()
            if val.isdigit():
                stats[kv[0].strip()] = int(val)

    page_size_out = subprocess.run(["/usr/sbin/sysctl", "-n", "hw.pagesize"], capture_output=True, text=True, timeout=10).stdout.strip()
    page_size = int(page_size_out) if page_size_out.isdigit() else 16384

    def pages(key: str) -> int:
        return stats.get(key, 0) * page_size

    active = pages("Pages active")
    wired = pages("Pages wired down")
    compressed = pages("Pages occupied by compressor")
    free = pages("Pages free")
    speculative = pages("Pages speculative")

    memsize_out = subprocess.run(["/usr/sbin/sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=10).stdout.strip()
    total_ram = int(memsize_out) if memsize_out.isdigit() else 0

    gb = 1024 * 1024 * 1024
    used_approx = active + wired + compressed

    result: dict = {
        "total_gb": f"{total_ram / gb:.1f}",
        "used_gb": f"{used_approx / gb:.1f}",
        "free_gb": f"{(free + speculative) / gb:.1f}",
        "wired_gb": f"{wired / gb:.1f}",
        "compressed_gb": f"{compressed / gb:.1f}",
    }

    swap_out = subprocess.run(["/usr/sbin/sysctl", "vm.swapusage"], capture_output=True, text=True, timeout=10).stdout.strip()
    if "used =" in swap_out:
        result["swap_used"] = swap_out.split("used = ", 1)[1].split(" ")[0]
    if "total =" in swap_out:
        result["swap_total"] = swap_out.split("total = ", 1)[1].split(" ")[0]

    used_pct = int(used_approx / total_ram * 100) if total_ram > 0 else 0
    result["used_pct"] = used_pct
    result["pressure"] = "high" if used_pct > 85 else "moderate" if used_pct > 65 else "normal"

    return result
