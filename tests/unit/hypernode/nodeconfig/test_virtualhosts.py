import mock
import tests.unit

import hypernode.nodeconfig.virtualhostname as vhost


class TestSetup(tests.unit.BaseTestCase):

    def setUp(self):
        self.fixture = {"hostnames": ["hostname1", "hostname2"], "other": "value"}

        self.mock_call = self.setUpPatch('subprocess.call')

        self.mock_checkvars = self.setUpPatch('hypernode.nodeconfig.common.check_vars')
        self.mock_writefile = self.setUpPatch('hypernode.nodeconfig.common.write_file')
        self.mock_template_output = mock.Mock()  # use a mock object so we have a unique value
        self.mock_filltemplate = self.setUpPatch('hypernode.nodeconfig.common.fill_template',
                                                 themock=mock.Mock(return_value=self.mock_template_output))

    def test_apply_config_checks_if_hostnames_are_set(self):
        vhost.apply_config(self.fixture)
        self.mock_checkvars.assert_called_once_with(self.fixture, ["hostnames"])

    def test_apply_config_does_not_handle_exceptions_by_check_vars(self):
        self.mock_checkvars = self.setUpPatch('hypernode.nodeconfig.common.check_vars',
                                              mock.Mock(side_effect=ValueError))
        self.assertRaises(ValueError, vhost.apply_config, self.fixture)

    def test_apply_config_writes_template_output_to_default_vhost_config(self):
        vhost.apply_config(self.fixture)
        self.mock_writefile.assert_called_once_with("/etc/apache2/sites-enabled/default",
                                                    self.mock_template_output)

    def test_apply_config_finds_template_in_right_place(self):
        vhost.apply_config(self.fixture)
        self.mock_filltemplate.assert_called_once_with("/etc/hypernode/templates/10.hostnames.default-vhost",
                                                       {'hostnames': self.fixture["hostnames"]})

    def test_apply_config_restarts_apache(self):
        vhost.apply_config(self.fixture)
        self.mock_call.assert_called_once_with(["service", "apache2", "restart"])