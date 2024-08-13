from time import time

from ml_cloud_connector.MlCloudConnector import MlCloudConnector


def run():
    start = time()
    print("start")
    ml_cloud_connector = MlCloudConnector()

    print("time", round(time() - start, 2), "s")
    start = time()
    print(ml_cloud_connector.start())
    print("time", round(time() - start, 2), "s")


if __name__ == '__main__':
    run()
