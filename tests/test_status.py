import unittest

from mink.status import read_status


class StatusTests(unittest.TestCase):
    def test_status_has_safe_fields(self):
        status = read_status(0)
        self.assertTrue(status.hostname)
        self.assertTrue(status.uptime)
        self.assertTrue(status.cpu)
        self.assertTrue(status.memory)


if __name__ == "__main__":
    unittest.main()
