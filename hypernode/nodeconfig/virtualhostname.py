#!/usr/bin/env python

import subprocess
import logging

from hypernode.nodeconfig import common

logger = logging.getLogger(__name__)


def apply_config(config):
    common.check_vars(config, ["hostnames"])

    logger.info("Writing apache configuration")
    common.write_file("/etc/apache2/sites-enabled/default",
                      common.fill_template("/etc/hypernode/templates/10.hostnames.default-vhost",
                                           {'hostnames': config["hostnames"]}))

    logger.info("Restarting apache2")
    subprocess.call(["service", "apache2", "reload"])