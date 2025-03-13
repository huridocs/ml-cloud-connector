import os
import subprocess
import time


class AutomaticShutDownUseCase:
    GPU_MEMORY_THRESHOLD = 1000
    CPU_MEMORY_THRESHOLD = 10
    INACTIVITY_TIME_THRESHOLD = 300
    CHECK_INTERVAL = 5

    @staticmethod
    def get_gpu_memory_usage():
        try:
            output = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,nounits,noheader"])
        except FileNotFoundError:
            return 0
        return sum([int(memory) for memory in output.split()])

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

        if self.get_cpu_usage() > AutomaticShutDownUseCase.CPU_MEMORY_THRESHOLD:
            return True

        return False

    def automatic_shutdown(self):
        last_usage_time = time.time()

        while True:
            if self.is_vm_in_use():
                last_usage_time = time.time()
            else:
                idle_time = int(time.time() - last_usage_time)

                if idle_time > self.INACTIVITY_TIME_THRESHOLD:
                    print("Inactivity threshold reached. Shutting down...")
                    os.system("sudo shutdown now")

            time.sleep(self.CHECK_INTERVAL)