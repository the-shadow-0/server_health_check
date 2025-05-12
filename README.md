# Server_health_check
A simple script for monitoring your server(s) for free

# VPS Health Check

A comprehensive, easy-to-use Python script to monitor and maintain the health of your VPS.  

## Features

- **System Load**: 1, 5, 15-minute averages (with fallback).
- **CPU Monitoring**: Utilization percentage and temperature.
- **Disk Space**: Per-mountpoint usage with warning thresholds.
- **Memory Usage**: Available RAM and usage percentage.
- **Service Management**: Auto-detect & restart Apache2/Nginx and MySQL.
- **Log Scanning**: Searches last 50 lines of key log files for errors.
- **Website Uptime**: HTTP checks for configured sites, with throttling.
- **Colorized Output**: Easy visual identification of statuses.
- **Configurable**:  
  - `.env` support for all thresholds and paths  
  - `websites.txt` for site list (one URL per line)
- **Logging**: Timestamped log file for auditing.

## Requirements

- Python 3.8+
- Linux server (systemd)
- `pip install`:
  - `psutil`
  - `requests`
  - `colorama`
  - `python-dotenv`

## Installation

1. **Clone this repo**  
   ```bash
   git clone https://github.com/youruser/vps-health-check.git
   cd vps-health-check
   python3 Server_health_check.py
    ```

2. **Install dependencies**

  ```bash
  pip install -r requirements.txt
   ```
3. **Configure**
   After cloning the repository and installing dependencies, you need to configure the script using either the .env file or websites.txt:
   Create Your .env File

After cloning the repository and installing dependencies, you need to configure the script using either the .env file or websites.txt:

Create Your .env File

Copy the provided .env.example to .env:

cp .env.example .env

    Open .env in your favorite editor and set your values:
    WEB_SITES: Comma-separated list of your site URLs (no spaces).
    APACHE_LOG, NGINX_LOG, MYSQL_LOG: Absolute paths to each service's error log.
    Threshold values: adjust DISK_WARNING_THRESHOLD, MEMORY_WARNING_THRESHOLD_MB, and LOG_SIZE_THRESHOLD_MB to suit your environment.
    Website check timing: WEBSITE_TIMEOUT_S (seconds to wait for a response) and WEBSITE_THROTTLE_S (delay between each HTTP request).
    Alternatively, Use websites.txt
    Create or edit websites.txt in the project root.
    Add one URL per line. Lines starting with # are ignored.

4. **Run the Script**
   python3 vps_health_check.py
