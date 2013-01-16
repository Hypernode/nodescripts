import tests.unit
import hypernode.log
import mock
import sys
import logging


class TestLogging(tests.unit.BaseTestCase):

    def test_get_logger_returns_logger_with_given_name_or_default(self):
        logger = hypernode.log.getLogger("henk")
        self.assertEqual("Logger", logger.__class__.__name__)
        self.assertEqual(logger.name, "henk")

        logger = hypernode.log.getLogger()
        self.assertEqual("Logger", logger.__class__.__name__)
        self.assertEqual(logger.name, "hypernode.log")

    def test_attach_console_handler_attaches_streamhandler(self):
        logger = mock.Mock()

        with mock.patch("logging.StreamHandler") as mock_handler:
            mock_handler_instance = mock_handler.return_value = mock.Mock()

            hypernode.log.attachConsoleHandler(logger)

            mock_handler.assert_called_once_with(sys.stdout)
            logger.addHandler.assert_called_once_with(mock_handler_instance)

    def test_attach_console_handler_sets_loglevel_to_debug(self):
        logger = mock.Mock()

        with mock.patch("logging.StreamHandler") as mock_handler:
            mock_handler_instance = mock_handler.return_value = mock.Mock()
            hypernode.log.attachConsoleHandler(logger)
            mock_handler_instance.setLevel.assert_called_once_with(logging.DEBUG)

    def test_attach_syslog_handler_attaches_sysloghandler(self):
        logger = mock.Mock()

        with mock.patch("logging.handlers.SysLogHandler") as mock_handler:
            mock_handler_instance = mock_handler.return_value = mock.Mock()

            hypernode.log.attachSyslogHandler(logger)

            mock_handler.assert_called_once_with(address="/dev/log")  # we created one object
            logger.addHandler.assert_called_once_with(mock_handler_instance)

    def test_attach_syslog_handler_sets_loglevel_to_info(self):
        logger = mock.Mock()

        with mock.patch("logging.handlers.SysLogHandler") as mock_handler:
            mock_handler_instance = mock_handler.return_value = mock.Mock()
            hypernode.log.attachSyslogHandler(logger)
            mock_handler_instance.setLevel.assert_called_once_with(logging.INFO)

    ###
    # Buffer handler
    ###
    def test_buffer_handler_has_buffer_attribute(self):
        logbuffer = hypernode.log.MyBufferHandler()
        logbuffer.buffer

    def test_buffer_handler_method_flush_does_nothing(self):
        bufferhandler = hypernode.log.MyBufferHandler(10)
        bufferhandler.buffer = ["a"]
        bufferhandler.flush()
        self.assertEqual(bufferhandler.buffer, ["a"])

    def test_buffer_handler_method_truncate_empties_buffer(self):
        bufferhandler = hypernode.log.MyBufferHandler(10)
        bufferhandler.buffer = ["a"]
        bufferhandler.truncate()
        self.assertEqual(bufferhandler.buffer, [])

    def test_buffer_handler_method_shouldflush_returns_false(self):
        bufferhandler = hypernode.log.MyBufferHandler(1)
        bufferhandler.buffer = ["a"]
        self.assertFalse(bufferhandler.shouldFlush("a"))

    def test_buffer_handler_method_format_buffer_formats_entire_buffer_into_strings(self):
        bufferhandler = hypernode.log.MyBufferHandler()
        bufferhandler.buffer = [1, 2, 3]
        bufferhandler.format = mock.Mock()
        bufferhandler.format.side_effect = ["a", "b", "c", "d", "e", "f"]
        result = bufferhandler.formatBuffer()
        self.assertEqual(result, ["a", "b", "c"])
        self.assertEqual(bufferhandler.format.call_count, 3)

    def test_attach_buffer_handler_attaches_and_returns_bufferhandler(self):
        logger = mock.Mock()

        with mock.patch("hypernode.log.MyBufferHandler") as mock_handler:
            mock_handler_instance = mock_handler.return_value = mock.Mock()

            logbuffer = hypernode.log.attachBufferHandler(logger)

            self.assertIs(logbuffer, mock_handler_instance)
            mock_handler.assert_called_once()  # we created one object
            logger.addHandler.assert_called_once_with(mock_handler_instance)

    def test_attach_buffer_handler_sets_loglevel_to_debug(self):
        logger = mock.Mock()

        with mock.patch("hypernode.log.MyBufferHandler") as mock_handler:
            mock_handler_instance = mock_handler.return_value = mock.Mock()
            hypernode.log.attachBufferHandler(logger)
            mock_handler_instance.setLevel.assert_called_once_with(logging.DEBUG)
