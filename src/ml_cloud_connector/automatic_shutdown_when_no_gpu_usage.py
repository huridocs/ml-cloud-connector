import os
import time
from math import floor
from pathlib import Path

import torch


def get_gb_gpu_memory_in_use() -> int:
    free_total_memory = torch.cuda.mem_get_info()
    return floor((free_total_memory[1] - free_total_memory[0]) / 1024 ** 3)


def check_gpu_usage():
    if not torch.cuda.is_available():
        return False

    return get_gb_gpu_memory_in_use() >= 1


def initiate_shutdown():
    print("Shutting down in 10 minutes")
    os.system("sudo shutdown +10")


def automatic_shutdown():
    while True:
        exists_shutdown_scheduled = Path("/run/systemd/shutdown/scheduled").exists()
        if not check_gpu_usage() and not exists_shutdown_scheduled:
            initiate_shutdown()
        else:
            os.system("sudo shutdown -c")

        time.sleep(300)  # Check every 5 minutes


if __name__ == "__main__":
    automatic_shutdown()
