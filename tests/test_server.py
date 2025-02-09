import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from server import Server

class TestServer(unittest.TestCase):
    def test_corrupt_data(self):
        server = Server()
        data = b"hello"
        corrupted_data = server.corrupt_data(data)
        self.assertNotEqual(data, corrupted_data)

if __name__ == "__main__":
    unittest.main()