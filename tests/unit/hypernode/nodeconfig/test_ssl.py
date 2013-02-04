#!/usr/bin/env python

import sys
import mock
import tests.unit

import subprocess

import hypernode.nodeconfig.sslcerts as ssl
import hypernode.nodeconfig.common


class TestSSLConfig(tests.unit.BaseTestCase):

    def setUp(self):
        self.mock_checkvars = self.setUpPatch('hypernode.nodeconfig.common.check_vars')

        self.mock_call = self.setUpPatch('subprocess.call')
        self.mock_check_output = self.setUpPatch('subprocess.check_output')

        self.mock_open = self.setUpPatch('__builtin__.open', themock=mock.mock_open())
        self.mock_tempfile = self.setUpPatch('tempfile.NamedTemporaryFile', themock=mock.mock_open())

        self.mock_writefile = self.setUpPatch('hypernode.nodeconfig.common.write_file', mock.Mock(return_value=True))
        self.mock_filltemplate = self.setUpPatch('hypernode.nodeconfig.common.fill_template', mock.Mock(return_value="data"))

        self.fixture = {
            "app_name": "myapp",
            "ssl_certificate": "laskdnf",
            "ssl_key_chain": "chain",
            "ssl_common_name": "cn",
            "ssl_body": "body"
        }

    def test_apply_config_checks_appname_var(self):
        self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl')
        ssl.apply_config(self.fixture)
        self.mock_checkvars.assert_called_once_with(self.fixture, ["app_name"])

    def test_apply_config_raises_exception_when_not_all_ssl_params_present(self):
        config = self.fixture.copy()
        del config["ssl_body"]
        self.assertRaises(Exception, ssl.apply_config, config)
        config = self.fixture.copy()
        del config["ssl_common_name"]
        self.assertRaises(Exception, ssl.apply_config, config)
        config = self.fixture.copy()
        del config["ssl_certificate"]
        self.assertRaises(Exception, ssl.apply_config, config)
        config = self.fixture.copy()
        config["ssl_key_chain"] = ''
        ssl.apply_config(config)  # No exception!

    def test_apply_config_doesnt_raise_exception_when_no_ssl_params_present(self):
        config = {
            "app_name": "myapp",
        }
        self.setUpPatch('hypernode.nodeconfig.sslcerts.disable_ssl')
        ssl.apply_config(config)

    def test_apply_config_calls_disable_ssl_config_when_no_ssl_params_are_present(self):
        config = {
            "app_name": "myapp",
        }
        mock_verify = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl')
        mock_disable = self.setUpPatch('hypernode.nodeconfig.sslcerts.disable_ssl')
        ssl.apply_config(config)
        assert not mock_verify.called
        assert mock_disable.called

    def test_apply_config_verifies_ssl_certificate(self):
        mock_verify = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl', mock.Mock(return_value=True))
        ssl.apply_config(self.fixture)
        mock_verify.assert_called_once_with(self.fixture['ssl_certificate'],
                                            self.fixture['ssl_body'],
                                            self.fixture['ssl_key_chain'])

    def test_apply_config_raises_exception_when_ssl_certificate_is_invalid(self):
        mock_verify = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl', mock.Mock(side_effect=SSLTestException()))
        self.assertRaises(Exception, ssl.apply_config, self.fixture)
        mock_verify.assert_called_once_with(self.fixture['ssl_certificate'],
                                            self.fixture['ssl_body'],
                                            self.fixture['ssl_key_chain'])

    def test_apply_config_writes_certificate_if_valid(self):
        self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl', mock.Mock(return_value=True))
        ret = ssl.apply_config(self.fixture)

        self.mock_writefile.assert_any_call("/etc/ssl/private/hypernode.ca", self.fixture['ssl_key_chain'], umask=0077)
        self.mock_writefile.assert_any_call("/etc/ssl/private/hypernode.crt", "%s\n\n%s" %
                                            (self.fixture['ssl_certificate'],
                                             self.fixture['ssl_body']), umask=0077)

    def test_apply_config_doesnt_write_ca_if_not_provided(self):
        self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl', mock.Mock(return_value=True))
        self.fixture['ssl_key_chain'] = ''

        ret = ssl.apply_config(self.fixture)

        self.assertNotIn(mock.call("/etc/ssl/private/hypernode.ca", self.fixture['ssl_key_chain'], umask=0077), self.mock_writefile.mock_calls)
        self.mock_writefile.assert_any_call("/etc/ssl/private/hypernode.crt", "%s\n\n%s" %
                                                                              (self.fixture['ssl_certificate'],
                                                                               self.fixture['ssl_body']), umask=0077)

    def test_apply_config_restarts_apache_if_certificate_is_valid(self):
        self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl')

        ssl.apply_config(self.fixture)
        self.mock_call.assert_called_once_with(["service", "apache2", "restart"])

    def test_verify_ssl_writes_certificateinfo_to_tempfiles(self):
        self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_pem')
        self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_ca')

        ssl.verify_ssl('my_crt', 'my_key', 'my_ca')

        fd = self.mock_tempfile()
        fd.write.assert_any_call('%s\n\n%s' % ('my_key', 'my_crt'))
        fd.write.assert_any_call('my_ca')

    def test_verify_ssl_raises_exception_when_pem_verification_fails(self):
        mock_verifypem = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_pem', mock.Mock(side_effect=SSLTestException))
        mock_verifyca = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_ca', mock.Mock())

        self.assertRaises(Exception, ssl.verify_ssl, 'my_crt', 'my_key', 'my_ca')

        self.assertTrue(mock_verifypem.called)
        self.assertFalse(mock_verifyca.called)

    def test_verify_ssl_raises_exception_when_ca_verification_fails(self):
        verify_ssl_pem = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_pem')
        verify_ssl_ca = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_ca', mock.Mock(side_effect=SSLTestException))

        self.assertRaises(Exception, ssl.verify_ssl, 'my_crt', 'my_key', 'my_ca')

        self.assertTrue(verify_ssl_pem.called)
        self.assertTrue(verify_ssl_ca.called)

    def test_verify_ssl_throws_no_exception_if_verification_succeeds(self):
        verify_ssl_pem = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_pem')
        verify_ssl_ca = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_ca')

        ssl.verify_ssl('my_crt', 'my_key', 'my_ca')

        self.assertTrue(verify_ssl_pem.called)
        self.assertTrue(verify_ssl_ca.called)

    def test_verify_ssl_doesn_check_ca_if_not_provided(self):
        verify_ssl_pem = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_pem')
        verify_ssl_ca = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_ca')

        ssl.verify_ssl('my_crt', 'my_key', '')

        self.assertTrue(verify_ssl_pem.called)
        self.assertFalse(verify_ssl_ca.called)

    def test_verify_ssl_pem_calls_openssl_with_filename(self):
        ssl.verify_ssl_pem("my_crt_file")
        self.mock_check_output.assert_called_once_with(["/usr/bin/openssl", "x509",
                                                        "-in", "my_crt_file", "-noout"],
                                                       shell=False, stderr=subprocess.STDOUT)

    def test_verify_ssl_pem_does_not_catch_exception_raised_by_subprocess(self):
        self.setUpPatch('subprocess.check_output', mock.Mock(side_effect=SSLTestException))
        self.assertRaises(SSLTestException, ssl.verify_ssl_pem, "non-existing-file")

    def test_verify_ssl_ca_calls_openssl_with_filenames(self):
        ssl.verify_ssl_ca("my_crt_file", "my_ca_file")
        self.mock_check_output.assert_called_once_with(["/usr/bin/openssl", "verify",
                                                        "-CAfile", "my_ca_file", "my_crt_file"],
                                                       shell=False, stderr=subprocess.STDOUT)

    def test_verify_ssl_ca_does_not_catch_exception_raised_by_subprocess(self):
        self.setUpPatch('subprocess.check_output', mock.Mock(side_effect=SSLTestException))
        self.assertRaises(SSLTestException, ssl.verify_ssl_ca, "non-existing-file", "non-existing-file")

    def test_disable_ssl_unlinks_required_files(self):
        with mock.patch('os.unlink') as mock_unlink:
            ssl.disable_ssl()
            mock_unlink.assert_has_calls([
                mock.call("/etc/ssl/private/hypernode.crt"),
                mock.call("/etc/ssl/private/hypernode.ca"),
                mock.call("/etc/apache2/sites-enabled/default-ssl")])

    def test_disable_ssl_restarts_apache_if_at_least_one_file_is_deleted(self):
        with mock.patch('os.unlink', mock.Mock(side_effect=[1, OSError(2, ""), OSError(2, "")])):
            ssl.disable_ssl()
            self.mock_call.assert_called_once_with(["service", "apache2", "restart"])

    def test_disable_ssl_catches_file_does_not_exist_exception_but_no_other_exception(self):
        with mock.patch('os.unlink', mock.Mock(side_effect=OSError(2, ""))):
            ssl.disable_ssl()

        with mock.patch('os.unlink', mock.Mock(side_effect=OSError(3, ""))):
            self.assertRaises(OSError, ssl.disable_ssl)


