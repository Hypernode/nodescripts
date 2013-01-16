import mock
import tests.unit

import hypernode.nodeconfig.pubkeys as pubkeys


class TestSetup(tests.unit.BaseTestCase):

    def setUp(self):
        self.fixture = {"public_keys": ["ssh-rsa henk", "ssh-rsa ingrid"], "other": "key"}

        self.mock_call = self.setUpPatch('subprocess.call')
        self.mock_mkdir = self.setUpPatch('os.mkdir')
        self.mock_chown = self.setUpPatch('os.chown')

        self.mock_checkvars = self.setUpPatch('hypernode.nodeconfig.common.check_vars')
        self.mock_writefile = self.setUpPatch('hypernode.nodeconfig.common.write_file')

    def test_apply_config_checks_if_pubkeys_are_set(self):
        pubkeys.apply_config(self.fixture)
        self.mock_checkvars.assert_called_once_with(self.fixture, ["public_keys"])

    def test_apply_config_does_not_handle_exceptions_by_check_vars(self):
        self.mock_checkvars = self.setUpPatch('hypernode.nodeconfig.common.check_vars',
                                              mock.Mock(side_effect=ValueError))
        self.assertRaises(ValueError, pubkeys.apply_config, self.fixture)

    def test_apply_config_dies_if_publickeys_var_is_not_an_array(self):
        # We iterate over the public_keys. We expect apply_config to croak if
        # the variable is not an array
        self.fixture["public_keys"] = False
        self.assertRaises(TypeError, pubkeys.apply_config, self.fixture)

    def test_apply_config_creates_the_users_dotssh_dir_if_not_exists(self):
        self.setUpPatch('os.path.isdir', mock.Mock(return_value=False))
        pubkeys.apply_config(self.fixture)
        self.mock_mkdir.assert_called_once_with(pubkeys.DOTSSH, 0755)

    def test_apply_config_does_not_create_dotssh_dir_if_exists(self):
        self.setUpPatch('os.path.isdir', mock.Mock(return_value=True))
        pubkeys.apply_config(self.fixture)
        self.assertEquals(len(self.mock_mkdir.mock_calls), 0)

    def test_apply_config_chowns_the_users_dotssh_dir(self):
        pubkeys.apply_config(self.fixture)
        self.mock_chown.assert_called_once_with(pubkeys.DOTSSH, 1000, 1000)

    def test_apply_config_writes_pubkeys_to_authkey_file(self):
        pubkeys.apply_config(self.fixture)
        contents = pubkeys.PREAMBLE + "ssh-rsa henk\n\nssh-rsa ingrid\n\n"
        self.mock_writefile.assert_called_once_with(pubkeys.AUTHKEYS, contents, umask=0022)

    def test_apply_config_returns_zero(self):
        ret = pubkeys.apply_config(self.fixture)
        self.assertEquals(ret, 0)
