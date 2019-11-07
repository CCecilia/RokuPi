import os
from pathlib import Path
import unittest


class TestChannelMethods(unittest.TestCase):

    def setUp(self):
        Path('.', exist_ok=True).mkdir('tmp')
        print(self.temp_dir)

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')


if __name__ == '__main__':
    unittest.main()