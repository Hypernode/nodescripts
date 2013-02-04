import os
import tempfile
import subprocess
import errno
import logging

from hypernode.nodeconfig import common


logger = logging.getLogger(__name__)

CRTPATH = '/etc/ssl/private/hypernode.crt'
CAPATH = '/etc/ssl/private/hypernode.ca'


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
        logger.debug("Configuring SSL")

        logger.debug("Verifying SSL key and certificate")
        verify_ssl(config["ssl_certificate"], config["ssl_body"], config["ssl_key_chain"])

        template_vars = {'app_name': config['app_name'],
                         'servername': config['ssl_common_name'],
                         'crtpath': CRTPATH}

        if 'ssl_key_chain' in config and config['ssl_key_chain']:
            logger.info("Writing %s", CAPATH)
            common.write_file(CAPATH,
                              config["ssl_key_chain"],
                              umask=0077)

            template_vars['capath'] = CAPATH

        logger.info("Writing %s", CRTPATH)
        common.write_file(CRTPATH,
                          "%s\n\n%s" % (config["ssl_certificate"], config["ssl_body"]),
                          umask=0077)

        logger.info("Writing /etc/apache2/sites-enabled/default-ssl")
        common.write_file("/etc/apache2/sites-enabled/default-ssl",
                          common.fill_template("/etc/hypernode/templates/05.ssl.default-ssl-vhost",
                                               vars=template_vars))

        logger.info("Restarting apache2")
        subprocess.call(["service", "apache2", "restart"])
        return

    elif "ssl_common_name" not in config and "ssl_body" not in config and "ssl_certificate" not in config and "ssl_key_chain" not in config:
        logger.debug("Disabling SSL")
        disable_ssl()
        return
    else:
        raise RuntimeError("Incomplete SSL parameters in configuration")


def verify_ssl(crt, key, ca):

    # Write certificate to tempfiles, and test them
    with tempfile.NamedTemporaryFile() as fd_crt, tempfile.NamedTemporaryFile() as fd_ca:
        fd_crt.write("%s\n\n%s" % (key, crt))
        fd_crt.flush()
        fd_ca.write(ca)
        fd_ca.flush()

        # If verification fails, an exception will be raised
        verify_ssl_pem(fd_crt.name)
        if ca:
            verify_ssl_ca(fd_crt.name, fd_ca.name)


def verify_ssl_pem(crt_file):
    # check_output raises CalledProcessError if exit code is != 0
    subprocess.check_output(["/usr/bin/openssl", "x509",
                             "-in", crt_file, "-noout"],
                            shell=False, stderr=subprocess.STDOUT)


def verify_ssl_ca(crt_file, ca_file):
    # check_output raises CalledProcessError if exit code is != 0
    subprocess.check_output(["/usr/bin/openssl", "verify",
                             "-CAfile", ca_file, crt_file],
                            shell=False, stderr=subprocess.STDOUT)


def disable_ssl():
    restart_apache = False

    for f in ["/etc/ssl/private/hypernode.crt", "/etc/ssl/private/hypernode.ca", "/etc/apache2/sites-enabled/default-ssl"]:
        try:
            logger.info("Removing %s", f)
            os.unlink(f)
            # if any of the files existed (and the unlink succeeded), we
            # need to restart apache after this
            restart_apache = True
        except OSError as e:
            # If we catch an error, check if it is errno 2 (No such file or directory).
            # This is a case we expect to happen, as the files may not exist.
            # - If the errno IS 2, then do nothing
            # - If the errno is NOT 2, then reraise the error
            if e.errno == errno.ENOENT:
                pass
            else:
                raise

    if restart_apache:
        logging.info("Restarting apache2")
        subprocess.call(["service", "apache2", "restart"])