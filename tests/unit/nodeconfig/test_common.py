import sys
import mock
import tests.unit

from hypernode.nodeconfig.common import get_config, check_vars, write_file, fill_template


class TestSetup(tests.unit.BaseTestCase):

    def setUp(self):
        self.mock_open = self.setUpPatch('__builtin__.open', themock=mock.mock_open())
        self.mock_umask = self.setUpPatch('os.umask')

    def test_get_config_throws_exception_on_non_existing_configfile(self):
        with mock.patch('__builtin__.open', mock.Mock(side_effect=IOError)) as mock_open:
            self.assertRaises(IOError, get_config, "non-exist")
            mock_open.assert_called_once_with("non-exist", "r")

    def test_get_config_returns_empty_dict_on_invalid_configfile(self):
        with mock.patch('json.loads', mock.Mock(side_effect=ValueError)):
            ret = get_config("non-exist")
            self.assertEqual(ret, {})

    def test_get_config_returns_dict_of_config_file(self):
        with mock.patch('__builtin__.open', mock.mock_open(read_data='{}')) as mock_open:
            ret = get_config("non-exist")
            assert mock_open.called
            self.assertIsInstance(ret, dict)

    def test_check_vars_raises_exception_if_config_is_no_dict(self):
        self.assertRaises(ValueError, check_vars, "no-dict", ["a"])

    def test_check_vars_raises_exception_if_keynames_is_no_list(self):
        self.assertRaises(ValueError, check_vars, {}, "no-list")

    def test_check_vars_raises_exception_if_key_not_found(self):
        self.assertRaises(ValueError, check_vars, {}, ["mykey"])
        self.assertRaises(ValueError, check_vars, {"a": "b"}, ["mykey"])
        self.assertRaises(ValueError, check_vars, {"a": "b"}, ["a", "mykey"])

    def test_check_vars_raises_returns_nothing_if_all_keys_found(self):
        check_vars({}, [])
        check_vars({"a": "b"}, ["a"])
        check_vars({"a": "b", "b": "c"}, ["a", "b"])
        check_vars({"a": None}, ["a"])

    def test_write_file_sets_no_umask_if_none_supplied(self):
        write_file("no-file", "data")

        fd = self.mock_open()
        fd.write.assert_called_once_with("data")
        assert not self.mock_umask.called

    def test_write_file_sets_supplied_umask_and_restores_afterwards(self):
        with mock.patch('os.umask', mock.Mock(return_value=0022)) as mock_umask:
            write_file("no-file", "data", umask=0077)

            self.assertIs(len(mock_umask.mock_calls), 2)
            self.assertEqual(mock_umask.mock_calls[0], mock.call(0077))
            self.assertEqual(mock_umask.mock_calls[1], mock.call(0022))

    def test_write_file_restores_umask_if_open_fails(self):
        with mock.patch('__builtin__.open', mock.mock_open(mock=mock.Mock(side_effect=IOError))):
            with mock.patch('os.umask', mock.Mock(return_value=0022)) as mock_umask:

                self.assertRaises(IOError, write_file, "no-file", "data", umask=0077)
                self.assertIs(len(mock_umask.mock_calls), 2)
                self.assertEqual(mock_umask.mock_calls[0], mock.call(0077))
                self.assertEqual(mock_umask.mock_calls[1], mock.call(0022))

    def test_write_file_writes_given_data(self):
        write_file("my-file", "my-data")
        self.mock_open.assert_called_once_with("my-file", "w")
        fd = self.mock_open()
        fd.write.assert_called_once_with("my-data")

    def test_fill_template_opens_template_and_fills_in_variables(self):
        with mock.patch('__builtin__.open', mock.mock_open(read_data='henk')) as mock_open:
            with mock.patch('django.template.Template') as mock_template:
                mock_template_instance = mock_template.return_value = mock.Mock()

                with mock.patch('django.template.Context') as mock_context:
                    mock_context_instance = mock_context.return_value = mock.Mock()

                    fill_template("sdfdsfdfs", {"a": 1})
                    mock_open.assert_called_once_with("sdfdsfdfs", "r")
                    mock_template.assert_called_once_with("henk")
                    mock_context.assert_called_once_with({"a": 1})

                    mock_template_instance.render.assert_called_once_with(mock_context_instance)

