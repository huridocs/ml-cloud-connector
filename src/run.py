from time import time

from ml_cloud_connector.MlCloudConnector import MlCloudConnector
from ml_cloud_connector.ServerType import ServerType


def run():
    start = time()
    print("start")
    MlCloudConnector.forget_cloud_instance()
    ml_cloud_connector = MlCloudConnector(ServerType.TRANSLATION)
    print("time", round(time() - start, 2), "s")
    start = time()
    print(ml_cloud_connector.get_ip())
    print("time", round(time() - start, 2), "s")


if __name__ == "__main__":
    run()
