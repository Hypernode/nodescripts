#!/usr/bin/env python

import os
import tempfile
import subprocess
import errno

from hypernode.nodeconfig import common


def apply_config(config):

    # There are three cases that we might expect:
    # 1. All ssl-fields are present, filled out and represent a certificate
    #    that passes the openssl-check.
    # 2. None of the ssl-fields are present.
    # 3. Other cases: not all of the ssl-fields are present, or they don't pass
    #    the openssl-check
    #
    # These cases yield the following actions
    # 1. The certificate is written to disk, apache is restarted
    # 2. Any certificate present on disk will be removed, the apache-
    #    configuration for the SSL-vhost will be removed, and apache will be
    #    restarted
    # 3. This is an exception, and means that there is an error in the
    #    configuration

    # We always need an app_name. Not found => exception
    common.check_vars(config, ["app_name"])

    if "ssl_common_name" in config and "ssl_body" in config and "ssl_certificate" in config and "ssl_key_chain" in config:
        # Configure SSL

        if not verify_ssl(config["ssl_certificate"], config["ssl_body"], config["ssl_key_chain"]):
            return 1
        else:
            common.write_file("/etc/ssl/private/hypernode.ca",
                              config["ssl_key_chain"],
                              umask=0077)
            common.write_file("/etc/ssl/private/hypernode.crt",
                              "%s\n\n%s" % (config["ssl_certificate"], config["ssl_body"]),
                              umask=0077)
            common.write_file("/etc/apache2/sites-enabled/default-ssl",
                              common.fill_template("/etc/hypernode/templates/05.ssl.default-ssl-vhost",
                                                   vars={'app_name': config['app_name'],
                                                         'servername': config['ssl_common_name']}))

            subprocess.call(["service", "apache2", "restart"])
            return 0

    elif "ssl_common_name" not in config and "ssl_body" not in config and "ssl_certificate" not in config and "ssl_key_chain" not in config:
        disable_ssl()
        return 0
    else:
        raise Exception


def verify_ssl(crt, key, ca):

    # Write certificate to tempfiles, and test them
    with tempfile.NamedTemporaryFile() as fd_crt, tempfile.NamedTemporaryFile() as fd_ca:
        fd_crt.write("%s\n\n%s" % (key, crt))
        fd_ca.write(ca)
        fd_crt.flush()
        fd_ca.flush()

        try:
            verify_ssl_pem(fd_crt.name)
            verify_ssl_ca(fd_crt.name, fd_ca.name)
        except subprocess.CalledProcessError:
            return False
        except Exception:
            return False

    return True


def verify_ssl_pem(crt_file):

    subprocess.check_output(["/usr/bin/openssl", "x509",
                             "-in", crt_file, "-noout"],
                            shell=False, stderr=subprocess.STDOUT)


def verify_ssl_ca(crt_file, ca_file):

    subprocess.check_output(["/usr/bin/openssl", "verify",
                             "-CAfile", ca_file, crt_file],
                            shell=False, stderr=subprocess.STDOUT)


def disable_ssl():
    restart_apache = False

    for f in ["/etc/ssl/private/hypernode.crt", "/etc/ssl/private/hypernode.ca", "/etc/apache2/sites-enabled/default-ssl"]:
        try:
            os.unlink(f)
            # if any of the files existed (and the unlink succeeded), we
            # need to restart apache after this
            restart_apache = True
        except OSError as e:
            # We expect this to happen, as the files may not exist. This
            # will yield errno 2 (No such file or directory)
            if e.errno != errno.ENOENT:
                raise

    if restart_apache:
        subprocess.call(["service", "apache2", "restart"])
