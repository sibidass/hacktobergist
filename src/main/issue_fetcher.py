from datetime import datetime, timedelta
import json
import os

import boto3
from src.main.utils.logger import get_logger
from src.main.utils.db import DB
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
    else:
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

def handler_new(event, context):
    day = json.loads(event.get("Records")[0]["body"]).get("day")
    filters = Event(day).format()
    if not filters:
        next_day = datetime.strptime(day, "%Y-%m-%d")+timedelta(days=1)
        if next_day > datetime.now():
            log.info("process completed"):
            return {
                "status": "complete"
            }
        else:
            log.info("all languages processed for {}".format(day))
            # send sqs
            send_msg({"day": next_day})
            return {
                "status": "InProgress",
                "ToProcess": next_day
            }

    job = IssueFetcherJobLean(**filters)
    try:
        job.run()
        db = DB("DataProcessed")
        db.put({
               "language": filters.get("language"),
               "date": day,
               "processed": True
               "processed_on": datetime.now().strftime("%Y-%m-%d")
               })
    except Exception as e:
        log.error("Error processing {} for {}".format(filters.get("language"), day))
    send_msg({"day": day})
    return {
        "status": "InProgress",
        "ToProcess": day
    }

def send_msg(message):
    sqs = boto3.client("sqs")
    sqs.send_message(
                     QueueUrl=os.environ.get("QueueUrl"),
                     MessageBody=message
                     )


class Event(object):
    """docstring for Event"""
    def __init__(self, date):
        self.date = date

    def format(self):
        if not self._validate_date():
            raise Exception("date {} entered is greater than current date {}".format(self.date, datetime.now().strftime("%Y-%m-%d")))
        # pick a lang
        lang = self._lang_picker()
        if lang:
            filters = {
            "language": lang,
            "qualifiers": {
            "updated": "{}..{}".format(date, date)
            }
            }
            return filters

    def _lang_picker(self):
        for lang in ALL_LANG:
            db = DB("DataProcessed")
            item = db.get_item({
                   "language": lang,
                   "date": self.date
                   })
            if item and item.get("processed"):
                continue
            return lang


    def _validate_date(self):
        return datetime.strptime(self.date, "%Y-%m-%d") <= datetime.now()



