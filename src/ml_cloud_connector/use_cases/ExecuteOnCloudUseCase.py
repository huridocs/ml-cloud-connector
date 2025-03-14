import logging
import time

from httpx import HTTPStatusError, RemoteProtocolError, ConnectError
from requests import ConnectTimeout, ReadTimeout

from ml_cloud_connector.domain.RestCall import RestCall
from ml_cloud_connector.ports.CloudProviderRepository import CloudProviderRepository


class ExecuteOnCloudUseCase:
    def __init__(self, cloud_provider: CloudProviderRepository, service_logger: logging.Logger):
        self.cloud_provider = cloud_provider
        self.service_logger = service_logger

    def execute(self, rest_call: RestCall) -> (any, bool, str):
        connection_wait_time = 0
        reconnect_trial_count = 0
        request_trial_count = 0
        reconnect = False

        while reconnect_trial_count < 10:
            try:
                if reconnect:
                    self.cloud_provider.restart()
                    time.sleep(connection_wait_time)
                else:
                    self.cloud_provider.start()

                ip = self.cloud_provider.get_ip()
                response = rest_call.make_request(ip)
                return response.json(), True, ""
            except (ConnectError, ReadTimeout) as e:
                if request_trial_count == 20:
                    return None, False, "There is a problem with getting the response."
                self.service_logger.warning(f"{e} Retrying in 30 seconds.. [Trial: {request_trial_count + 1}]")
                time.sleep(30)
                request_trial_count += 1
            except (ConnectionError, ConnectTimeout, HTTPStatusError, RemoteProtocolError, KeyError) as e:
                self.service_logger.error(f"{e} Retrying... [Trial: {reconnect_trial_count + 1}]")
                connection_wait_time = connection_wait_time * 1.5 if connection_wait_time else 150
                if connection_wait_time > 900:
                    connection_wait_time = 900
                time.sleep(30)
                reconnect = True
                reconnect_trial_count += 1
            except Exception as e:
                self.service_logger.error(f"{e} Server error.")
                return None, False, "Server error." + str(e)
        return None, False, "Response not returned. Server error."
