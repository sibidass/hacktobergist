from db import DB
from github_client import GithubUser

onboard_table = "user_details"

class User(object):
    preserve_attrs = ['id', 'email'] # we preserve these from filtering
    to_fetch = ['login',
        'avatar_url',
        'name',
        'location',
        'email'
        ]
    """Fetch user data from github and update to DB"""
    def __init__(
        self,
        user_id,
        email,
        *args,
        ):
        """Represents a single user in github"""
        self._set_user_data(GithubUser(user_id).user)
        if args:
            self._filter_args(args)
        self._set_communication_mail(email)

    def _set_user_data(self, github_named_user):
        self.user = {}
        for key in self.to_fetch:
            self.user.update({
                key: getattr(github_named_user, key)
                          })

    def _filter_args(self, filter):
        preserved = {}
        for attr in preserve_attrs:
            preserved[attr] = self.user.pop(attr, None)
        for key in self.user:
            if key not in filter:
                self.user.pop(key, None)
        self.user.update(
            preserved
            )

    def _set_communication_mail(self, email):
        if not email:
            email = self.user.get(email)
        self.user.update({
                "communication_mailid": email
            })

    def insert_to_db(self):
        db_resp = DB(onboard_table).put(self.user)
        return db_resp
