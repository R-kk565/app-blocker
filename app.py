#!/usr/bin/env python3
"""App Blocker - Web UI for managing app block schedules."""

import json
import os
import signal
import socket
import subprocess
import sys
from datetime import datetime

import psutil
from flask import Flask, jsonify, redirect, render_template, request, url_for

from ios_apps import IOS_APPS, get_categories

app = Flask(__name__)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
DAEMON_PID_FILE = os.path.join(os.path.dirname(__file__), "daemon.pid")
DNS_PID_FILE = os.path.join(os.path.dirname(__file__), "dns_daemon.pid")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {"blocked_apps": []}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_running_processes():
    """Return a sorted list of unique running process names."""
    processes = set()
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            name = proc.info["name"]
            if name and not name.startswith(("[", "kthread", "ksoftirqd")):
                processes.add(name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return sorted(processes, key=str.lower)


def _get_pid_status(pid_file: str) -> dict:
    if not os.path.exists(pid_file):
        return {"running": False, "pid": None}
    with open(pid_file) as f:
        pid = int(f.read().strip())
    try:
        proc = psutil.Process(pid)
        if proc.is_running():
            return {"running": True, "pid": pid}
    except psutil.NoSuchProcess:
        pass
    os.remove(pid_file)
    return {"running": False, "pid": None}


def get_daemon_status():
    return _get_pid_status(DAEMON_PID_FILE)


def get_dns_daemon_status():
    return _get_pid_status(DNS_PID_FILE)


def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


# ── Routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    config = load_config()
    processes = get_running_processes()
    daemon_status = get_daemon_status()
    dns_status = get_dns_daemon_status()
    ios_categories = get_categories()
    local_ip = get_local_ip()

    desktop_rules = [r for r in config["blocked_apps"] if r.get("type") != "ios"]
    ios_rules = [r for r in config["blocked_apps"] if r.get("type") == "ios"]

    return render_template(
        "index.html",
        blocked_apps=config["blocked_apps"],
        desktop_rules=desktop_rules,
        ios_rules=ios_rules,
        processes=processes,
        daemon_status=daemon_status,
        dns_status=dns_status,
        ios_categories=ios_categories,
        ios_apps=IOS_APPS,
        local_ip=local_ip,
        now=datetime.now().strftime("%H:%M"),
    )


@app.route("/add", methods=["POST"])
def add_rule():
    config = load_config()
    rule_type = request.form.get("type", "desktop")
    app_name = request.form.get("app_name", "").strip()
    start_time = request.form.get("start_time", "").strip()
    end_time = request.form.get("end_time", "").strip()
    days = request.form.getlist("days")

    if not app_name or not start_time or not end_time:
        return redirect(url_for("index"))

    all_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    if rule_type == "ios":
        # iOS: store domains from the known app list
        domains = IOS_APPS.get(app_name, {}).get("domains", [])
        rule = {
            "type": "ios",
            "name": app_name,
            "domains": domains,
            "start_time": start_time,
            "end_time": end_time,
            "days": days if days else all_days,
            "enabled": True,
        }
    else:
        rule = {
            "type": "desktop",
            "name": app_name,
            "start_time": start_time,
            "end_time": end_time,
            "days": days if days else all_days,
            "enabled": True,
        }

    # Dedup
    for existing in config["blocked_apps"]:
        if (
            existing.get("type") == rule_type
            and existing["name"] == app_name
            and existing["start_time"] == start_time
            and existing["end_time"] == end_time
        ):
            return redirect(url_for("index"))

    config["blocked_apps"].append(rule)
    save_config(config)
    return redirect(url_for("index") + f"#{'ios' if rule_type == 'ios' else 'desktop'}")


@app.route("/delete/<int:index>", methods=["POST"])
def delete_rule(index):
    config = load_config()
    if 0 <= index < len(config["blocked_apps"]):
        config["blocked_apps"].pop(index)
        save_config(config)
    return redirect(url_for("index"))


@app.route("/toggle/<int:index>", methods=["POST"])
def toggle_rule(index):
    config = load_config()
    if 0 <= index < len(config["blocked_apps"]):
        config["blocked_apps"][index]["enabled"] = not config["blocked_apps"][index].get(
            "enabled", True
        )
        save_config(config)
    return redirect(url_for("index"))


# ── Daemon control ───────────────────────────────────────────────────────

@app.route("/daemon/start", methods=["POST"])
def start_daemon():
    if not get_daemon_status()["running"]:
        subprocess.Popen(
            [sys.executable, os.path.join(os.path.dirname(__file__), "daemon.py")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return redirect(url_for("index"))


@app.route("/daemon/stop", methods=["POST"])
def stop_daemon():
    status = get_daemon_status()
    if status["running"]:
        try:
            os.kill(status["pid"], signal.SIGTERM)
        except ProcessLookupError:
            pass
        if os.path.exists(DAEMON_PID_FILE):
            os.remove(DAEMON_PID_FILE)
    return redirect(url_for("index"))


@app.route("/dns/start", methods=["POST"])
def start_dns():
    if not get_dns_daemon_status()["running"]:
        subprocess.Popen(
            [sys.executable, os.path.join(os.path.dirname(__file__), "dns_daemon.py")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return redirect(url_for("index"))


@app.route("/dns/stop", methods=["POST"])
def stop_dns():
    status = get_dns_daemon_status()
    if status["running"]:
        try:
            os.kill(status["pid"], signal.SIGTERM)
        except ProcessLookupError:
            pass
        if os.path.exists(DNS_PID_FILE):
            os.remove(DNS_PID_FILE)
    return redirect(url_for("index"))


# ── API ──────────────────────────────────────────────────────────────────

@app.route("/api/processes")
def api_processes():
    return jsonify(get_running_processes())


@app.route("/api/status")
def api_status():
    return jsonify({
        "daemon": get_daemon_status(),
        "dns": get_dns_daemon_status(),
    })


if __name__ == "__main__":
    print("App Blocker running at http://localhost:5000")
    app.run(debug=False, host="0.0.0.0", port=5000)
