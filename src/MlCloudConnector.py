class MlCloudConnector:
    def __init__(self, cloud_provider):
        self.cloud_provider = cloud_provider

    def connect(self):
        if self.cloud_provider == "aws":
            return "Connecting to AWS"
        elif self.cloud_provider == "azure":
            return "Connecting to Azure"
        elif self.cloud_provider == "gcp":
            return "Connecting to GCP"
        else:
            return "Invalid cloud provider"