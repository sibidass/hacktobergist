from datetime import datetime
from datetime import timedelta
import json
import os
import unicodedata

import toml
from utils.db import DB
from utils.client import IssueFetch
from utils.logger import get_logger
from template_builder import Template


default_filter_rules = """
{
    "query": {"label":"hacktoberfest",
            "type":"issue",
            "no":"assignee"},
    "qualifiers": {"updated": "2021-10-01..2021-10-01"}
}
"""

SEC = 1000 # 1 sec = 1000ms
MIN = 60 * SEC # 1 min = 60 secs
ALL_LANG = ['HTML', 'Twig', 'CSS', 'Swift', 'Julia', 'Haskell', 'Kotlin', 'Svelte', 'HCL', 'Vue', 'TypeScript', 'Rust', 'Dockerfile', 'YAML', 'Shell', 'C++', 'C', 'Java', 'SCSS', 'Jupyter Notebook', 'R', 'Q#', 'Lua', 'C#', 'Perl', 'PHP', 'Go', 'Ruby', 'Hack', 'Cython', 'Python', 'Elixir', 'JavaScript', 'Dart']

log = get_logger(__name__)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(APP_DIR, "../../")
config_file = os.path.join(APP_DIR, "config.toml")
config = toml.load(config_file)
issues_table = config.get("db")["issues_table"]
issues_table_process = config.get("db")["issues_table_process"]


def apply_custom_filters(func):
    def inner(_, **filters):
        base_filter = func(_)
        if filters.get("qualifiers"):
            base_filter.update({"qualifiers": filters["qualifiers"]})
        list(map(lambda k: base_filter["query"].update({k[0]:k[1]}) if(k[0] not in base_filter) else None, filters.items()))
        return base_filter
    return inner


class IssueFetcherJob(object):
    """docstring for IssueFetcherJob"""
    def __init__(self, start_date, end_date, lamda_context=None, *languages):
        self.lamda_context = lamda_context
        self.date_range = self._construct_date_range(start_date, end_date)
        self.languages = languages
        self.processed_info = self._get_processed_info()

    def _construct_date_range(self, s_date, e_date):
        date_range = []
        cur_date = datetime.strptime(s_date, "%Y-%m-%d")
        while cur_date <= datetime.strptime(e_date, "%Y-%m-%d"):
            date_range.append(cur_date.strftime("%Y-%m-%d"))
            cur_date = cur_date + timedelta(days=1)
        return date_range

    @apply_custom_filters
    def _apply_filters(self, **filters):
        return json.loads(default_filter_rules)

    def run(self):
        fetcher = IssueFetch()
        for lang in self.languages:
            l_start_date = None
            lang_process_info = None
            if lang in self.processed_info:
                if self.processed_info[lang].get("completed_on"):
                    continue
                lang_process_info = self.processed_info[lang].get("process_info")
                l_start_date = lang_process_info.get("process_started")
            if l_start_date:
                date_range_idx = self._find_date_idx(l_start_date)
                date_range = self.date_range[date_range_idx:]
            else:
                date_range = self.date_range
                lang_process_info["processed"] = []
            log.info("Getting {} issues from {}".format(lang, date_range[0]))
            for day in date_range:
                lang_process_info["process_started"] = day
                if self.lamda_context and self.lamda_context.get_remaining_time_in_millis() < 5 * MIN:
                    log.info("premature ending..")
                    self._update_processed_info(lang, lang_process_info)
                    return {
                    "status": "partial",
                    "process_info": self.processed_info
                    }
                log.debug("Issues on {}".format(day))
                qualifiers = {"updated": "{}..{}".format(day, day)}
                filters = self._apply_filters(language=lang, qualifiers=qualifiers)
                issues = fetcher.pop_issues(**filters)
                if issues:
                    self.add_issues_to_db(issues)
                    log.debug("Stored in DB")
                    log.debug("-"*5)
                lang_process_info["processed"].append(day)
            lang_process_info["process_started"] = None
            self._update_processed_info(lang, lang_process_info, complete=True)
            log.debug("="*5)
        return {
        "status": "complete"
        }

    def _update_processed_info(self, lang, process_info, complete=False):
        if complete:
            completed = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
        else:
            completed = None
        self.processed_info.update({
                                   lang: {
                                   "language": lang,
                                   "process_info": process_info,
                                   "completed_on": completed
                                   }
                                   })
        db = DB(issues_table_process)
        db.put(self.processed_info[lang])

    def _find_date_idx(self, date):
        for idx, item in enumerate(self.date_range):
            if item == date:
                return idx

    @staticmethod
    def add_issues_to_db(issues):
        db = DB(issues_table)
        for issue in issues:
            resp = issue.insert_to_db(db)
            if resp:
                if resp.get("ResponseMetadata")["HTTPStatusCode"] != 200:
                    log.error("Failed to insert {}-{} to DB. Errorcode: {}".format(issue.id, issue.language, str(resp.get("HTTPStatusCode"))))
            else:
                log.critical("Failed to connect to db")
                raise Exception("DB Error")

    def _get_processed_info(self):
        db = DB(issues_table_process)
        today = datetime.now().strftime("%Y-%m-%d")
        processed_info = {}
        for lang in self.language:
            resp = db.get({
                    "key": {
                    "name": "language",
                    "value": lang
                    },
                    "condition": "eq",
                    "attr": {
                    "name": "completed_on",
                    "value": today,
                    "condition": "eq"
                    }
                   })
            if resp:
                processed_info[lang] = resp[0]
        return processed_info


