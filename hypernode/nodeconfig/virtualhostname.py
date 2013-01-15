#!/usr/bin/env python

import subprocess

from hypernode.nodeconfig import common


def apply_config(config):
    common.check_vars(config, ["hostnames"])

    common.write_file("/etc/apache2/sites-enabled/default",
                      common.fill_template("/etc/hypernode/templates/10.hostnames.default-vhost",
                                           {'hostnames': config["hostnames"]}))

    subprocess.call(["service", "apache2", "restart"])

    return 0
