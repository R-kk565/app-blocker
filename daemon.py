#!/usr/bin/env python3
"""App Blocker Daemon - Monitors and kills blocked apps during scheduled times."""

import json
import os
import signal
import sys
import time
from datetime import datetime

import psutil

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
PID_FILE = os.path.join(os.path.dirname(__file__), "daemon.pid")
LOG_FILE = os.path.join(os.path.dirname(__file__), "daemon.log")

DAY_MAP = {
    0: "mon",
    1: "tue",
    2: "wed",
    3: "thu",
    4: "fri",
    5: "sat",
    6: "sun",
}


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"blocked_apps": []}
    with open(CONFIG_FILE) as f:
        return json.load(f)


def is_blocked_now(rule):
    """Check if a rule is active at the current time."""
    if not rule.get("enabled", True):
        return False

    now = datetime.now()
    today = DAY_MAP[now.weekday()]

    allowed_days = rule.get("days", list(DAY_MAP.values()))
    if today not in allowed_days:
        return False

    current = now.strftime("%H:%M")
    start = rule.get("start_time", "00:00")
    end = rule.get("end_time", "23:59")

    # Handle overnight ranges (e.g., 22:00 - 06:00)
    if start <= end:
        return start <= current <= end
    else:
        return current >= start or current <= end


def kill_blocked_processes(blocked_names):
    """Find and kill processes that are currently blocked."""
    killed = []
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            name = proc.info["name"]
            if name in blocked_names:
                proc.terminate()
                killed.append(f"{name} (pid={proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return killed


def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def cleanup(signum=None, frame=None):
    log("Daemon stopping.")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    sys.exit(0)


def main():
    write_pid()
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    log(f"Daemon started (pid={os.getpid()})")

    while True:
        try:
            config = load_config()
            blocked_now = set()

            for rule in config.get("blocked_apps", []):
                if is_blocked_now(rule):
                    blocked_now.add(rule["name"])

            if blocked_now:
                killed = kill_blocked_processes(blocked_now)
                if killed:
                    log(f"Killed: {', '.join(killed)}")

        except Exception as e:
            log(f"Error: {e}")

        time.sleep(5)  # Check every 5 seconds


if __name__ == "__main__":
    main()
