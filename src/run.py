from time import time, sleep

from ml_cloud_connector.MlCloudConnector import MlCloudConnector


def run():
    ml_cloud_connector = MlCloudConnector()
    start = time()
    ml_cloud_connector.restart()

    for i in range(1000):
        print(ml_cloud_connector.is_active())
        sleep(10)
    print("time", round(time() - start, 2), "s")


if __name__ == '__main__':
    run()
