from jinja2 import Environment, FileSystemLoader
import os
import toml
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
