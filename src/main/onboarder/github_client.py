import logging
import os

from github import Github

log = logging.getLogger()
log.setLevel(os.environ.get("LOG_LEVEL", 'info').upper())

class GitHubClient(object):
    """docstring for GitHubClient"""
    token = os.environ.get("GITHUB_TOKEN")
    g_client = Github(token)
    def __init__(self, per_page=100):
        self.g_client.per_page = 100
        self.__check_conn()

    def __check_conn(self):
        try:
            if not self.token:
                log.warn("api client not authenticated."
                          "proceeding with anonymous mode")
            print("Connected. Rate Limit: {}".format(self.g_client.rate_limiting[1]))
        except Exception as e:
            print("Failed to connect. Error: {}".format(str(e)))


class GithubUser(GitHubClient):
    def __init__(self,
    user_id,
    ):
        self.id = user_id
        super(GithubUser, self).__init__()
        self._set_user_details()

    def _set_user_details(self):
        self.user = self.g_client.get_user(self.id)
