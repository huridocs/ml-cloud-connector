import subprocess
import time
import os

GPU_MEMORY_THRESHOLD = 1000
INACTIVITY_TIME_THRESHOLD = 300
CHECK_INTERVAL = 5


def get_gpu_memory_usage():
    try:
        output = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,nounits,noheader"])
    except FileNotFoundError:
        return 0
    return sum([int(memory) for memory in output.split()])


def get_cpu_usage():
    try:
        output = subprocess.check_output(["top", "-bn1"])
    except FileNotFoundError:
        return 0
    return float(output.split(b"%Cpu(s):")[1].split(b"us")[0])


def is_vm_in_use():
    if get_gpu_memory_usage() >= GPU_MEMORY_THRESHOLD:
        return True

    if get_cpu_usage() > 10:
        return True

    return False


def automatic_shutdown():
    last_usage_time = time.time()

    while True:
        if is_vm_in_use():
            last_usage_time = time.time()
        else:
            idle_time = int(time.time() - last_usage_time)

            if idle_time > INACTIVITY_TIME_THRESHOLD:
                print("Inactivity threshold reached. Shutting down...")
                os.system("sudo shutdown now")

        time.sleep(CHECK_INTERVAL)
