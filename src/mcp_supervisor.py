from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence


def _default_log_path() -> Path:
    return Path.home() / ".claude" / "local-mac-mcp.log"


def _install_signal_handlers() -> None:
    def _handle_signal(signum: int, _frame: object) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)


def run_process_loop(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    restart_delay: float = 1.0,
    max_restarts: int | None = None,
    log_path: Path | None = None,
    once: bool = False,
) -> int:
    """Run a child process, restarting it when it exits unexpectedly."""
    _install_signal_handlers()
    log_path = log_path or _default_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    restart_count = 0
    while True:
        try:
            if log_path.exists() and log_path.stat().st_size > 10_000_000:
                log_path.write_text("", encoding="utf-8")
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] starting {' '.join(command)}\n")
                handle.flush()

            process = subprocess.Popen(
                list(command),
                cwd=str(cwd) if cwd else None,
                env=env,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            returncode = process.wait()
        except KeyboardInterrupt:
            return 0

        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(
                f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] exited with code {returncode}\n"
            )
            handle.flush()

        if once or (max_restarts is not None and restart_count >= max_restarts):
            return returncode

        restart_count += 1
        time.sleep(restart_delay)


def main() -> int:
    parser = argparse.ArgumentParser(description="Keep the local-mac MCP server alive")
    parser.add_argument("--once", action="store_true", help="run the child process once without restarting")
    parser.add_argument("--restart-delay", type=float, default=1.0, help="seconds between restart attempts")
    parser.add_argument("--max-restarts", type=int, default=None, help="maximum number of restarts before giving up")
    parser.add_argument("--log-path", type=Path, default=None, help="path to the supervisor log file")
    parser.add_argument("child", nargs=argparse.REMAINDER, default=None, help="child command to run")
    args = parser.parse_args()

    if not args.child:
        repo_root = Path(__file__).resolve().parents[1]
        child = [sys.executable, str(repo_root / "mcp_server.py")]
    else:
        child = args.child[1:] if args.child and args.child[0] == "--" else args.child

    return run_process_loop(
        child,
        cwd=Path.cwd(),
        env=os.environ.copy(),
        restart_delay=args.restart_delay,
        max_restarts=args.max_restarts,
        log_path=args.log_path,
        once=args.once,
    )


if __name__ == "__main__":
    raise SystemExit(main())
