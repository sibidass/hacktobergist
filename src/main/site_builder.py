from time import sleep
import toml

from utils.logger import get_logger
from jobs import ALL_LANG, SiteUpdaterIssueJob

log = get_logger(__name__)

def main():
    log.info("Fetching issues from DB")
    update_job = SiteUpdaterIssueJob(ALL_LANG, "open")

    update_job.run()


if __name__ == '__main__':
    main()

