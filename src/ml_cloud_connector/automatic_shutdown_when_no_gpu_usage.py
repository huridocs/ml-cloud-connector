import subprocess
import time
import os

GPU_MEMORY_THRESHOLD = 1000
INACTIVITY_THRESHOLD = 300
CHECK_INTERVAL = 60


def get_gpu_memory_usage():
    try:
        output = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,nounits,noheader'])
    except FileNotFoundError:
        return 0
    return sum([int(memory) for memory in output.split()])


def is_gpu_in_use():
    return get_gpu_memory_usage() >= GPU_MEMORY_THRESHOLD


def automatic_shutdown():
    last_usage_time = time.time()

    while True:
        if is_gpu_in_use():
            last_usage_time = time.time()
        else:
            idle_time = int(time.time() - last_usage_time)

            if idle_time > INACTIVITY_THRESHOLD:
                print("Inactivity threshold reached. Shutting down...")
                os.system("sudo shutdown now")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    automatic_shutdown()
