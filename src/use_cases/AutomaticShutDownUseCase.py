import os
import subprocess
import time

import systemd.journal


class AutomaticShutDownUseCase:
    GPU_MEMORY_THRESHOLD = 10000
    GPU_USAGE_THRESHOLD = 10
    CPU_USAGE_THRESHOLD = 95
    INACTIVITY_TIME_THRESHOLD = 30
    CHECK_INTERVAL = 5

    @staticmethod
    def get_gpu_memory_usage():
        try:
            output = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,nounits,noheader"])
        except FileNotFoundError:
            return 0
        return sum([int(memory) for memory in output.split()])

    @staticmethod
    def get_gpu_utilization():
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,nounits,noheader"])
            return int(output.strip())
        except FileNotFoundError:
            return 0

    @staticmethod
    def get_cpu_usage():
        try:
            output = subprocess.check_output(["top", "-bn1"])
        except FileNotFoundError:
            return 0
        return float(output.split(b"%Cpu(s):")[1].split(b"us")[0])

    def is_vm_in_use(self):
        if self.get_gpu_memory_usage() >= AutomaticShutDownUseCase.GPU_MEMORY_THRESHOLD:
            return True

        if self.get_gpu_utilization() > AutomaticShutDownUseCase.GPU_USAGE_THRESHOLD:
            return True

        if self.get_cpu_usage() > AutomaticShutDownUseCase.CPU_USAGE_THRESHOLD:
            return True

        return False

    def automatic_shutdown(self):
        last_usage_time = time.time()

        while True:
            if self.is_vm_in_use():
                last_usage_time = time.time()
                print("VM is in use.")
                self.log_to_journal("VM is in use.")
            else:
                print("VM is NOT in use.")
                self.log_to_journal("VM is NOT in use.")
                idle_time = int(time.time() - last_usage_time)
                if idle_time > self.INACTIVITY_TIME_THRESHOLD:
                    print("Inactivity threshold reached. Shutting down...")
                    self.log_to_journal("Inactivity threshold reached. Shutting down...")
                    os.system("sudo shutdown now")

            time.sleep(self.CHECK_INTERVAL)

    @staticmethod
    def log_to_journal(message, priority=systemd.journal.LOG_INFO):
        """Logs a message to the systemd journal."""
        with systemd.journal.JournalHandler() as journal:
            journal.send(message, PRIORITY=priority)

if __name__ == '__main__':
    AutomaticShutDownUseCase().automatic_shutdown()