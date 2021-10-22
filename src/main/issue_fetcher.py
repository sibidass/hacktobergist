import toml

from scheduler import Scheduler
from utils.logger import get_logger
from jobs import IssueFetcherJob, ALL_LANG

log = get_logger(__name__)
config_file = "config.toml"
schedule_config = toml.load(config_file)["scheduled_jobs"]

def handler(event, context):
    lang = event.get("languages_rem", ALL_LANG)
    job = IssueFetcherJob(issue_fetcher_config["start_date"], datetime.now().strftime("%Y-%m-%d"), context, *lang)
    job_resp = job.run()
    if job_resp.get("status") == "complete":
        return {
            "status": job_resp.get("status"),
            "message": "Issues successfully fetched from github"
        }
    else:
        log.info("Languages processed: {}".format(
                                                   job_resp.get("languages_processed")))

        lang_to_process = [l for l in lang if l not in job_resp.get("languages_processed")]

        # TO DO:
        # invoke lambda for remaining languages
        return {
            "status": job_resp.get("status"),
            "total": ALL_LANG,
            "curr_processed": job_resp.get("languages_processed"),
            "pending": lang_to_process,
            "message": "task partially completed"
        }


