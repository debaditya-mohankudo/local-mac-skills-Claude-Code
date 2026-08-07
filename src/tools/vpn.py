"""
vpn.py
------
MCP tool handlers for Surfshark VPN control, ported from
local-mac-tool/Sources/LocalMacMCP/SurfsharkTool.swift — which never used
AppleScript at all, confirmed via reading the source. It drives macOS's
built-in `scutil --nc` (network configuration) CLI directly and reads
session metadata from Surfshark's own preferences plist. Grooming's
speculation about System Events UI scripting was wrong; this is a pure
CLI/plist port, no AppleScript feasibility question to resolve.
"""
from __future__ import annotations

import plistlib
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

_SESSION_PLIST = (
    Path.home()
    / "Library"
    / "Group Containers"
    / "YHUG37CKN8.com.surfshark.vpn.tunnel"
    / "Library"
    / "Preferences"
    / "YHUG37CKN8.com.surfshark.vpn.tunnel.plist"
)


def _run(args: list[str], timeout: int = 15) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return result.stdout


def _scutil_list() -> list[dict]:
    output = _run(["/usr/sbin/scutil", "--nc", "list"])
    connections = []
    for line in output.split("\n"):
        if "com.surfshark" not in line:
            continue
        state = "Connected" if "(Connected)" in line else "Disconnected"
        first_q = line.find('"')
        last_q = line.rfind('"')
        name = line[first_q + 1:last_q] if first_q != -1 and last_q != -1 and first_q != last_q else "Unknown"
        if "WireGuard" in line:
            proto = "WireGuard"
        elif "OpenVPN" in line:
            proto = "OpenVPN"
        elif "IKEv2" in line:
            proto = "IKEv2"
        else:
            proto = "VPN"
        connections.append({"name": name, "state": state, "vpnProtocol": proto})
    return connections


def _scutil_detail(name: str) -> dict:
    output = _run(["/usr/sbin/scutil", "--nc", "status", name])
    lines = output.split("\n")

    vpn_ip = ""
    dns: list[str] = []
    iface = ""

    in_dns = False
    for line in lines:
        t = line.strip()
        if t.startswith("DNSServers"):
            in_dns = True
            continue
        if in_dns:
            if t.startswith("}"):
                in_dns = False
                continue
            if t.startswith("0 :") or t.startswith("1 :"):
                ip = t.split(":", 1)[1].strip() if ":" in t else ""
                if ip:
                    dns.append(ip)

    in_addresses = False
    for line in lines:
        t = line.strip()
        if t.startswith("Addresses"):
            in_addresses = True
            continue
        if in_addresses:
            if t.startswith("}"):
                in_addresses = False
                continue
            if t.startswith("0 :"):
                vpn_ip = t.split(":", 1)[1].strip() if ":" in t else ""

    for line in lines:
        t = line.strip()
        if t.startswith("InterfaceName"):
            iface = t.split(":", 1)[1].strip() if ":" in t else ""
            break

    return {"vpn_ip": vpn_ip, "dns_servers": dns, "interface": iface}


def _read_session_info() -> dict | None:
    if not _SESSION_PLIST.exists():
        return None
    try:
        with open(_SESSION_PLIST, "rb") as f:
            data = plistlib.load(f)
        raw = data.get("vpnSessionInfo")
        if not raw:
            return None
        import json
        info = json.loads(raw)
    except (OSError, plistlib.InvalidFileException, ValueError, KeyError):
        return None

    server = info.get("vpnServer") or {}
    return {
        "server": server.get("locationName", ""),
        "country_code": server.get("countryCode", ""),
        "server_address": server.get("serverAddress", ""),
        "vpn_protocol": info.get("vpnProtocol", ""),
        "transport": info.get("transportProtocol", ""),
        "post_quantum": info.get("isPostQuantumSecureConnection", False),
    }


def handle_status() -> dict:
    """Get Surfshark VPN connection status — connected/disconnected, server location, protocol, DNS, and post-quantum status."""
    connections = _scutil_list()
    active = next((c for c in connections if c["state"] == "Connected"), None)

    result: dict = {
        "connected": active is not None,
        "connections": [{"name": c["name"], "state": c["state"], "protocol": c["vpnProtocol"]} for c in connections],
    }

    if active:
        detail = _scutil_detail(active["name"])
        result["ip_address"] = detail["vpn_ip"]
        result["dns_servers"] = detail["dns_servers"]
        result["interface"] = detail["interface"]

        session = _read_session_info()
        if session:
            result.update(session)

    return result


def handle_disconnect() -> dict:
    """Disconnect Surfshark VPN."""
    connections = _scutil_list()
    active = next((c for c in connections if c["state"] == "Connected"), None)
    if not active:
        return {"ok": False, "message": "VPN is already disconnected"}
    _run(["/usr/sbin/scutil", "--nc", "stop", active["name"]])
    return {"ok": True, "message": f"Disconnected {active['name']}"}


def handle_connect() -> dict:
    """Connect Surfshark VPN (reconnects the WireGuard config)."""
    connections = _scutil_list()
    target = next(
        (c for c in connections if "WireGuard" in c["vpnProtocol"] and c["state"] != "Connected"),
        next((c for c in connections if c["state"] != "Connected"), None),
    )
    if not target:
        return {"ok": False, "message": "VPN is already connected"}
    _run(["/usr/sbin/scutil", "--nc", "start", target["name"]])
    return {"ok": True, "message": f"Connected {target['name']}"}


def handle_pause(minutes: int = 30) -> dict:
    """Pause Surfshark VPN for a set number of minutes (1–480), then auto-reconnect. Default: 30 min."""
    if not (0 < minutes <= 480):
        return {"ok": False, "message": "minutes must be between 1 and 480"}

    connections = _scutil_list()
    active = next((c for c in connections if c["state"] == "Connected"), None)
    if not active:
        return {"ok": False, "message": "VPN is already disconnected — nothing to pause"}
    conn_name = active["name"]

    _run(["/usr/sbin/scutil", "--nc", "stop", conn_name])

    seconds = minutes * 60
    script_path = f"/tmp/surfshark_resume_{int(time.time())}.sh"
    script_content = f'#!/bin/bash\nsleep {seconds}\n/usr/sbin/scutil --nc start "{conn_name}"\n'
    with open(script_path, "w") as f:
        f.write(script_content)
    Path(script_path).chmod(0o755)

    subprocess.Popen(
        ["/bin/bash", script_path],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    resume_time = datetime.now(ZoneInfo("Asia/Kolkata")) + timedelta(seconds=seconds)
    resume_str = resume_time.strftime("%H:%M") + " IST"

    return {
        "ok": True,
        "message": f"VPN paused for {minutes} min — will reconnect at {resume_str}",
        "resume_at": resume_str,
        "connection": conn_name,
    }
