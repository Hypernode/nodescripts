import tests.unit
import hypernode.nodeconfig.callback as callback
import hashlib
import json
import requests
import mock


class TestCallBack(tests.unit.BaseTestCase):

    def setUp(self):
        self.fixture = {"hostnames": ["hostname1", "hostname2"], "app_name": "appname1", "other": "value", "callback_url": "https://control.hypernode.com/nodeconfig/app/1/"}
        self.mock_checkvars = self.setUpPatch('hypernode.nodeconfig.common.check_vars')

        self.mock_response = mock.Mock()
        self.mock_response.status_code = 200
        self.mock_post = self.setUpPatch('requests.post')
        self.mock_post.return_value = self.mock_response

    ###
    # Success callback
    ###
    def test_call_success_checks_callback_url_var(self):
        callback.call_success(self.fixture)
        self.mock_checkvars.assert_called_once_with(self.fixture, ["callback_url", "app_name"])

    def test_call_success_croaks_if_callback_url_not_set(self):
        self.mock_checkvars.side_effect = ValueError
        self.assertRaises(ValueError, callback.call_success, self.fixture)

    def test_call_success_hashes_nodeconfig_to_create_hash(self):
        mock_hash = self.setUpPatch('hypernode.nodeconfig.callback.hash_deployment_config')
        callback.call_success(self.fixture)
        mock_hash.assert_called_with(self.fixture)

    def test_call_success_posts_to_callback_url(self):
        callback.call_success(self.fixture)
        postdata = {"applied_hash": callback.hash_deployment_config(self.fixture)}
        self.mock_post.assert_called_once_with(
            self.fixture["callback_url"],
            data=postdata,
            headers={'User-Agent': 'nodeconfig/callback for appname1'},
            verify=True)

    def test_call_success_does_not_handle_connection_errors(self):
        self.mock_post.side_effect = requests.ConnectionError
        self.assertRaises(requests.ConnectionError, callback.call_success, self.fixture)

    def test_call_success_raises_exception_if_post_fails(self):
        self.mock_response.status_code = 404
        with self.assertRaises(Exception):
            callback.call_success(self.fixture)

    def test_hash_deployment_config_returns_sha256_string(self):
        # hash is hex and 128 bits long
        hash = callback.hash_deployment_config(self.fixture)
        self.assertRegexpMatches(hash, r'^[a-f0-9]*$')
        self.assertEquals(len(hash), 128)

    def test_hash_deployment_returns_correct_hash(self):
        hash = hashlib.sha512(json.dumps(self.fixture)).hexdigest()
        self.assertEqual(hash, callback.hash_deployment_config(self.fixture))

    def test_call_success_checks_callback_url_var(self):
        callback.call_success(self.fixture)
        self.mock_checkvars.assert_called_once_with(self.fixture, ["callback_url", "app_name"])

    def test_call_success_croaks_if_callback_url_not_set(self):
        self.mock_checkvars.side_effect = ValueError
        self.assertRaises(ValueError, callback.call_success, self.fixture)

    def test_call_success_hashes_nodeconfig_to_create_hash(self):
        mock_hash = self.setUpPatch('hypernode.nodeconfig.callback.hash_deployment_config')
        callback.call_success(self.fixture)
        mock_hash.assert_called_with(self.fixture)

    def test_call_success_posts_to_callback_url(self):
        callback.call_success(self.fixture)
        postdata = {"applied_hash": callback.hash_deployment_config(self.fixture)}
        self.mock_post.assert_called_once_with(
            self.fixture["callback_url"],
            data=postdata,
            headers={'User-Agent': 'nodeconfig/callback for appname1'},
            verify=True)

    def test_call_success_does_not_handle_connection_errors(self):
        self.mock_post.side_effect = requests.ConnectionError
        self.assertRaises(requests.ConnectionError, callback.call_success, self.fixture)

    def test_call_success_raises_exception_if_post_fails(self):
        self.mock_response.status_code = 404
        with self.assertRaises(Exception):
            callback.call_success(self.fixture)

    ###
    # hash deployment config
    ###
    def test_hash_deployment_config_returns_sha256_string(self):
        # hash is hex and 128 bits long
        hash = callback.hash_deployment_config(self.fixture)
        self.assertRegexpMatches(hash, r'^[a-f0-9]*$')
        self.assertEquals(len(hash), 128)

    def test_hash_deployment_returns_correct_hash(self):
        hash = hashlib.sha512(json.dumps(self.fixture)).hexdigest()
        self.assertEqual(hash, callback.hash_deployment_config(self.fixture))

    ###
    # Error callback
    ###
    def test_call_error_checks_callback_url_var(self):
        callback.call_error(self.fixture, callback, Exception(), [])
        self.mock_checkvars.assert_called_once_with(self.fixture, ["callback_url", "app_name"])

    def test_call_error_hashes_nodeconfig_to_create_hash(self):
        mock_hash = self.setUpPatch('hypernode.nodeconfig.callback.hash_deployment_config')
        callback.call_error(self.fixture, callback, Exception(), [])
        mock_hash.assert_called_with(self.fixture)

    def test_call_error_croaks_if_callback_url_not_set(self):
        self.mock_checkvars.side_effect = ValueError
        self.assertRaises(ValueError, callback.call_error, self.fixture, callback, Exception(), [])

    def test_call_error_posts_to_callback_url(self):
        log = ["a", "b", "c"]
        e = Exception
        callback.call_error(self.fixture, callback, e, log)

        postdata = {"applied_hash": callback.hash_deployment_config(self.fixture),
                    "error": e,
                    "module": callback.__name__,
                    "log": "\n".join(log)}

        self.mock_post.assert_called_once_with(self.fixture["callback_url"],
                                               data=postdata,
                                               headers={'User-Agent': 'nodeconfig/callback for appname1'},
                                               verify=True)

    def test_call_error_does_not_handle_connection_errors(self):
        self.mock_post.side_effect = requests.ConnectionError
        self.assertRaises(requests.ConnectionError, callback.call_error, self.fixture, callback, Exception(), [])

    def test_call_error_raises_exception_if_post_fails(self):
        self.mock_response.status_code = 404
        with self.assertRaises(callback.CallbackException):
            callback.call_error(self.fixture, callback, Exception(), [])
