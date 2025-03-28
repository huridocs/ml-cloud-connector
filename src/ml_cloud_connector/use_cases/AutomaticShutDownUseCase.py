import logging
import os
import subprocess
import sys
import time


class AutomaticShutDownUseCase:
    GPU_MEMORY_THRESHOLD = int(os.environ.get("GPU_MEMORY_THRESHOLD", 10000))
    GPU_USAGE_THRESHOLD = int(os.environ.get("GPU_USAGE_THRESHOLD", 10))
    CPU_USAGE_THRESHOLD = int(os.environ.get("CPU_USAGE_THRESHOLD", 95))
    INACTIVITY_TIME_THRESHOLD = int(os.environ.get("INACTIVITY_TIME_THRESHOLD", 600))
    CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 30))
    DOCKER_CONTAINER_TO_FOLLOW = os.environ.get("DOCKER_CONTAINER_TO_FOLLOW", "")

    def __init__(self):
        self.logger = logging.getLogger("AutomaticShutDownUseCase")
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(fmt="%(asctime)s %(name)s.%(levelname)s: %(message)s", datefmt="%Y.%m.%d %H:%M:%S")
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.container_last_log = ""

    def is_docker_container_active(self):
        print(f"Checking if docker container {self.DOCKER_CONTAINER_TO_FOLLOW} is active")
        if self.DOCKER_CONTAINER_TO_FOLLOW == "":
            return False

        try:
            last_log = subprocess.check_output(["docker", "logs", "--tail", "1", self.DOCKER_CONTAINER_TO_FOLLOW]).decode()
            print(f"Last log: {last_log}")
            if last_log != self.container_last_log:
                self.container_last_log = last_log
                return True

        except subprocess.CalledProcessError as e:
            print(f"Error checking docker container: {e}")
            return False

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
            output = subprocess.check_output(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,nounits,noheader"])
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

    def is_vm_in_use(self) -> tuple[bool, str]:
        if self.is_docker_container_active():
            return True, f"Docker container is active, last log: {self.container_last_log}"

        if self.get_gpu_memory_usage() >= AutomaticShutDownUseCase.GPU_MEMORY_THRESHOLD:
            return True, f"GPU memory usage is above threshold {self.get_gpu_memory_usage()}"

        if self.get_gpu_utilization() > AutomaticShutDownUseCase.GPU_USAGE_THRESHOLD:
            return True, f"GPU utilization is above threshold {self.get_gpu_utilization()}"

        if self.get_cpu_usage() > AutomaticShutDownUseCase.CPU_USAGE_THRESHOLD:
            return True, f"CPU utilization is above threshold {self.get_cpu_usage()}"

        return False, ""

    def automatic_shutdown(self):
        last_usage_time = time.time()

        while True:
            is_in_use, reason = self.is_vm_in_use()
            if is_in_use:
                last_usage_time = time.time()
                self.log_to_journal(f"VM is in use. Reason: {reason}")
            else:
                self.log_to_journal("VM is NOT in use.")
                idle_time = int(time.time() - last_usage_time)
                if idle_time > self.INACTIVITY_TIME_THRESHOLD:
                    self.log_to_journal("Inactivity threshold reached. Shutting down...")
                    os.system("sudo shutdown now")

            time.sleep(self.CHECK_INTERVAL)

    def log_to_journal(self, message):
        try:
            self.logger.info(message)
        except:
            pass


if __name__ == "__main__":
    AutomaticShutDownUseCase().automatic_shutdown()
