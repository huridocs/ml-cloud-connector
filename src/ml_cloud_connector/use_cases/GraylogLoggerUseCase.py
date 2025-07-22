import requests
import json
import socket  # To get hostname and IP, and for UDP sending
import time  # To get timestamp
import os  # For environment variables


class GraylogLoggerUseCase:
    GRAYLOG_HOST = os.environ.get("GRAYLOG_HOST", "setup_ip")
    GRAYLOG_PORT = int(os.environ.get("GRAYLOG_PORT", "12201"))
    SOURCE = os.environ.get("GRAYLOG_SOURCE", "pdf_metadata_extraction")

    # Syslog severity levels mapping
    # 0: Emergency, 1: Alert, 2: Critical, 3: Error, 4: Warning, 5: Notice, 6: Informational, 7: Debug
    LOG_LEVELS = {"DEBUG": 7, "INFO": 6, "NOTICE": 5, "WARNING": 4, "ERROR": 3, "CRITICAL": 2, "ALERT": 1, "EMERGENCY": 0}

    def __init__(self, graylog_host=None, graylog_port=None):
        self.graylog_host = graylog_host if graylog_host else self.GRAYLOG_HOST
        self.graylog_port = graylog_port if graylog_port else self.GRAYLOG_PORT

        self.graylog_url = f"http://{self.graylog_host}:{self.graylog_port}/gelf"
        self.source = self.SOURCE
        self.ip_address = self._get_local_ip()

        if self.graylog_host == "your_graylog_server_ip_or_hostname":
            print("WARNING: Graylog host is not configured. Please update GRAYLOG_HOST in the script or environment.")
            print("Logs will attempt to send to the default placeholder address.")

    @staticmethod
    def _get_local_ip():
        """Attempts to get the local machine's IP address."""
        try:
            # Create a socket connection to an external server (doesn't actually send data)
            # This is a common trick to get the local IP used for outbound connections.
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Google DNS server
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"  # Fallback to loopback if unable to determine

    def _prepare_gelf_payload(self, short_message, full_message, level, facility, **kwargs):
        """Helper to construct the GELF JSON payload."""
        gelf_level = self.LOG_LEVELS.get(level.upper(), 6)  # Default to INFO if level is unknown

        payload = {
            "version": "1.1",
            "host": self.source,
            "short_message": short_message,
            "full_message": full_message,
            "timestamp": time.time(),  # Current Unix timestamp
            "level": gelf_level,
            "facility": facility,
        }

        # Add custom fields from kwargs, ensuring they are prefixed with '_'
        for key, value in kwargs.items():
            if not key.startswith("_"):
                payload[f"_{key}"] = value
            else:
                payload[key] = value  # If already prefixed, use as is

        return payload

    def _send_gelf_udp(self, payload):
        """Sends a GELF message to Graylog via UDP."""
        try:
            # GELF UDP messages are simply the JSON payload sent as a UDP packet
            message = json.dumps(payload).encode("utf-8")

            # Create a UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Send data to the Graylog server
            sock.sendto(message, (self.graylog_host, self.graylog_port))
            sock.close()
            print(f"Successfully sent '{payload.get('level')}' log to Graylog via UDP: '{payload.get('short_message')}'")
        except socket.gaierror:
            print(f"Error (UDP): Hostname '{self.graylog_host}' could not be resolved.")
        except ConnectionRefusedError:
            print(f"Error (UDP): Connection refused. Check Graylog UDP input and firewall.")
        except Exception as e:
            print(f"An unexpected error occurred while sending log via UDP: {e}")

    def send_log(self, short_message, full_message="", level="INFO", facility="python_app", **kwargs):
        """
        Sends a GELF log message to Graylog using the configured protocol.

        Args:
            short_message (str): A short, single-line message.
            full_message (str, optional): A long message that can contain more details.
            level (str, optional): The severity level of the log (e.g., "INFO", "ERROR").
                                   Defaults to "INFO".
            facility (str, optional): The facility or application name. Defaults to "python_app".
            **kwargs: Additional custom fields to be sent to Graylog.
                      These will be prefixed with an underscore automatically.
        """
        payload = self._prepare_gelf_payload(short_message, full_message, level, facility, **kwargs)
        self._send_gelf_udp(payload)


if __name__ == "__main__":
    # Example usage
    graylog_logger = GraylogLoggerUseCase()

    # Sending a test log message
    graylog_logger.send_log(
        short_message="Test log message",
        full_message="This is a detailed message for testing purposes.",
        level="INFO",
        facility="test_script",
        custom_field1="value1",
        custom_field2="value2",
    )
