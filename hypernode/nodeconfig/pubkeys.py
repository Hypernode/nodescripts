import os
import logging

from hypernode.nodeconfig import common


logger = logging.getLogger(__name__)

PREAMBLE = "#\n# This file is generated. Please update your public keys on the Hyperpanel\n#\n\n"
DOTSSH = "/home/user/.ssh"
AUTHKEYS = "/home/user/.ssh/authorized_keys"


def apply_config(config):
    common.check_vars(config, ["public_keys"])
    contents = PREAMBLE + "".join([("%s\n\n" % key) for key in config["public_keys"]])

    # do not handle any errors here
    if not os.path.isdir(DOTSSH):
        logging.info("Creating .ssh directory")
        os.mkdir(DOTSSH, 0755)

    logging.info("Setting .ssh dir owner")
    os.chown(DOTSSH, 1000, 1000)

    logging.info("Write authorized_keys file")
    common.write_file(AUTHKEYS, contents, umask=0022)