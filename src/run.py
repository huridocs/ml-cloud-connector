from time import sleep

from ml_cloud_connector.MlCloudConnector import MlCloudConnector


def run():
    ml_cloud_connector = MlCloudConnector()
    print(ml_cloud_connector.get_ip())

    # for i in range(1000):
    #     if ml_cloud_connector.is_active():
    #         print("Instance is active")
    #     else:
    #         print("Instance is not active")
    #     sleep(10)


if __name__ == '__main__':
    run()
