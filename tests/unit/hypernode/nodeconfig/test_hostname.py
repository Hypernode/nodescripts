import mock
import tests.unit

import hypernode.nodeconfig.hostname as hostname


class TestSetup(tests.unit.BaseTestCase):

    def setUp(self):
        self.fixture = {"hostnames": ["hostname1", "hostname2"], "app_name": "appname1", "other": "value"}

        self.mock_call = self.setUpPatch('subprocess.call')

        self.mock_checkvars = self.setUpPatch('hypernode.nodeconfig.common.check_vars')
        self.mock_writefile = self.setUpPatch('hypernode.nodeconfig.common.write_file')
        self.mock_template_contents = "henk"
        self.mock_filltemplate = self.setUpPatch('hypernode.nodeconfig.common.fill_template',
                                                 themock=mock.Mock(return_value=self.mock_template_contents))

    def test_apply_config_checks_hostnames_and_appname_vars(self):
        hostname.apply_config(self.fixture)
        self.mock_checkvars.assert_called_once_with(self.fixture, ["hostnames", "app_name"])

    def test_apply_config_does_not_catch_exception_if_check_var_croaks(self):
        self.mock_checkvars = self.setUpPatch('hypernode.nodeconfig.common.check_vars',
                                              themock=mock.Mock(side_effect=ValueError))
        self.assertRaises(ValueError, hostname.apply_config, self.fixture)
        self.mock_checkvars.assert_called_once_with(self.fixture, ["hostnames", "app_name"])

    def test_apply_config_writes_appname_to_etc_hostname(self):
        hostname.apply_config(self.fixture)
        self.mock_writefile.assert_any_call("/etc/hostname", self.fixture["app_name"])

    def test_apply_config_writes_template_to_etc_hosts(self):
        hostname.apply_config(self.fixture)

        self.mock_filltemplate.assert_called_once_with("/etc/hypernode/templates/03.hostname.hosts",
                                                       {'hostnames': self.fixture['hostnames'],
                                                        'app_name': self.fixture['app_name']})

        self.mock_writefile.assert_any_call("/etc/hosts", self.mock_template_contents)

    def test_apply_config_calls_hostname_to_set_hostname(self):
        hostname.apply_config(self.fixture)
        self.mock_call.assert_any_call(["hostname", self.fixture["app_name"]])

    def test_apply_config_restarts_syslog(self):
        hostname.apply_config(self.fixture)
        self.mock_call.assert_any_call(["service", "rsyslog", "restart"])