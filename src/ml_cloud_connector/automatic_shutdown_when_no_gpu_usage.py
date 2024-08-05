import os
import time
from math import floor

import torch


def get_gb_gpu_memory_in_use() -> int:
    free_total_memory = torch.cuda.mem_get_info()
    return floor((free_total_memory[1] - free_total_memory[0]) / 1024 ** 3)


def check_gpu_usage():
    if not torch.cuda.is_available():
        return False

    return get_gb_gpu_memory_in_use() >= 1


def initiate_shutdown():
    print("Shutting down in 30 minutes")
    os.system("sudo shutdown -c")
    os.system("sudo shutdown +10")


def automatic_shutdown():
    while True:
        if not check_gpu_usage():
            initiate_shutdown()
        time.sleep(300)  # Check every 5 minutes


if __name__ == "__main__":
    automatic_shutdown()