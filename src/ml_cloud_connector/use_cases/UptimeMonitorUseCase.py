import logging
import os
import subprocess
import time
import json
import requests


class UptimeMonitorUseCase:
    GRAYLOG_HOST = os.environ.get("GRAYLOG_HOST", "your_graylog_server_ip_or_hostname")
    GRAYLOG_PORT = os.environ.get("GRAYLOG_PORT", "12202")
    UPTIME_THRESHOLD_HOURS = int(os.environ.get("UPTIME_THRESHOLD_HOURS", 20))
    CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 300))
    ALERT_FLAG_FILE = "/tmp/uptime_alert_sent_python"

    def __init__(self):
        self.logger = logging.getLogger("UptimeMonitorUseCase")
        self.logger.setLevel(logging.INFO)

    @staticmethod
    def get_system_uptime_minutes():
        try:
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])
            return int(uptime_seconds / 60)
        except FileNotFoundError:
            logging.error("'/proc/uptime' not found. Cannot determine system uptime.")
            return 0
        except Exception as e:
            logging.error(f"Error reading system uptime: {e}")
            return 0

    @staticmethod
    def get_hostname():
        try:
            return subprocess.check_output(["hostname"]).decode().strip()
        except Exception as e:
            logging.error(f"Error getting hostname: {e}")
            return "unknown_host"

    @staticmethod
    def get_ip_address():
        try:
            return subprocess.check_output(["hostname", "-I"]).decode().split()[0].strip()
        except Exception as e:
            logging.error(f"Error getting IP address: {e}")
            return "unknown_ip"

    def send_gelf_message(self, short_message, full_message, level=3, custom_fields=None):
        if custom_fields is None:
            custom_fields = {}

        gelf_payload = {
            "version": "1.1",
            "host": self.get_hostname(),
            "short_message": short_message,
            "full_message": full_message,
            "timestamp": time.time(),
            "level": level,
            "_source_ip": self.get_ip_address(),
            "_alert_source": "uptime_monitor_python",
        }

        for key, value in custom_fields.items():
            gelf_payload[f"_{key}"] = value

        try:
            response = requests.post(
                f"http://{self.GRAYLOG_HOST}:{self.GRAYLOG_PORT}/gelf",
                data=json.dumps(gelf_payload),
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=10,
            )

            if response.status_code == 202:
                self.logger.info(f"Successfully sent GELF message to Graylog: {short_message}")
            else:
                self.logger.error(
                    f"Failed to send GELF message to Graylog. Status code: {response.status_code}, Response: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error while sending GELF message to Graylog: {e}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while sending GELF message: {e}")

    def monitor_uptime(self):
        self.log_to_journal("Starting Uptime Monitor Service...")
        uptime_threshold_minutes = self.UPTIME_THRESHOLD_HOURS * 60

        while True:
            current_uptime_minutes = self.get_system_uptime_minutes()
            current_uptime_hours = int(current_uptime_minutes / 60)
            hostname = self.get_hostname()

            self.log_to_journal(
                f"[{hostname}] Current uptime: {current_uptime_hours} hours ({current_uptime_minutes} minutes)"
            )

            if current_uptime_minutes > uptime_threshold_minutes:
                if not os.path.exists(self.ALERT_FLAG_FILE):
                    self.log_to_journal(f"[{hostname}] Uptime threshold exceeded! Sending alert to Graylog.")

                    short_msg = f"System uptime exceeded {self.UPTIME_THRESHOLD_HOURS} hours on {hostname}"
                    full_msg = (
                        f"The system '{hostname}' (IP: {self.get_ip_address()}) has been running for "
                        f"{current_uptime_hours} hours, which is above the {self.UPTIME_THRESHOLD_HOURS}-hour threshold. "
                        "Please investigate. This alert was triggered by the 'uptime_monitor_python.service' on the system."
                    )

                    custom_fields = {
                        "uptime_hours": current_uptime_hours,
                        "uptime_minutes": current_uptime_minutes,
                        "ip_address": self.get_ip_address(),
                        "alert_type": "uptime_threshold_exceeded",
                    }

                    self.send_gelf_message(short_msg, full_msg, level=3, custom_fields=custom_fields)

                    try:
                        with open(self.ALERT_FLAG_FILE, "w") as f:
                            f.write(str(current_uptime_minutes))
                        self.log_to_journal(f"[{hostname}] Created alert flag file: {self.ALERT_FLAG_FILE}")
                    except IOError as e:
                        self.log_to_journal(f"[{hostname}] Error creating alert flag file: {e}")
                else:
                    self.log_to_journal(
                        f"[{hostname}] Uptime threshold exceeded, but alert already sent for this uptime period. Skipping."
                    )
            else:
                self.log_to_journal(f"[{hostname}] Uptime is below threshold. No alert needed.")
                if os.path.exists(self.ALERT_FLAG_FILE):
                    try:
                        os.remove(self.ALERT_FLAG_FILE)
                        self.log_to_journal(
                            f"[{hostname}] Removed alert flag file: {self.ALERT_FLAG_FILE} as uptime is now below threshold."
                        )
                    except OSError as e:
                        self.log_to_journal(f"[{hostname}] Error removing alert flag file: {e}")

            time.sleep(self.CHECK_INTERVAL)

    def log_to_journal(self, message, level=logging.INFO):
        try:
            if level == logging.DEBUG:
                self.logger.debug(message)
            elif level == logging.INFO:
                self.logger.info(message)
            elif level == logging.WARNING:
                self.logger.warning(message)
            elif level == logging.ERROR:
                self.logger.error(message)
            elif level == logging.CRITICAL:
                self.logger.critical(message)
            else:
                self.logger.info(message)
        except Exception as e:
            print(f"Logging error: {e} - Original message: {message}")


if __name__ == "__main__":
    monitor = UptimeMonitorUseCase()
    monitor.monitor_uptime()
