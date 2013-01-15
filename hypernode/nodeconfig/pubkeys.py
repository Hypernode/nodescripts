#!/usr/bin/env python

import os

from hypernode.nodeconfig import common

PREAMBLE = "#\n# This file is generated. Please update your public keys on the Hyperpanel\n#\n\n"
DOTSSH = "/home/user/.ssh"
AUTHKEYS = "/home/user/.ssh/authorized_keys"


def apply_config(config):
    common.check_vars(config, ["public_keys"])
    contents = PREAMBLE + "".join([("%s\n\n" % key) for key in config["public_keys"]])

    # do not handle any errors here
    if not os.path.isdir(DOTSSH):
        os.mkdir(DOTSSH, 0755)

    os.chown(DOTSSH, 1000, 1000)
    common.write_file(AUTHKEYS, contents, umask=0022)

    return 0
