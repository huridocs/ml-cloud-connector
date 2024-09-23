import time

from google.api_core.exceptions import GoogleAPICallError


def wait_for_operation(project, compute, operation, service_logger):
    service_logger.info("Waiting for operation to finish...")
    operation_name = operation["name"]

    if "zone" in operation:
        operation_scope = "zone"
        scope_name = operation["zone"].split("/")[-1]
    elif "region" in operation:
        operation_scope = "region"
        scope_name = operation["region"].split("/")[-1]
    else:
        operation_scope = "global"
        scope_name = None

    while True:
        if operation_scope == "zone":
            result = compute.zoneOperations().get(project=project, zone=scope_name, operation=operation_name).execute()
        elif operation_scope == "region":
            result = compute.regionOperations().get(project=project, region=scope_name, operation=operation_name).execute()
        else:
            result = compute.globalOperations().get(project=project, operation=operation_name).execute()

        if "error" in result:
            if result["error"]["errors"][0]["code"] == "ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS":
                raise GoogleAPICallError(result["error"])
            raise Exception(result["error"])

        if result["status"] == "DONE":
            service_logger.info("Operation completed.")
            if "error" in result:
                service_logger.info("Error in operation:", result["error"])
            break
        time.sleep(5)
