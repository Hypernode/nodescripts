import mock
import tests.unit

import hypernode.nodeconfig.cfninit as cfninit


class TestPHPIni(tests.unit.BaseTestCase):

    def setUp(self):
        self.fixture = {'region': 'my_region', 'app_name': 'my_app'}
        self.mock_call = self.setUpPatch('subprocess.call')
        self.mock_checkvars = self.setUpPatch('hypernode.nodeconfig.common.check_vars')

    def test_apply_config_calls_cfn_init(self):
        cfninit.apply_config(self.fixture)

        self.mock_call.assert_called_once_with(["/usr/local/bin/cfn-init", "-s", self.fixture["app_name"], "-r", "LaunchConfig", "--credential-file", "/etc/cfn/cfn-credentials", "--region", self.fixture["region"]])

    def test_apply_config_checks_appname_and_region_vars(self):
        cfninit.apply_config(self.fixture)
        self.mock_checkvars.assert_called_once_with(self.fixture, ["app_name", "region"])

    def test_apply_config_does_not_catch_exception_if_check_var_croaks(self):
        self.mock_checkvars = self.setUpPatch('hypernode.nodeconfig.common.check_vars',
                                              themock=mock.Mock(side_effect=ValueError))
        self.assertRaises(ValueError, cfninit.apply_config, self.fixture)
        self.mock_checkvars.assert_called_once_with(self.fixture, ["app_name", "region"])