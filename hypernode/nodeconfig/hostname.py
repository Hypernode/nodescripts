#!/usr/bin/env python

import subprocess
import hypernode.nodeconfig
import hypernode.log
from hypernode.nodeconfig import common


def apply_config(config):

    logger = hypernode.log.getLogger(__name__)

    common.check_vars(config, ["hostnames", "app_name"])

    logger.debug("Setting hostname to %s" % config["app_name"])

    logger.debug("Writing /etc/hostname")
    common.write_file("/etc/hostname", config["app_name"])

    logger.debug("Writing /etc/hosts from template /etc/hypernode/templates/03.hostname.hosts")
    common.write_file("/etc/hosts",
                      common.fill_template("/etc/hypernode/templates/03.hostname.hosts",
                                           {"hostnames": config["hostnames"],
                                           "app_name": config["app_name"]}))

    logger.debug("Calling `hostname`")
    subprocess.call(["hostname", config["app_name"]])

    logger.debug("Restarting syslog")
    subprocess.call(["service", "rsyslog", "restart"])

    return 0
