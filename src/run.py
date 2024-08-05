from time import time

from ml_cloud_connector.MlCloudConnector import MlCloudConnector


def run():
    ml_cloud_connector = MlCloudConnector()
    start = time()
    print(ml_cloud_connector.stop())
    print(ml_cloud_connector.get_ip())
    print("time", round(time() - start, 2), "s")


if __name__ == '__main__':
    run()
