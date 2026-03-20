#!/usr/bin/env python3
"""App Blocker - Web UI for managing app block schedules."""

import json
import os
import signal
import subprocess
import sys
from datetime import datetime

import psutil
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
DAEMON_PID_FILE = os.path.join(os.path.dirname(__file__), "daemon.pid")


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


def get_daemon_status():
    if not os.path.exists(DAEMON_PID_FILE):
        return {"running": False, "pid": None}
    with open(DAEMON_PID_FILE) as f:
        pid = int(f.read().strip())
    try:
        proc = psutil.Process(pid)
        if proc.is_running():
            return {"running": True, "pid": pid}
    except psutil.NoSuchProcess:
        pass
    os.remove(DAEMON_PID_FILE)
    return {"running": False, "pid": None}


@app.route("/")
def index():
    config = load_config()
    processes = get_running_processes()
    daemon_status = get_daemon_status()
    now = datetime.now().strftime("%H:%M")
    return render_template(
        "index.html",
        blocked_apps=config["blocked_apps"],
        processes=processes,
        daemon_status=daemon_status,
        now=now,
    )


@app.route("/add", methods=["POST"])
def add_rule():
    config = load_config()
    app_name = request.form.get("app_name", "").strip()
    start_time = request.form.get("start_time", "").strip()
    end_time = request.form.get("end_time", "").strip()
    days = request.form.getlist("days")

    if not app_name or not start_time or not end_time:
        return redirect(url_for("index"))

    # Check for duplicate
    for rule in config["blocked_apps"]:
        if (
            rule["name"] == app_name
            and rule["start_time"] == start_time
            and rule["end_time"] == end_time
        ):
            return redirect(url_for("index"))

    config["blocked_apps"].append(
        {
            "name": app_name,
            "start_time": start_time,
            "end_time": end_time,
            "days": days if days else ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            "enabled": True,
        }
    )
    save_config(config)
    return redirect(url_for("index"))


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


@app.route("/daemon/start", methods=["POST"])
def start_daemon():
    status = get_daemon_status()
    if not status["running"]:
        daemon_script = os.path.join(os.path.dirname(__file__), "daemon.py")
        subprocess.Popen(
            [sys.executable, daemon_script],
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


@app.route("/api/processes")
def api_processes():
    return jsonify(get_running_processes())


@app.route("/api/status")
def api_status():
    return jsonify(get_daemon_status())


if __name__ == "__main__":
    print("App Blocker running at http://localhost:5000")
    app.run(debug=False, host="0.0.0.0", port=5000)
