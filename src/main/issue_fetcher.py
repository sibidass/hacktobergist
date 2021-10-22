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
    lang = event.get("languages_rem", ALL_LANG)
    start_date = issue_fetcher_config["start_date"]
    lang_start_date = event.get("lang_start_date")
    job = IssueFetcherJob(start_date, datetime.now().strftime("%Y-%m-%d"), context, *lang)
    job_resp = job.run(l_start_date=lang_start_date)
    if job_resp.get("status") == "complete":
        return {
            "status": job_resp.get("status"),
            "message": "Issues successfully fetched from github"
        }
    else:
        log.info("Languages processed: {}".format(
                                                   job_resp.get("languages_processed")))

        lang_to_process = [l for l in lang if l not in job_resp.get("languages_processed")]
        day = job_resp.get("dated")

        new_event = {
            "languages_rem": lang_to_process,
            "lang_start_date": day
        }

        # invoke lambda for remaining languages
        resp = lambda_client.invoke_async(
                                  FunctionName=context.function_name,
                                  InvokeArgs=json.dumps(new_event).encode()
                                  )
        log.info("New lambda invoked with the payload: {}".format(json.dumps(new_event)))
        log.info("Invoke response: {}".format(json.dumps(resp)))
        return {
            "status": job_resp.get("status"),
            "total": list(ALL_LANG),
            "curr_processed": job_resp.get("languages_processed"),
            "pending": lang_to_process,
            "message": "task partially completed"
        }
