import unittest
import sys
import os

# Add the parent directory (project root) to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from utils import simulate_network_error

class TestUtils(unittest.TestCase):
    def test_simulate_network_error(self):
        self.assertIsInstance(simulate_network_error(), bool)

if __name__ == "__main__":
    unittest.main()
