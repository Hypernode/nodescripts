#!/usr/bin/env python

import hashlib
import json
import requests
import hypernode.nodeconfig
from hypernode.nodeconfig import common


class CallbackException(Exception):  # pragma: no cover
    pass


def call_success(config):
    logger = hypernode.nodeconfig.getLogger(__name__)

    common.check_vars(config, ["callback_url", "app_name"])
    hash = hash_deployment_config(config)

    logger.info("Signaling back to control that we successfully applied nodeconfig with hash %s" % hash)
    logger.debug("POSTing to %s" % config["callback_url"])

    headers = {'User-Agent': 'nodeconfig/callback for %s' % config["app_name"]}
    r = requests.post(config["callback_url"], data={"applied_hash": hash}, headers=headers, verify=True)

    if r.status_code == 200:
        logger.debug("Callback was received")
    else:
        logger.error("Callback was unsuccessful: %s" % r.status_code)
        logger.error(r.text)
        raise Exception("Success callback failed with HTTP status code %d: %s" % (r.status_code, r.text))


def call_error(config, module, exception, log):
    logger = hypernode.nodeconfig.getLogger(__name__)

    common.check_vars(config, ["callback_url", "app_name"])
    hash = hash_deployment_config(config)

    logger.info("Signaling back to control that module %s failed while applying the nodeconfig" % module.__name__)
    logger.debug("POSTing to %s" % config["callback_url"])

    headers = {'User-Agent': 'nodeconfig/callback for %s' % config["app_name"]}
    r = requests.post(config["callback_url"],
                      data={"applied_hash": hash,
                            "error": exception,
                            "module": module.__name__,
                            "log": "\n".join(log)
                            },
                      headers=headers,
                      verify=True)

    if r.status_code == 200:
        logger.debug("Callback was received")
    else:
        logger.error("Callback was unsuccessful: %s" % r.status_code)
        logger.error(r.text)
        raise CallbackException("Error callback failed with HTTP status code %d: %s" % (r.status_code, r.text))


def hash_deployment_config(config):
    # do not handle any json or hashing exceptions
    return hashlib.sha512(json.dumps(config)).hexdigest()
