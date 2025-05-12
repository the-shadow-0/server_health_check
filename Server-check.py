#!/usr/bin/env python3
"""
Server_health_check.py

A Server health-check tool:
 - System load (with fallback)
 - CPU usage & temperature (via psutil)
 - Disk space
 - Memory usage
 - Selective service restart (Apache/Nginx + MySQL)
 - Log-file error scanning (with size guard)
 - Website availability (throttled)
 - Colorized terminal output
 - Optional email alerts (SMTP)
 - Configurable via environment or websites.txt
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from colorama import init as colorama_init, Fore, Style
import psutil 
from dotenv import load_dotenv

colorama_init(autoreset=True)

''' Load environment variables from .env file if it exists, if not, use system environment variables;
This allows for easy configuration of the script without modifying the code and is useful for deployment in different environments.
'''
load_dotenv()

SCRIPT_DIR = Path(__file__).parent
WEBSITES_FILE = SCRIPT_DIR / "websites.txt"
WEBSITES = []
if WEBSITES_FILE.exists():
    with WEBSITES_FILE.open() as f:
        WEBSITES = [line.strip() for line in f 
                    if line.strip() and not line.startswith('#')]
else:
    WEBSITES = os.getenv("WEB_SITES", "").split(",")
    WEBSITES = [w for w in WEBSITES if w]

APACHE_LOG = os.getenv("APACHE_LOG", "/var/log/apache2/error.log")
NGINX_LOG = os.getenv("NGINX_LOG", "/var/log/nginx/error.log")
MYSQL_LOG = os.getenv("MYSQL_LOG", "/var/log/mysql/error.log")

DISK_WARNING_THRESHOLD = int(os.getenv("DISK_WARNING_THRESHOLD", "90"))
MEMORY_WARNING_THRESHOLD_MB = int(os.getenv("MEMORY_WARNING_THRESHOLD_MB", "100"))
LOG_SIZE_THRESHOLD_MB = int(os.getenv("LOG_SIZE_THRESHOLD_MB", "10"))

WEBSITE_TIMEOUT_S = float(os.getenv("WEBSITE_TIMEOUT_S", "5"))
WEBSITE_THROTTLE_S = float(os.getenv("WEBSITE_THROTTLE_S", "1"))

LOG_FILE = SCRIPT_DIR / f"health_check_{datetime.now():%Y%m%d_%H%M%S}.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

def info(msg):
    print(Fore.CYAN + msg)
    logging.info(msg)

def warn(msg):
    print(Fore.YELLOW + "WARNING: " + msg)
    logging.warning(msg)

def error(msg):
    print(Fore.RED + "ERROR: " + msg)
    logging.error(msg)

def check_system_load():
    info("Checking system load...")
    try:
        load1, load5, load15 = os.getloadavg()
    except (AttributeError, OSError):
        load1, load5, load15 = psutil.getloadavg()
    info(f"Load Average (1m/5m/15m): {load1:.2f}/{load5:.2f}/{load15:.2f}")

def check_cpu():
    info("Checking CPU usage and temperature...")
    cpu_percent = psutil.cpu_percent(interval=1)
    info(f"CPU Usage: {cpu_percent:.1f}%")
    try:
        temps = psutil.sensors_temperatures()
        for name, entries in temps.items():
            for entry in entries:
                info(f"Temp sensor '{name}': {entry.current:.1f}°C")
    except (AttributeError, KeyError):
        warn("CPU temperature data not available on this system.")

def check_disk_space():
    info("Checking disk space usage...")
    for part in psutil.disk_partitions(all=False):
        usage = psutil.disk_usage(part.mountpoint)
        pct = usage.percent
        info(f"{part.mountpoint}: {pct:.1f}% used ({usage.used//(2**30)}GiB/{usage.total//(2**30)}GiB)")
        if pct > DISK_WARNING_THRESHOLD:
            warn(f"High disk usage on {part.mountpoint}: {pct:.1f}%")

def check_memory():
    info("Checking memory usage...")
    vm = psutil.virtual_memory()
    free_mb = vm.available // (2**20)
    info(f"Available Memory: {free_mb}MB ({vm.percent:.1f}% used)")
    if free_mb < MEMORY_WARNING_THRESHOLD_MB:
        warn(f"Low free memory: {free_mb}MB")

def restart_services():
    info("Restarting active web & DB services...")
    services = []
    for svc in ("apache2", "nginx"):
        if subprocess.run(["systemctl", "is-active", svc], capture_output=True).stdout.strip() == b"active":
            services.append(svc)
    services.append("mysql")
    for svc in services:
        try:
            info(f"Restarting {svc}...")
            subprocess.run(["systemctl", "restart", svc], check=True)
            status = subprocess.run(["systemctl", "is-active", svc],
                                    capture_output=True).stdout.decode().strip()
            info(f"{svc} status: {status}")
        except subprocess.CalledProcessError:
            error(f"Failed to restart or find service: {svc}")

def check_logs(log_path):
    info(f"Scanning logs: {log_path}")
    p = Path(log_path)
    if not p.exists():
        warn(f"Log file not found: {log_path}")
        return
    if p.stat().st_size > LOG_SIZE_THRESHOLD_MB * 1024 * 1024:
        warn(f"Skipping {log_path} (>{LOG_SIZE_THRESHOLD_MB}MB)")
        return
    with p.open(errors="ignore") as f:
        lines = f.readlines()[-50:]
    for line in lines:
        if any(term in line.lower() for term in ("error", "fail", "critical")):
            error(f"{p.name}: {line.strip()}")

def check_websites():
    if not WEBSITES:
        warn("No websites configured to check.")
        return
    info("Checking website statuses...")
    for url in WEBSITES:
        try:
            r = requests.get(url, timeout=WEBSITE_TIMEOUT_S)
            if r.status_code == 200:
                print(Fore.GREEN + f"{url} is UP")
                logging.info(f"{url} status 200 OK")
            else:
                warn(f"{url} returned {r.status_code}")
        except requests.RequestException as e:
            error(f"{url} check failed: {e}")
        time.sleep(WEBSITE_THROTTLE_S)

def display_banner():
    banner =    "=============================================="
    banner += "\n      Welcome to SHC (Server Health Check)    "      
    banner += "\n     A Powerful Tool for Security Research    "
    banner += "\n                   Developed by the_shadow_0  "
    banner += "\n=============================================="
    print(banner)

def main():
    display_banner()
    info("=== Server(VPS) Health Check Started ===")
    check_system_load()
    check_cpu()
    check_disk_space()
    check_memory()
    restart_services()
    check_logs(APACHE_LOG)
    check_logs(NGINX_LOG)
    check_logs(MYSQL_LOG)
    check_websites()
    info("=== Health Check Complete ===")
    info(f"Log file: {LOG_FILE}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error(f"Unhandled exception: {e}")
        sys.exit(1)
