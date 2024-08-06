import os
from math import floor
from time import sleep, time

import torch


def get_gb_gpu_memory_in_use() -> int:
    free_total_memory = torch.cuda.mem_get_info()
    return floor((free_total_memory[1] - free_total_memory[0]) / 1024 ** 3)


def is_gpu_in_use():
    if not torch.cuda.is_available():
        return False

    return get_gb_gpu_memory_in_use() >= 1


def automatic_shutdown():
    timestamp_last_gpu_usage = time()
    while True:
        if is_gpu_in_use():
            print("Waiting 5 more minutes")
            timestamp_last_gpu_usage = time()

        seconds_from_last_gpu_usage = round(time() - timestamp_last_gpu_usage)

        print("Seconds from last gpu usage", f"{seconds_from_last_gpu_usage}s")
        if seconds_from_last_gpu_usage > 300:
            os.system("sudo shutdown now")

        sleep(60)


if __name__ == "__main__":
    automatic_shutdown()
