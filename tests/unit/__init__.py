
import unittest
import mock


class BaseTestCase(unittest.TestCase):

    def setUpPatch(self, topatch, themock=None):
        if themock is None:
            themock = mock.Mock()

        patcher = mock.patch(topatch, themock)
        self.addCleanup(patcher.stop)
        return patcher.start()

    # create alias
    set_up_patch = setUpPatch