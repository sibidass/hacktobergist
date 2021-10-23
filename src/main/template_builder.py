from jinja2 import Environment, FileSystemLoader
import os
import toml
from utils.db import DB
from utils.db import DB


config_file = "config.toml"
TEMPLATES_PATH = "templates"
class Template(object):
    """docstring for Template"""
    def __init__(self, template_folder):
        loaded = FileSystemLoader(template_folder)
        self.template = Environment(loader=loaded)

    def render(self, file, **tmpl_vars):
        content = self.template.get_template(file)
        return content.render(tmpl_vars)

if __name__ == '__main__':
    updater = SiteUpdaterIssueJob(["PHP"])
    updater.run()
    # t = Template("templates/head/issue_head.yaml")
    # with open("sitefile.md", "w") as f:
    #     f.write(t.render(language="python"))
    # with open("sitefile1.md", "w") as f:
    #     f.write(t.render(repo_link="test repo"))
