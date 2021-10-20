import json
from utils.client import IssueFetch

default_filter_rules = """
{
    "query": {"label":"hacktoberfest",
            "state":"open",
            "type":"issue"},
    "qualifiers": {"updated": "2021-10-01..2021-10-01"}
}
"""

default_filter = json.loads(default_filter_rules)

def get_issues(**kwargs):
    if not kwargs.get("query"):
        kwargs["query"] = apply_default("query")
    if not kwargs.get("qualifiers"):
        kwargs["qualifiers"] = apply_default("qualifiers")
    filters = {}
    filters.update({
                   "query": kwargs["query"],
                   "qualifiers": kwargs["qualifiers"]
                   })
    # print(kwargs)
    # exit(0)
    # apply everything in kwargs as part of query
    list(map(lambda k: filters["query"].update({k[0]:k[1]}) if(k[0] not in default_filter) else None, kwargs.items()))
    fetch_issues = IssueFetch(**filters)
    hck_issues = fetch_issues.pop_issues()
    return hck_issues


def apply_default(filter_name):
    try:
        return default_filter.get(filter_name)
    except KeyError:
        print("Error: Failed to get default values for {}".format(filter_name))
        raise

if __name__ == '__main__':
    get_issues()
