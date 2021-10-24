from datetime import datetime
import json

import boto3
from src.main.utils.logger import get_logger
from src.main.jobs import IssueFetcherJob, ALL_LANG, config

log = get_logger(__name__)
schedule_config = config["scheduled_jobs"]
issue_fetcher_config = schedule_config["issue_fetcher"]

lambda_client = boto3.client("lambda")

def handler(event, context):
    lang = event.get("languages", ALL_LANG)
    start_date = issue_fetcher_config["start_date"]
    job = IssueFetcherJob(start_date, datetime.now().strftime("%Y-%m-%d"), context, *lang)
    job_resp = job.run()
    if job_resp.get("status") == "complete":
        return {
            "status": job_resp.get("status"),
            "message": "Issues successfully fetched from github"
        }
    log.info("Processed Info: {}".format(job_resp.get("process_info")))

    # invoke lambda for remaining languages
    resp = lambda_client.invoke(
                              FunctionName=context.function_name,
                              InvocationType='Event',
                              Payload=json.dumps(event).encode()
                              )
    log.info("New lambda invoked with the payload: {}".format(json.dumps(event)))
    return {
        "status": job_resp.get("status"),
        "total": lang,
        "process_info": job_resp.get("process_info"),
        "message": "task partially completed"
    }