class IssueFetcherJobLean(object):
    """docstring for IssueFetcherJobLean"""
    def __init__(self, **filters):
        self.filters = self._apply_filters(**filters)

    @apply_custom_filters
    def _apply_filters(self, **filters):
        return json.loads(default_filter_rules)

    def run(self):
        fetcher = IssueFetch()
        issues = fetcher.pop_issues(**self.filters)
        day = self.filters.get("qualifiers")["updated"].split(".")[0]
        language = self.filters.get("query")["language"]
        if issues:
            log.info("Found {} issues for {} on {}".format(len(issues), language, day))
            self.add_issues_to_db(issues)
            log.debug("Stored in DB")
            log.debug("-"*5)
        else:
            log.info("no issues found for {} on {}".format(language, day))

class SiteUpdaterIssueJob(object):
    config = config["siteupdater"]
    """docstring for SiteUpdaterJob"""
    def __init__(self, languages, issue_state):
        self.issues_meta = self.config.get("issues")
        self.templates_location = os.path.join(BASE_DIR, self.config.get("templates_location"))
        self.dest_path = os.path.join(BASE_DIR, self.issues_meta.get("dest_path"))
        self.templates = Template(self.templates_location)
        self.db = DB(self.issues_meta.get("db_table"))
        self.languages = languages
        self.issue_state = issue_state

    def run(self):
        log.debug("Reading issues from DB:\n{}".format(",".join(self.languages)))
        issues = self._read_from_db()
        log.debug("Finished reading DB")
        tmpl_vars = {}
        for issue in issues:
            tmpl_vars.update({
                             "time": issue.get("updated_date"),
                             "issue_title": self.escape_special(issue.get("title")),
                             "issue_url": issue.get("url"),
                             "repo_link": issue.get("url").rsplit("/",2)[0],
                             "language": issue.get("language")
                             })
            page_mdfile_location = os.path.join(self.templates_location, "pages", self.issues_meta["data_file"])
            page_data = self._read_from_file(page_mdfile_location)
            dst_parent_dir = issue.get("language")
            for file in self.issues_meta["template_files"]:
                log.debug("rendering template {}".format(file))
                content = self.templates.render(file, **tmpl_vars)
                try:
                    if file.find("_head") != -1:
                        file_name = str(issue.get("id")) + ".md"
                        content += "\n" + page_data
                    # elif file.find("_index") != -1:
                    #     file_name = "_index.md"
                    else:
                        raise Exception("template file {} not supported yet".format(file))
                    dst_file = os.path.join(self.dest_path, dst_parent_dir, file_name)
                    log.debug("writing data to {}".format(dst_file))
                    self._write_to_file(content, dst_file)
                except Exception as e:
                    log.warn(str(e))
                    continue
            self._update_index()

    def _update_index(self):
        index_template = self.issues_meta["index_template"]
        index_file = "_index.md"
        dst_parent_dir = self.dest_path
        for lang in ALL_LANG:
            dst = os.path.join(dst_parent_dir, lang)
            if os.path.exists(dst):
                content = self.templates.render(index_template, language=lang)
                self._write_to_file(content, os.path.join(dst, index_file))

    def _read_from_file(self, file):
        lines = ""
        with open(file, "r") as f:
            for line in f:
                lines += line
        return lines

    def _write_to_file(self, content, file):
        try:
            with open(file, "w") as f:
                f.write(content)
        except FileNotFoundError:
            log.warn("{} does not exist. creating and writing".format(file))
            os.makedirs(os.path.dirname(file), exist_ok=True)
            self._write_to_file(content, file)


    def _read_from_db(self):
        p_key = self.issues_meta.get("db_partition_key")
        items_total = []
        for lang in self.languages:
            items = self.db.get({
                                "key": {
                                "name": "language",
                                "value": lang
                                },
                                "condition": "eq",
                                "attr": {
                                "name": "state",
                                "value": "open",
                                "condition": "eq"
                                }
                                })
            items_total.extend(items)
        return items_total

    @staticmethod
    def escape_special(text):
        new_text = text
        for c in ['\\', '"']:
            new_text = new_text.replace(c, '\\'+c)
        formatted_text = "".join(ch for ch in new_text if unicodedata.category(ch)[0]!="C")
        return '"' + formatted_text + '"'

if __name__ == '__main__':
    log.info("Test from jobs module")
    test_logger()

