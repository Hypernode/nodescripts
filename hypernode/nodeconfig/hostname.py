import subprocess
from hypernode.nodeconfig import common
import logging

logger = logging.getLogger(__name__)


def apply_config(config):

    common.check_vars(config, ["hostnames", "app_name"])

    logger.debug("Setting hostname to %s" % config["app_name"])

    logger.info("Writing /etc/hostname")
    common.write_file("/etc/hostname", config["app_name"])

    logger.info("Writing /etc/hosts from template /etc/hypernode/templates/03.hostname.hosts")
    common.write_file("/etc/hosts",
                      common.fill_template("/etc/hypernode/templates/03.hostname.hosts",
                                           {"hostnames": config["hostnames"],
                                           "app_name": config["app_name"]}))

    logger.info("Calling `hostname`")
    subprocess.call(["hostname", config["app_name"]])

    logger.info("Restarting rsyslog")
    subprocess.call(["service", "rsyslog", "restart"])