class IntegratedSSLConfig(tests.unit.BaseTestCase):

    def setUp(self):
        self.write_file = self.setUpPatch('hypernode.nodeconfig.common.write_file')
        self.subprocess_call = self.setUpPatch('subprocess.call')
        self.check_output = self.setUpPatch('subprocess.check_output')
        self.unlink = self.setUpPatch('os.unlink')
        self.open = self.setUpPatch('__builtin__.open', mock.mock_open(read_data=template))

    def test_that_config_without_ssl_parameters_disables_ssl(self):
        config = {'app_name': 'testapp'}
        hypernode.nodeconfig.sslcerts.apply_config(config)
        self.assertEqual(self.unlink.call_count, 3)
        self.subprocess_call.assert_called_once_with(['service', 'apache2', 'restart'])

    def test_that_config_with_ssl_parameters_enables_ssl(self):
        config = {'app_name': 'testapp',
                  'ssl_common_name': 'cname',
                  'ssl_body': 'sslbody',
                  'ssl_certificate': 'sslcert',
                  'ssl_key_chain': 'sslchain'}
        hypernode.nodeconfig.sslcerts.apply_config(config)
        self.assertEqual(self.write_file.call_count, 3)
        self.assertEqual(self.get_written_file(hypernode.nodeconfig.sslcerts.CAPATH), 'sslchain')
        self.assertEqual(self.get_written_file(hypernode.nodeconfig.sslcerts.CRTPATH), 'sslcert\n\nsslbody')
        apacheconf = self.get_written_file('/etc/apache2/sites-enabled/default-ssl')
        self.assertRegexpMatches(apacheconf, r"ServerName\W+cname")
        self.assertRegexpMatches(apacheconf, r"SSLCertificateFile\W+" + hypernode.nodeconfig.sslcerts.CRTPATH)
        self.assertRegexpMatches(apacheconf, r"SSLCertificateChainFile\W+" + hypernode.nodeconfig.sslcerts.CAPATH)
        self.subprocess_call.assert_called_once_with(['service', 'apache2', 'restart'])

    def test_that_config_with_ssl_parameters_without_chain_enables_ssl(self):
        config = {'app_name': 'testapp',
                  'ssl_common_name': 'cname',
                  'ssl_body': 'sslbody',
                  'ssl_certificate': 'sslcert',
                  'ssl_key_chain': ''}
        hypernode.nodeconfig.sslcerts.apply_config(config)
        self.assertEqual(self.write_file.call_count, 2)
        self.assertFalse(self.get_written_file(hypernode.nodeconfig.sslcerts.CAPATH))
        self.assertEqual(self.get_written_file(hypernode.nodeconfig.sslcerts.CRTPATH), 'sslcert\n\nsslbody')
        apacheconf = self.get_written_file('/etc/apache2/sites-enabled/default-ssl')
        self.assertRegexpMatches(apacheconf, r"ServerName\W+cname")
        self.assertRegexpMatches(apacheconf, r"SSLCertificateFile\W+" + hypernode.nodeconfig.sslcerts.CRTPATH)
        self.assertNotRegexpMatches(apacheconf, r"SSLCertificateChainFile")
        self.subprocess_call.assert_called_once_with(['service', 'apache2', 'restart'])

    def test_that_config_with_missing_parameter_raises_exception(self):
        config = {'app_name': 'testapp',
                  'ssl_common_name': 'cname',
                  'ssl_certificate': 'sslcert',
                  'ssl_key_chain': ''}
        self.assertRaises(RuntimeError, hypernode.nodeconfig.sslcerts.apply_config, config)

    def get_written_file(self, filename):
        for call in self.write_file.mock_calls:
            if call[1][0] == filename:
                return call[1][1]
        return False

