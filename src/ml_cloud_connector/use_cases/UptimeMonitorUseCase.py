import logging
import logging.handlers
import os
import subprocess
import time
from ml_cloud_connector.use_cases.GraylogLoggerUseCase import GraylogLoggerUseCase


class UptimeMonitorUseCase:
    GRAYLOG_HOST = os.environ.get("GRAYLOG_HOST", "your_graylog_server_ip_or_hostname")
    GRAYLOG_PORT = os.environ.get("GRAYLOG_PORT", "12201")
    UPTIME_THRESHOLD_HOURS = int(os.environ.get("UPTIME_THRESHOLD_HOURS", 20))
    CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 300))
    SOURCE = os.environ.get("SOURCE", "pdf_metadata_extraction")

    def __init__(self):
        self.journal_logger = self._setup_journal_logger()
        self.graylog_logger = GraylogLoggerUseCase()
        self.threshold_exceeded = False
        self.last_alert_hour = None
        self.initial_alert_sent = False

    @staticmethod
    def _setup_journal_logger():
        logger = logging.getLogger("UptimeMonitor_Journal")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            try:
                journal_handler = logging.handlers.SysLogHandler(address="/dev/log")
                journal_handler.setFormatter(logging.Formatter("UptimeMonitor: %(message)s"))
                logger.addHandler(journal_handler)
            except Exception:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(logging.Formatter("%(asctime)s - UptimeMonitor: %(message)s"))
                logger.addHandler(console_handler)
        return logger

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
    def get_ip_address():
        try:
            return subprocess.check_output(["hostname", "-I"]).decode().split()[0].strip()
        except Exception as e:
            logging.error(f"Error getting IP address: {e}")
            return "unknown_ip"

    def send_gelf_message(self, short_message, full_message, level=3, custom_fields=None):
        """Send GELF message to Graylog using GraylogLoggerUseCase"""
        if custom_fields is None:
            custom_fields = {}
        level_str = "ERROR" if level <= 3 else "INFO"
        try:
            self.graylog_logger.send_log(
                short_message, full_message, level=level_str, facility="uptime_monitor_python", **custom_fields
            )
            self.journal_logger.info(f"Successfully sent GELF message to Graylog: {short_message}")
        except Exception as e:
            self.journal_logger.error(f"Failed to send GELF message to Graylog: {e}")

    def monitor_uptime(self):
        self.log_to_journal("Starting Uptime Monitor Service...")
        uptime_threshold_minutes = self.UPTIME_THRESHOLD_HOURS * 60

        while True:
            current_uptime_minutes = self.get_system_uptime_minutes()
            current_uptime_hours = int(current_uptime_minutes / 60)

            self.log_to_journal(
                f"[UptimeMonitorUseCase] Current uptime: {current_uptime_hours} hours ({current_uptime_minutes} minutes)"
            )

            if current_uptime_minutes > uptime_threshold_minutes:
                should_send_alert = False

                if not self.initial_alert_sent:
                    self.log_to_journal(
                        f"[UptimeMonitorUseCase] Uptime threshold exceeded! Sending initial alert to Graylog."
                    )
                    should_send_alert = True
                    self.initial_alert_sent = True
                    self.threshold_exceeded = True
                    self.last_alert_hour = current_uptime_hours
                else:
                    if self.last_alert_hour is None or current_uptime_hours >= self.last_alert_hour + 1:
                        self.log_to_journal(
                            f"[UptimeMonitorUseCase] One hour passed since last alert. Sending hourly alert to Graylog."
                        )
                        should_send_alert = True
                        self.last_alert_hour = current_uptime_hours
                    else:
                        self.log_to_journal(
                            f"[UptimeMonitorUseCase] Uptime threshold exceeded, but hourly alert not due yet."
                        )

                if should_send_alert:
                    short_msg = f"System uptime exceeded {self.UPTIME_THRESHOLD_HOURS} hours on UptimeMonitorUseCase"
                    full_msg = (
                        f"The system 'UptimeMonitorUseCase' (IP: {self.get_ip_address()}) has been running for "
                        f"{current_uptime_hours} hours, which is above the {self.UPTIME_THRESHOLD_HOURS}-hour threshold. "
                        f"Please investigate. This alert was triggered by the 'uptime_monitor_python.service' on the system."
                    )

                    custom_fields = {
                        "uptime_hours": current_uptime_hours,
                        "uptime_minutes": current_uptime_minutes,
                        "ip_address": self.get_ip_address(),
                        "alert_type": "uptime_threshold_exceeded",
                        "threshold_hours": self.UPTIME_THRESHOLD_HOURS,
                    }

                    self.send_gelf_message(short_msg, full_msg, level=3, custom_fields=custom_fields)
            else:
                if self.threshold_exceeded:
                    self.log_to_journal(f"[UptimeMonitorUseCase] Uptime is now below threshold. Resetting alert state.")
                    self.threshold_exceeded = False
                    self.initial_alert_sent = False
                    self.last_alert_hour = None
                else:
                    self.log_to_journal(f"[UptimeMonitorUseCase] Uptime is below threshold. No alert needed.")

            time.sleep(self.CHECK_INTERVAL)

    def log_to_journal(self, message, level=logging.INFO):
        try:
            if level == logging.DEBUG:
                self.journal_logger.debug(message)
            elif level == logging.INFO:
                self.journal_logger.info(message)
            elif level == logging.WARNING:
                self.journal_logger.warning(message)
            elif level == logging.ERROR:
                self.journal_logger.error(message)
            elif level == logging.CRITICAL:
                self.journal_logger.critical(message)
            else:
                self.journal_logger.info(message)
        except Exception as e:
            print(f"Logging error: {e} - Original message: {message}")


if __name__ == "__main__":
    monitor = UptimeMonitorUseCase()
    monitor.monitor_uptime()
