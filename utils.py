import random

# Constants
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
CHUNK_SIZE = 1024  # 1 KB

# Utility Functions
def simulate_network_error():
    # Simulate a 10% chance of network error
    return random.random() < 0.1