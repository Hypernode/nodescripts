import subprocess
from hypernode.nodeconfig import common
import logging

logger = logging.getLogger(__name__)


def apply_config(config):

    logger.debug("Checking configuration for app_name and region")
    common.check_vars(config, ["app_name", "region"])

    logging.info("Calling /usr/local/bin/cfn-init")
    subprocess.call(["/usr/local/bin/cfn-init", "-s", config["app_name"], "-r", "LaunchConfig", "--credential-file", "/etc/cfn/cfn-credentials", "--region", config["region"]])