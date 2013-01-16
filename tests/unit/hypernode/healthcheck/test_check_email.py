import tests.unit
from hypernode.healthcheck.mailout import send_mail, check_delivery, raise_sos
from smtplib import SMTPConnectError, SMTPSenderRefused, SMTPRecipientsRefused, SMTPDataError
import mock
import socket


class TestSendmail(tests.unit.BaseTestCase):

    def setUp(self):
        self.mock_smtp = mock.Mock()
        self.mock_smtp.mail.return_value = (250, "OK")
        self.mock_smtp.rcpt.return_value = (250, "OK")
        self.mock_smtp.data.return_value = (250, "2.0.0 Ok: queued as 8E220500567")

        self.msc = self.set_up_patch('smtplib.SMTP')
        self.msc.return_value = self.mock_smtp

        self.send_mail_arguments = {"smtphost": "localhost",
                                    "smtpport": 25,
                                    "recipient": "testrecipient@hypernode.com",
                                    "sender": "testsender@hypernode.com",
                                    "subject": "subject",
                                    "body": "body"}

    def test_send_mail_accepts_smtphost_smtpport_recipient_sender_subject_and_body(self):
        send_mail(self.send_mail_arguments)

    def test_send_mail_does_not_require_arguments(self):
        send_mail()

    def test_send_mail_raises_exception_when_connect_to_mailserver_fails(self):
        self.msc.side_effect = SMTPConnectError("a", "b")
        with self.assertRaises(SMTPConnectError):
            send_mail(**self.send_mail_arguments)

        # also catch socket.error
        self.msc.side_effect = socket.error()
        with self.assertRaises(SMTPConnectError):
            send_mail(**self.send_mail_arguments)

    def test_send_mail_raises_exception_when_setting_sender_fails(self):
        self.mock_smtp.mail.return_value = (0, "Sender Refused")
        with self.assertRaises(SMTPSenderRefused):
            send_mail(**self.send_mail_arguments)

    def test_send_mail_raises_exception_when_setting_recipient_fails(self):
        self.mock_smtp.rcpt.return_value = (0, "Sender Refused")
        with self.assertRaises(SMTPRecipientsRefused):
            send_mail(**self.send_mail_arguments)

    def test_send_mail_raises_exception_when_sending_body_fails(self):
        self.mock_smtp.data.return_value = (0, "not ok")
        with self.assertRaises(SMTPDataError):
            send_mail(**self.send_mail_arguments)

    def test_send_mail_raises_exception_when_no_queueid_found_in_data_response(self):
        self.mock_smtp.data.return_value = (250, "not ok")
        with self.assertRaises(ValueError):
            send_mail(**self.send_mail_arguments)

    def test_send_mail_returns_queue_id(self):
        queueid = send_mail(**self.send_mail_arguments)
        self.assertEqual(queueid, "8E220500567")


class TestCheckDelivery(tests.unit.BaseTestCase):

    def setUp(self):
        self.sample_log = ("\n"
                           "Jan 11 10:39:13 allard postfix/smtpd[2087]: connect from localhost[127.0.0.1]\n"
                           "Jan 11 10:39:13 allard postfix/smtpd[2087]: E8313500567: client=localhost[127.0.0.1]\n"
                           "Jan 11 10:39:13 allard postfix/cleanup[2091]: E8313500567: message-id=<20130111093913.E8313500567@allard-desktop.r139.net>\n"
                           "Jan 11 10:39:14 allard postfix/qmgr[27566]: E8313500567: from=<testsender@hypernode.com>, size=351, nrcpt=1 (queue active)\n"
                           "Jan 11 10:39:14 allard postfix/smtpd[2087]: disconnect from localhost[127.0.0.1]\n"
                           "Jan 11 10:39:14 allard postfix/smtp[2100]: E8313500567: to=<testrecipient@hypernode.com>, relay=smtp.hypernode.com[82.94.214.140]:2525, delay=0.16, delays=0.09/0/0.05/0.01, dsn=2.0.0, status=sent (250 2.0.0 Ok: queued as 18E578E802)\n"
                           "Jan 11 10:39:14 allard postfix/qmgr[27566]: E8313500567: removed\n"
                           )

    def test_check_delivery_croaks_if_no_messageid(self):
        with self.assertRaises(ValueError):
            check_delivery(None, [])

    def test_check_delivery_returns_false_when_no_lines_match(self):
        self.assertFalse(check_delivery("E8313500567", []))
        self.assertFalse(check_delivery("E8313500567", ["asdadsf"]))

    def test_check_delivery_returns_true_when_delivery_is_seen(self):
        self.assertTrue(check_delivery("E8313500567", self.sample_log.split("\n")))
        pass


class TestRaiseSOS(tests.unit.BaseTestCase):

    def setUp(self):
        self.logger = self.set_up_patch('hypernode.log.getLogger')

    def test_raise_sos_posts_to_callback_url(self):
        get_deployment_config = self.set_up_patch('hypernode.nodeconfig.common.get_config')
        get_deployment_config.return_value = {'sos_url': 'my_url'}

        mock_post = self.set_up_patch('requests.post')
        data = {'message': "Help!"}

        ret = raise_sos("Help!")

        assert get_deployment_config.called
        mock_post.assert_called_once_with('my_url', data=data)

    def test_raise_sos_raises_keyerror_if_sos_url_not_found(self):
        get_deployment_config = self.set_up_patch('hypernode.nodeconfig.common.get_config')
        get_deployment_config.return_value = {'noop': 'my_url'}

        self.assertRaises(KeyError, raise_sos, "Help!")

    def test_raise_sos_returns_true_if_status_code_200(self):
        get_deployment_config = self.set_up_patch('hypernode.nodeconfig.common.get_config')
        get_deployment_config.return_value = {'sos_url': 'my_url'}

        mock_post = self.set_up_patch('requests.post')
        mock_post.return_value.status_code = 200

        ret = raise_sos("Help!")

        self.assertTrue(ret)

    def test_raise_sos_returns_false_if_status_code_not_200(self):
        get_deployment_config = self.set_up_patch('hypernode.nodeconfig.common.get_config')
        get_deployment_config.return_value = {'sos_url': 'my_url'}

        mock_post = self.set_up_patch('requests.post')
        mock_post.return_value.status_code = 403

        ret = raise_sos("Help!")

        self.assertFalse(ret)

    def test_raise_sos_catches_ioexception_and_logs_and_returns_false(self):
        mock_getdepconf = self.set_up_patch('hypernode.nodeconfig.common.get_config')
        mock_getdepconf.side_effect = IOError()

        ret = raise_sos("Henk!")

        self.logger.return_value.critical.assert_called_once()
        self.assertFalse(ret)