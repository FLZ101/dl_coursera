import unittest


class TestMisc(unittest.TestCase):
    def test_pypi_api(self):
        from dl_coursera.lib.misc import get_latest_app_version

        ver = get_latest_app_version()
        self.assertEqual(len(ver), 3)
