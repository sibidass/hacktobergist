from datetime import datetime
from time import sleep
import toml

from scheduler import Scheduler
from utils.logger import get_logger
from jobs import IssueFetcherJob, ALL_LANG, SiteUpdaterIssueJob


log = get_logger(__name__)
config_file = "config.toml"
schedule_config = toml.load(config_file)["scheduled_jobs"]


def main():
    log.info("Creating scheduled jobs")
    issue_fetcher_config = schedule_config["issue_fetcher"]
    siteupdater_issue_config = schedule_config["site_updater_issue"]
    jobs = {}
    jobs.update({
                IssueFetcherJob(issue_fetcher_config["start_date"], datetime.now().strftime("%Y-%m-%d"), *ALL_LANG): issue_fetcher_config["schedule"],
                SiteUpdaterIssueJob(["Python"]): siteupdater_issue_config["schedule"]
                })
    scheduled_jobs = []
    for job, job_time in jobs.items():
        scheduled_jobs.append(Scheduler(job, job_time))

    for sch in scheduled_jobs:
        print(sch.time)
        print(datetime.now().strftime("%H:%M"))
        if sch.time == datetime.now().strftime("%H:%M"):
            log.info("running the job {}".format(sch.job))
            sch.run()


if __name__ == '__main__':
    main()
