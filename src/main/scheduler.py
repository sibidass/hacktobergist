import logging
import os
from datetime import datetime, timedelta
import json
import sys

from utils.issues import get_issues
from utils.db import DB
from utils.client import IssueFetch
from utils.logger import get_logger
from jobs import IssueFetcherJob


LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").upper()
SH = logging.StreamHandler(stream=sys.stdout)
fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s:%(message)s")
SH.setFormatter(fmt)
log = logging.getLogger(__name__)
log.setLevel(LOG_LEVEL)
log.addHandler(SH)
start_date = "2021-10-01"
end_date = datetime.now().strftime("%Y-%m-%d")

default_filter_rules = """
{
    "query": {"label":"hacktoberfest",
            "state":"open",
            "type":"issue",
            "no":"assignee"},
    "qualifiers": {"updated": "2021-10-01..2021-10-01"}
}
"""

# def get_log_config():
#     config = {
#     "format":
#     "level": LOG_LEVEL
#     }

def apply_custom_filters(func):
    def inner(**filters):
        base_filter = func()
        if filters.get("qualifiers"):
            base_filter.update({"qualifiers": filters["qualifiers"]})
        list(map(lambda k: base_filter["query"].update({k[0]:k[1]}) if(k[0] not in base_filter) else None, filters.items()))
        return base_filter
    return inner


class Scheduler(object):
    """docstring for Scheduler"""
    def __init__(self, job, time):
        self.job = job
        self.time = time

    def run(self):
        self.job.run()



# def run():
#     fetcher = IssueFetch()
#     date_range = construct_date_range(start_date, end_date)
#     for lang in ALL_LANG:
#         print("Getting {} issues".format(lang))
#         for day in date_range:
#             print("Issues on {}".format(day))
#             qualifiers = {"updated": "{}..{}".format(day, day)}
#             fetcher.set_update_filters(language=lang, qualifiers=qualifiers)
#             issues = fetcher.pop_issues()
#             if issues:
#                 add_issues_to_db(issues)
#                 print("Stored")
#                 print("+"*5)
#         print("="*5)

if __name__ == '__main__':
    # run()
    log.info("This is test")
