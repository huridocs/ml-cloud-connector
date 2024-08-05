import os
from os.path import join
from pathlib import Path
from crontab import CronTab
from ml_cloud_connector.configuration import ROOT_PATH, SERVICE_PATH


def get_post_start_script():
    post_installation_script = f"#!/bin/bash\n"
    with open(join(ROOT_PATH, "requirements.txt")) as f:
        requirements = f.read().splitlines()

        for requirement in requirements:
            post_installation_script += f"pip install {requirement}\n"

    automatic_shutdown_script_path = join(ROOT_PATH, 'src', 'ml_cloud_connector',
                                          "automatic_shutdown_when_no_gpu_usage.py")
    post_installation_script += f"nohup python3 {automatic_shutdown_script_path} &\n"
    post_installation_script += f"cd {SERVICE_PATH} ; make start_detached\n"
    return post_installation_script


def create_post_start_script():
    path = Path(ROOT_PATH, "post_start_script.sh")
    path.write_text(get_post_start_script())
    os.system(f"chmod +x {path}")
    cron = CronTab(user=True)
    job = cron.new(command=f"{path}")
    job.every_reboot()
    cron.write()


if __name__ == '__main__':
    create_post_start_script()