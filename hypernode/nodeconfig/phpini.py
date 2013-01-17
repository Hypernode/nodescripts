#!/usr/bin/env python

import subprocess
import logging

from hypernode.nodeconfig import common

logger = logging.getLogger(__name__)


def apply_config(config):

    logger.debug("Checking configuration for php_options")
    common.check_vars(config, ["php_options"])

    options = None
    extensions = {}

    logger.debug("Checking configuration for php_options.options")
    # Options is dict, and template determines which keys are valid
    if "options" in config["php_options"]:
        logger.debug("php_options.options found")
        options = config["php_options"]["options"]

    logger.debug("Checking configuration for php_options.extensions")
    # Extensions is a list. We'll map it to a dict here, to give it to the template
    if "extensions" in config["php_options"]:
        logger.debug("php_options.extensions found")
        for item in config["php_options"]["extensions"]:
            logger.debug("Enabling extension '%s'" % item)
            extensions[item] = True

    logger.info("Writing /etc/php5/mods-available/hypernode.ini")
    common.write_file("/etc/php5/mods-available/hypernode.ini",
                      common.fill_template("/etc/hypernode/templates/20.phpini",
                                           {"options": options,
                                            "extensions": extensions}))

    subprocess.call(["php5enmod", "hypernode/99"])

    logger.info("Restarting PHP5-FPM daemon")
    subprocess.call(["service", "php5-fpm", "restart"])

    return 0
