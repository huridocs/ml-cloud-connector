import logging
import time
from typing import Optional

import requests
from requests import ReadTimeout, Response

from ml_cloud_connector.domain.RestCall import RestCall
from ml_cloud_connector.ports.ServerlessProviderRepository import ServerlessProviderRepository


class ExecuteOnServerlessUseCase:
    def __init__(self, serverless_provider: ServerlessProviderRepository, service_logger: logging.Logger):
        self.serverless_provider = serverless_provider
        self.service_logger = service_logger

    def execute(self, rest_call: RestCall) -> tuple[Optional[Response], bool, str]:
        request_trial_count = 0
        self.service_logger.info(f"Serverless Connector: {rest_call}")

        while request_trial_count < 5:
            try:
                response = self.serverless_provider.make_request(rest_call)
                return response, True, ""
            except (
                requests.exceptions.InvalidURL,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                ReadTimeout,
            ) as e:
                if request_trial_count == 4:
                    return None, False, "There is a problem with getting the response."
                self.service_logger.warning(f"{e} {rest_call} Retrying in 30 seconds.. [Trial: {request_trial_count + 1}]")
                time.sleep(30)
                request_trial_count += 1
            except Exception as e:
                self.service_logger.error(f"{e} {rest_call} Server error.")
                return None, False, "Server error." + str(e)
        return None, False, "Response not returned. Server error."
