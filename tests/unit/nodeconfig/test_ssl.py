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
            "ssl_key_chain": "",
            "ssl_common_name": "",
            "ssl_body": ""
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
        del config["ssl_key_chain"]
        self.assertRaises(Exception, ssl.apply_config, config)

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
        ret = ssl.apply_config(self.fixture)
        mock_verify.assert_called_once_with(self.fixture['ssl_certificate'],
                                            self.fixture['ssl_body'],
                                            self.fixture['ssl_key_chain'])
        self.assertEquals(0, ret)

    def test_apply_config_returns_1_when_ssl_certificate_is_invalid(self):
        mock_verify = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl', mock.Mock(return_value=False))
        ret = ssl.apply_config(self.fixture)
        mock_verify.assert_called_once_with(self.fixture['ssl_certificate'],
                                            self.fixture['ssl_body'],
                                            self.fixture['ssl_key_chain'])
        self.assertEquals(1, ret)

    def test_apply_config_writes_certificate_if_valid(self):
        self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl', mock.Mock(return_value=True))
        ret = ssl.apply_config(self.fixture)

        self.mock_writefile.assert_any_call("/etc/ssl/private/hypernode.ca", self.fixture['ssl_key_chain'], umask=0077)
        self.mock_writefile.assert_any_call("/etc/ssl/private/hypernode.crt", "%s\n\n%s" %
                                            (self.fixture['ssl_certificate'],
                                             self.fixture['ssl_body']), umask=0077)
        self.assertEquals(0, ret)

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

    def test_verify_ssl_catches_exception_from_verify_ssl_pem_and_returns_false(self):
        mock_verifypem = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_pem', mock.Mock(side_effect=SSLTestException))
        mock_verifyca = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_ca', mock.Mock())

        ret = ssl.verify_ssl('my_crt', 'my_key', 'my_ca')

        assert mock_verifypem.called
        assert not mock_verifyca.called
        self.assertEqual(ret, False)

    def test_verify_ssl_catches_exception_from_verify_ssl_ca_and_returns_false(self):
        verify_ssl_pem = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_pem')
        verify_ssl_ca = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_ca', mock.Mock(side_effect=SSLTestException))

        ret = ssl.verify_ssl('my_crt', 'my_key', 'my_ca')

        assert verify_ssl_pem.called
        assert verify_ssl_ca.called
        self.assertEqual(ret, False)

    def test_verify_ssl_returns_true_if_verification_succeeds(self):
        verify_ssl_pem = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_pem')
        verify_ssl_ca = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_ca')

        ret = ssl.verify_ssl('my_crt', 'my_key', 'my_ca')

        assert verify_ssl_pem.called
        assert verify_ssl_ca.called
        self.assertEqual(ret, True)

    def test_verify_ssl_does_not_verify_ca_if_pem_invalid(self):
        mock_verifypem = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_pem', mock.Mock(side_effect=SSLTestException))
        mock_verifyca = self.setUpPatch('hypernode.nodeconfig.sslcerts.verify_ssl_ca', mock.Mock())

        ssl.verify_ssl('my_crt', 'my_key', 'my_ca')

        assert mock_verifypem.called
        assert not mock_verifyca.called

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

    def test_verify_ssl_returns_false_if_crt_invalid(self):
        hypernode.nodeconfig.sslcerts.verify_ssl_pem = mock.Mock(return_value=False)
        hypernode.nodeconfig.sslcerts.verify_ssl_ca = mock.Mock()

    def test_disable_ssl_unlinks_required_files(self):
        with mock.patch('os.unlink') as mock_unlink:
            ssl.disable_ssl()
            mock_unlink.assert_has_calls([
                mock.call("/etc/ssl/private/hypernode.crt"),
                mock.call("/etc/ssl/private/hypernode.ca"),
                mock.call("/etc/apache2/sites-enabled/default-ssl")])

    def test_disable_ssl_raises_no_exception_if_file_does_not_exist(self):
        with mock.patch('os.unlink', mock.Mock(side_effect=[OSError(2, ""), 1, OSError(2, "")])) as mock_unlink:
            ssl.disable_ssl()
            self.assertIs(mock_unlink.call_count, 3)

    def test_disable_ssl_restarts_apache_if_at_least_one_file_is_deleted(self):
        with mock.patch('os.unlink', mock.Mock(side_effect=[1, OSError(2, ""), OSError(2, "")])):
            ssl.disable_ssl()
            self.mock_call.assert_called_once_with(["service", "apache2", "restart"])


class SSLTestException(Exception):
    pass
