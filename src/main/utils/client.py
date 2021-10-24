import os
import json
from github import Github
from datetime import datetime
import time
from github.GithubException import GithubException

default_filter_rules = """
{
    "query": {"label":"hacktoberfest",
            "state":"open",
            "type":"issue",
            "no":"assignee"},
    "qualifiers": {"updated": "2021-10-01..2021-10-01"}
}
"""

default_filter = json.loads(default_filter_rules)
SLEEP_TIME = int(os.environ.get("github_client_sleep_time", 5))

def apply_default(filter_name):
    try:
        return default_filter.get(filter_name)
    except KeyError:
        print("Error: Failed to get default values for {}".format(filter_name))
        raise

class GitHubClient(object):
    """docstring for GitHubClient"""
    token = os.environ.get("GITHUB_TOKEN")
    user = os.environ.get("GITHUB_USER")
    g_client = Github(token)
    def __init__(self, per_page=100):
        self.g_client.per_page = per_page
        self.__check_conn()

    def __check_conn(self):
        try:
            self.rem_limit, limit =  self.g_client.rate_limiting
            self.limit_reset_time = self.g_client.rate_limiting_resettime
            self.limit_reset_time_human = datetime.fromtimestamp(self.limit_reset_time).strftime("%Y-%m-%d %H:%M:%S")
            print("Connected. Rate Limit: {}".format(limit))
            print("Next refresh time: {}".format(
                                                 self.limit_reset_time_human))
        except Exception as e:
            print("Failed to connect. Error: {}".format(str(e)))

    # def get_issues(self, query, qualifier):
    #     return self.g_client.search_issues(query=query, sort="updated", order="asc", **qualifier)



class HacktoberIssue(object):
    """docstring for HacktoberIssue"""
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.url = kwargs.get("url")
        self.state = kwargs.get("state")
        self.updated_date = kwargs.get("updated_at")
        self.title = kwargs.get("title")

    def is_active(self):
        return self.updated_date > datetime.strptime(self.min_date)

    def set_language(self, lang):
        self.language = lang

    def insert_to_db(self, db):
        return db.put({
               "id": self.id,
               "url": self.url,
               "state": self.state,
               "updated_date": self.updated_date.strftime("%Y-%m-%d %H:%M:%S"),
               "language": self.language,
               "title": self.title
               })

class IssueFetch(GitHubClient):
    """docstring for IssueFetch"""
    def __init__(self):
        self.api_count = 1
        super(IssueFetch, self).__init__()

    def pop_issues(self, **filters):
        hck_issues = []
        query = filters.get("query")
        qualifiers = filters.get("qualifiers")
        language = query.get("language")
        try:
            print(query)
            print(qualifiers)
            self.api_count += 1
            issues = self.g_client.search_issues(query=self._construct_query(query), sort="updated", order="asc", **qualifiers)
            print("got {} issues".format(issues.totalCount))
            for item in issues:
                hck_issue = HacktoberIssue(**{
                                           "id":item.id,
                                           "url":item.html_url,
                                           "state": item.state,
                                           "updated_at": item.updated_at,
                                           "title": item.title})
                if language:
                    hck_issue.set_language(language)
                else:
                    lang = item.repository.language # not efficient
                    hck_issue.set_language(lang)
                hck_issues.append(hck_issue)
            if issues.totalCount >= 1000:
                last_updated = hck_issues[-1].updated_date
                print("fetching issues from {}".format(last_updated.strftime("%Y-%m-%dT%H:%M:%S")))
                if ".." in self.qualifiers["updated"]:
                    end_date = self.qualifiers["updated"].split("..")[1]
                else:
                    end_date = ""
                self.qualifiers["updated"] = "{}..{}".format(last_updated.strftime("%Y-%m-%dT%H:%M:%S"), end_date)
                hck_issues.extend(self.pop_issues())
            else:
                print("issue fetched {} is less than 1000. stopping probe".format(issues.totalCount))
        except GithubException as e:
            print("Error: {}".format(str(e)))
            if "API rate limit exceeded" in str(e):
                if self.api_count >= self.rem_limit:
                    print("Next refresh time: {}".format(self.limit_reset_time_human))
                    curr_time = int(datetime.timestamp(datetime.now()))
                    sec_to_wait = self.limit_reset_time - curr_time
                    self.api_count = 1
                else:
                    print("Per minute limit reached. Curret api count: {}".format(self.api_count))
                    sec_to_wait = 60
                print("waiting for {} secs..".format(sec_to_wait))
                time.sleep(sec_to_wait)
                print("resuming..")
                if self.api_count == 1:
                    super(IssueFetch, self).__init__()
                hck_issues = self.pop_issues(**filters)
            elif "Please wait a few minutes before you try again" in str(e):
                time.sleep(150)
                hck_issues = self.pop_issues(**filters)
        # sleeping for 2 secs before another github request
        time.sleep(SLEEP_TIME)
        return hck_issues

    def _construct_query(self, query):
        query_constructed = ""
        for k, v in query.items():
            if query_constructed:
                query_constructed += " "
            query_constructed += "{}:{}".format(k, v)
        return query_constructed


class GithubUser(GitHubClient):
    def __init__(self,
    user_id,
    user_email,
    ):
        self.id = user_id
        self.email = user_email
        super(GithubUser, self).__init__()
        self.user = self.get_user_details()

    def get_user_details(self):
        return self.g_client.get_user(self.id)

class GithubRepo(GitHubClient):
    """docstring for GithubRepo"""
    def __init__(self,
                 repo_id):
        super(GithubRepo, self).__init__()
        self.repo_data = self._get_details(repo_id)

    def _get_details(self, id):
        return self.g_client.get_repo(id)



if __name__ == '__main__':
    filters = {
    "query": {"label":"hacktoberfest",
            "state":"open",
            "type":"issue",
            "language":"python"},
    "qualifiers": {"updated": ">=2021-10-01"}
    }
    # fetch_issues = IssueFetch(**filters)
    # hck_issues = fetch_issues.pop_issues()
    user = GithubUser('octocat', 'sibidas@gmail.com').user
    # user.communication = "sbd@gmail.com"
    to_fetch = ['login',
        'avatar_url',
        'name',
        'location',
        'email'
        ]
    myuser = {}
    for key in to_fetch:
        myuser.update({
            key: getattr(user, key)
                      })
    print(myuser)

    # print("Found {} issues".format(len(hck_issues)))
    # for i in hck_issues:
    #     print("{}: {}".format(i, i.updated_date))
