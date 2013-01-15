#!/usr/bin/env python

import subprocess

from hypernode.nodeconfig import common


def apply_config(config):
    common.check_vars(config, ["php_options"])

    options = None
    extensions = {}

    # Options is dict, and template determines which keys are valid
    if "options" in config["php_options"]:
        options = config["php_options"]["options"]

    # Extensions is a list. We'll map it to a dict here, to give it to the template
    if "extensions" in config["php_options"]:
        for item in config["php_options"]["extensions"]:
            extensions[item] = True

    common.write_file("/etc/php5/conf.d/99.hypernode.ini",
                      common.fill_template("/etc/hypernode/templates/20.phpini",
                                           {"options": options,
                                            "extensions": extensions}))

    subprocess.call(["service", "php5-fpm", "restart"])

    return 0
