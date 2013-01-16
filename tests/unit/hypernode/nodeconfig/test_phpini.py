
import mock
import tests.unit

import hypernode.nodeconfig.phpini as phpini


class TestPHPIni(tests.unit.BaseTestCase):

    def setUp(self):
        self.fixture = {"php_options": {"options": {"apc.stat": 1}, "extensions": ["ioncube"], "other": "value"}}

        self.mock_call = self.setUpPatch('subprocess.call')

        self.mock_checkvars = self.setUpPatch('hypernode.nodeconfig.common.check_vars')
        self.mock_writefile = self.setUpPatch('hypernode.nodeconfig.common.write_file')
        self.mock_template_contents = mock.Mock()
        self.mock_filltemplate = self.setUpPatch('hypernode.nodeconfig.common.fill_template',
                                                 themock=mock.Mock(return_value=self.mock_template_contents))

    def test_apply_config_checks_phpoptions(self):
        phpini.apply_config(self.fixture)
        self.mock_checkvars.assert_called_once_with(self.fixture, ["php_options"])

    def test_apply_config_does_not_catch_exception_if_check_var_croaks(self):
        self.mock_checkvars = self.setUpPatch('hypernode.nodeconfig.common.check_vars',
                                              themock=mock.Mock(side_effect=ValueError))
        self.assertRaises(ValueError, phpini.apply_config, self.fixture)
        self.mock_checkvars.assert_called_once_with(self.fixture, ["php_options"])

    def test_apply_config_writes_template_to_hypernode_ini(self):
        phpini.apply_config(self.fixture)
        self.mock_writefile.assert_called_once_with("/etc/php5/conf.d/99.hypernode.ini",
                                                    self.mock_template_contents)
        self.mock_filltemplate.assert_called_once_with("/etc/hypernode/templates/20.phpini",
                                                       {"options": {"apc.stat": 1},
                                                        "extensions": {"ioncube": True}})

    def test_apply_config_restarts_phpfpm(self):
        phpini.apply_config(self.fixture)
        self.mock_call.assert_called_once_with(["service", "php5-fpm", "restart"])

    def test_apply_config_returns_zero(self):
        ret = phpini.apply_config(self.fixture)
        self.assertEqual(ret, 0)