# This template is copied from the puppet-ami repo
template = """
<IfModule mod_ssl.c>
    Listen 443

    <VirtualHost _default_:443>
        ServerAdmin support@hypernode.com
        ServerName  {{ servername }}

        DocumentRoot /home/user/docroot/

        <Directory />
            Options FollowSymLinks
            AllowOverride None
        </Directory>
        <Directory /home/user/docroot/>
            Options -Indexes FollowSymLinks MultiViews
            AllowOverride All
            Order allow,deny
            allow from all
        </Directory>

        ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
        <Directory /usr/lib/cgi-bin>
            AllowOverride None
            Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
            Order allow,deny
            Allow from all
        </Directory>

        <IfModule mod_dir.c>
            DirectoryIndex index.html index.php
        </IfModule>

        CustomLog /var/log/apache2/access.log combined
        ErrorLog /var/log/apache2/error.log
        LogLevel warn

        <Files ~ "\.(cgi|shtml|phtml|php[34]?|pl)$">
            SSLOptions        +StdEnvVars
        </Files>

        SSLEngine            On
        SSLCipherSuite       RSA:!EXP:!NULL:+HIGH:+MEDIUM:-LOW:!MD5
        SetEnvIf             User-Agent ".*MSIE.*" nokeepalive ssl-unclean-shutdown downgrade-1.0 force-response-1.0

        SSLCertificateFile      {{ crtpath }}
{% if capath %}
        SSLCertificateChainFile {{ capath }}
{% endif %}
    </VirtualHost>
</IfModule>
"""


class SSLTestException(Exception):
    pass