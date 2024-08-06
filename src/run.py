from ml_cloud_connector.MlCloudConnector import MlCloudConnector


def run():
    ml_cloud_connector = MlCloudConnector()
    ml_cloud_connector.start()


if __name__ == '__main__':
    run()
