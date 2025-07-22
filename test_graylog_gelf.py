#!/usr/bin/env python3
"""
Standalone test script for Graylog GELF message sending using graypy.
This script tests the GELF endpoint using the graypy library.
"""

import time
import subprocess
import os
import sys
import logging
import graypy


def get_hostname():
    """Get system hostname"""
    try:
        return subprocess.check_output(["hostname"]).decode().strip()
    except Exception as e:
        print(f"Error getting hostname: {e}")
        return "test-host"


def get_ip_address():
    """Get system IP address"""
    try:
        return subprocess.check_output(["hostname", "-I"]).decode().split()[0].strip()
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return "unknown-ip"


def test_graylog_connection(graylog_host, graylog_port):
    """Test basic connectivity to Graylog server using graypy"""
    print(f"Testing connection to Graylog at {graylog_host}:{graylog_port}...")

    try:
        # Create a test logger with graypy handler
        test_logger = logging.getLogger("graylog_connection_test")
        test_logger.setLevel(logging.INFO)

        # Clear any existing handlers
        test_logger.handlers.clear()

        # Add graypy handler
        graylog_handler = graypy.GELFUDPHandler(graylog_host, int(graylog_port))
        test_logger.addHandler(graylog_handler)

        # Try to send a test message
        test_logger.info(
            "Connection test message",
            extra={"test_type": "connection_test", "source_ip": get_ip_address(), "script_version": "1.0"},
        )

        print(f"✓ GELF handler created successfully for {graylog_host}:{graylog_port}")
        return True, test_logger

    except Exception as e:
        print(f"✗ Connection error: {e}")
        print(f"  Make sure:")
        print(f"  1. Graylog server is running on {graylog_host}")
        print(f"  2. GELF UDP input is configured on port {graylog_port}")
        print(f"  3. Firewall allows UDP connections to port {graylog_port}")
        print(f"  4. The host {graylog_host} is reachable from this machine")
        return False, None


def send_test_gelf_message(logger, test_name="Basic Test", level=logging.INFO):
    """Send a test GELF message to Graylog using graypy"""

    print(f"\nSending GELF message: {test_name}")

    try:
        message = f"Graylog Test Message - {test_name}"
        extra_fields = {
            "test_type": test_name.lower().replace(" ", "_"),
            "source_ip": get_ip_address(),
            "alert_source": "graylog_test_script",
            "script_version": "1.0",
            "timestamp_readable": time.strftime("%Y-%m-%d %H:%M:%S"),
            "hostname": get_hostname(),
        }

        if level == logging.ERROR:
            logger.error(message, extra=extra_fields)
        elif level == logging.WARNING:
            logger.warning(message, extra=extra_fields)
        else:
            logger.info(message, extra=extra_fields)

        print(f"✓ SUCCESS: {test_name} message sent")
        return True

    except Exception as e:
        print(f"✗ FAILED: Error sending {test_name} message: {e}")
        return False


def main():
    print("=" * 60)
    print("GRAYLOG GELF MESSAGE TEST SCRIPT (using graypy)")
    print("=" * 60)

    # Get configuration from environment or prompt user
    graylog_host = os.environ.get("GRAYLOG_HOST")
    graylog_port = os.environ.get("GRAYLOG_PORT", "12201")

    if not graylog_host:
        print("\nGRAYLOG_HOST environment variable not set.")
        graylog_host = input("Enter Graylog server IP/hostname: ").strip()
        if not graylog_host:
            print("Error: Graylog host is required")
            sys.exit(1)

    print(f"\nConfiguration:")
    print(f"  Graylog Host: {graylog_host}")
    print(f"  Graylog Port: {graylog_port} (UDP)")
    print(f"  Test Host: {get_hostname()}")
    print(f"  Test IP: {get_ip_address()}")

    # Test 1: Basic connectivity
    print(f"\n{'='*40}")
    print("TEST 1: Basic Connectivity")
    print(f"{'='*40}")
    success, logger = test_graylog_connection(graylog_host, graylog_port)
    if not success:
        print("\nCannot proceed with GELF tests - connection failed")
        sys.exit(1)

    # Test 2: Send basic GELF message
    print(f"\n{'='*40}")
    print("TEST 2: Basic GELF Message (INFO)")
    print(f"{'='*40}")
    success1 = send_test_gelf_message(logger, "Basic Info Test", logging.INFO)

    # Test 3: Send warning level message
    print(f"\n{'='*40}")
    print("TEST 3: Warning Level Message")
    print(f"{'='*40}")
    success2 = send_test_gelf_message(logger, "Warning Test", logging.WARNING)

    # Test 4: Send error level message
    print(f"\n{'='*40}")
    print("TEST 4: Error Level Message")
    print(f"{'='*40}")
    success3 = send_test_gelf_message(logger, "Error Test", logging.ERROR)

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    total_tests = 3
    passed_tests = sum([success1, success2, success3])

    print(f"Tests passed: {passed_tests}/{total_tests}")

    if passed_tests == total_tests:
        print("✓ ALL TESTS PASSED - Graylog GELF endpoint is working correctly!")
    else:
        print(f"✗ {total_tests - passed_tests} TESTS FAILED - Check Graylog configuration")

    print(f"\nTo check messages in Graylog:")
    print(f"1. Open Graylog web interface")
    print(f"2. Search for: _alert_source:graylog_test_script")
    print(f"3. Or search for: source:{get_hostname()}")
    print(f"4. Look for messages from the last few minutes")

    # Give some time for messages to be processed
    print(f"\nNote: Messages may take a few seconds to appear in Graylog")


if __name__ == "__main__":
    main()
