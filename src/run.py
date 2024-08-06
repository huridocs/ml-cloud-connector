from time import time

from ml_cloud_connector.MlCloudConnector import MlCloudConnector


def run():
    ml_cloud_connector = MlCloudConnector()
    for i in range(10):
        start = time()
        print("start")

        print(ml_cloud_connector.get_ip())
        print("time", round(time() - start, 2), "s")


if __name__ == '__main__':
    run()
