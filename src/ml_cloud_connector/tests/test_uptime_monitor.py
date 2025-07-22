#!/usr/bin/env python3

import sys
import os
import tempfile
import unittest
from unittest.mock import patch, mock_open, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from ml_cloud_connector.use_cases.UptimeMonitorUseCase import UptimeMonitorUseCase


class TestUptimeMonitorUseCase(unittest.TestCase):

    def setUp(self):
        self.monitor = UptimeMonitorUseCase()

    def test_get_system_uptime_minutes(self):
        """Test that uptime reading works correctly"""
        with patch("builtins.open", mock_open(read_data="86400.0 43200.0\n")):
            uptime = UptimeMonitorUseCase.get_system_uptime_minutes()
            self.assertEqual(uptime, 1440)  # 86400 seconds = 1440 minutes

    def test_get_hostname(self):
        """Test hostname retrieval"""
        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = b"test-hostname\n"
            hostname = UptimeMonitorUseCase.get_hostname()
            self.assertEqual(hostname, "test-hostname")

    def test_get_ip_address(self):
        """Test IP address retrieval"""
        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = b"192.168.1.100 10.0.0.1\n"
            ip = UptimeMonitorUseCase.get_ip_address()
            self.assertEqual(ip, "192.168.1.100")

    @patch("requests.post")
    def test_send_gelf_message_success(self, mock_post):
        """Test successful GELF message sending"""
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_post.return_value = mock_response

        with (
            patch.object(self.monitor, "get_hostname", return_value="test-host"),
            patch.object(self.monitor, "get_ip_address", return_value="192.168.1.100"),
        ):

            self.monitor.send_gelf_message("Test message", "Full test message")

            # Verify the request was made
            self.assertTrue(mock_post.called)
            call_args = mock_post.call_args

            # Check URL
            expected_url = f"http://{self.monitor.GRAYLOG_HOST}:{self.monitor.GRAYLOG_PORT}/gelf"
            self.assertEqual(call_args[0][0], expected_url)

            # Check headers
            self.assertEqual(call_args[1]["headers"]["Content-Type"], "application/json")

    @patch("requests.post")
    def test_send_gelf_message_failure(self, mock_post):
        """Test GELF message sending failure"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with (
            patch.object(self.monitor, "get_hostname", return_value="test-host"),
            patch.object(self.monitor, "get_ip_address", return_value="192.168.1.100"),
        ):

            # This should not raise an exception but should log an error
            self.monitor.send_gelf_message("Test message", "Full test message")

            self.assertTrue(mock_post.called)

    def test_error_handling_uptime(self):
        """Test error handling for uptime reading"""
        with patch("builtins.open", side_effect=FileNotFoundError):
            uptime = UptimeMonitorUseCase.get_system_uptime_minutes()
            self.assertEqual(uptime, 0)

    def test_error_handling_hostname(self):
        """Test error handling for hostname retrieval"""
        with patch("subprocess.check_output", side_effect=Exception("Command failed")):
            hostname = UptimeMonitorUseCase.get_hostname()
            self.assertEqual(hostname, "unknown_host")

    def test_error_handling_ip(self):
        """Test error handling for IP address retrieval"""
        with patch("subprocess.check_output", side_effect=Exception("Command failed")):
            ip = UptimeMonitorUseCase.get_ip_address()
            self.assertEqual(ip, "unknown_ip")


if __name__ == "__main__":
    unittest.main()
