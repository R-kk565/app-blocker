#!/usr/bin/env python3
"""
DNS Daemon for iOS App Blocking.

Listens on UDP port 53. Blocked app domains return 0.0.0.0.
All other queries are forwarded to an upstream DNS (default: 8.8.8.8).

Usage:
  sudo python3 dns_daemon.py [--upstream 8.8.8.8] [--port 53]
"""

import argparse
import json
import os
import signal
import socket
import sys
import threading
import time
from datetime import datetime

from dnslib import DNSRecord, RR, QTYPE, A
from dnslib.server import DNSServer, BaseResolver, DNSLogger

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
PID_FILE = os.path.join(os.path.dirname(__file__), "dns_daemon.pid")
LOG_FILE = os.path.join(os.path.dirname(__file__), "dns_daemon.log")

DAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}


def log(message: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {message}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {"blocked_apps": []}
    with open(CONFIG_FILE) as f:
        return json.load(f)


def is_blocked_now(rule: dict) -> bool:
    if not rule.get("enabled", True):
        return False
    today = DAY_MAP[datetime.now().weekday()]
    if today not in rule.get("days", list(DAY_MAP.values())):
        return False
    current = datetime.now().strftime("%H:%M")
    start, end = rule.get("start_time", "00:00"), rule.get("end_time", "23:59")
    if start <= end:
        return start <= current <= end
    return current >= start or current <= end


def get_blocked_domains() -> set[str]:
    """Return all domains that should be blocked right now."""
    config = load_config()
    blocked = set()
    for rule in config.get("blocked_apps", []):
        if rule.get("type") != "ios":
            continue
        if is_blocked_now(rule):
            for domain in rule.get("domains", []):
                # Add both bare domain and wildcard
                blocked.add(domain.lstrip("*.").lower())
    return blocked


class BlockingResolver(BaseResolver):
    def __init__(self, upstream: str = "8.8.8.8", upstream_port: int = 53):
        self.upstream = upstream
        self.upstream_port = upstream_port

    def resolve(self, request, handler):
        qname = str(request.q.qname).rstrip(".").lower()
        blocked_domains = get_blocked_domains()

        # Check if qname matches any blocked domain or its subdomain
        is_blocked = any(
            qname == domain or qname.endswith("." + domain)
            for domain in blocked_domains
        )

        if is_blocked:
            log(f"BLOCKED: {qname}")
            reply = request.reply()
            reply.add_answer(
                RR(request.q.qname, QTYPE.A, rdata=A("0.0.0.0"), ttl=10)
            )
            return reply

        # Forward to upstream DNS
        try:
            proxy_r = DNSRecord.parse(
                request.send(self.upstream, self.upstream_port, timeout=3)
            )
            return proxy_r
        except Exception as e:
            log(f"Upstream error for {qname}: {e}")
            return request.reply()


def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def cleanup(signum=None, frame=None):
    log("DNS daemon stopping.")
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="DNS-based iOS app blocker")
    parser.add_argument("--upstream", default="8.8.8.8", help="Upstream DNS server")
    parser.add_argument("--port", type=int, default=53, help="Listen port")
    args = parser.parse_args()

    write_pid()
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    resolver = BlockingResolver(upstream=args.upstream, upstream_port=53)

    # Suppress dnslib's built-in logger
    logger = DNSLogger(prefix=False)

    server = DNSServer(resolver, port=args.port, address="0.0.0.0", logger=logger)

    log(f"DNS daemon started on port {args.port}, upstream={args.upstream}")
    server.start_thread()

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        cleanup()


if __name__ == "__main__":
    main()
