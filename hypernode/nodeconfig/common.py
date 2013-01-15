#!/usr/bin/env python

import sys
import json
import os

from django.conf import settings
import django.template

settings.configure(DEBUG=True, TEMPLATE_DEBUG=True,
                   TEMPLATE_DIRS=('conf.d'))


def get_config(filename):
    with open(filename, 'r') as fd:
        content = fd.read()
        try:
            return json.loads(content)
        except ValueError:
            return {}


def check_vars(config, keynames):

    for key in keynames:
        if key not in config:
            raise ValueError("Required key '%s' not found" % key)


def write_file(filename, data, umask=None):
    old_umask = None

    if not umask is None:
        old_umask = os.umask(umask)

    try:
        with open(filename, 'w') as fd:
            fd.write(data)
    finally:
        if not umask is None:
            os.umask(old_umask)


def fill_template(template, vars={}):

    with open(template, "r") as fd:
        tmpl = django.template.Template(fd.read())
        return tmpl.render(django.template.Context(vars))
