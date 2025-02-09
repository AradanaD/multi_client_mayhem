import unittest
import threading
import socket
import hashlib
import time
import os
import sys

# Add the parent directory (project root) to sys.path so that client and utils can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from client import Client
from utils import SERVER_HOST, SERVER_PORT, CHUNK_SIZE

def dummy_server():
    """
    A simple dummy server that follows the same protocol as the real server:
      - Receives metadata (file_name|file_size)
      - Sends an ACK
      - Receives file data until file_size bytes are read
      - Splits the file data into chunks and sends them back with headers
      - Sends the checksum of the file data
    """
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((SERVER_HOST, SERVER_PORT))
    server_sock.listen(1)
    
    conn, addr = server_sock.accept()
    try:
        # Receive metadata
        metadata = conn.recv(1024).decode().strip()
        file_name, file_size_str = metadata.split("|")
        file_size = int(file_size_str)
        
        # Send ACK so client can start sending file data
        conn.send("ACK".encode())
        
        # Receive file data
        file_data = b""
        while len(file_data) < file_size:
            chunk = conn.recv(CHUNK_SIZE)
            if not chunk:
                break
            file_data += chunk

        # Compute checksum for the received file data
        checksum = hashlib.sha256(file_data).hexdigest()

        # Split file data into chunks
        chunks = [file_data[i:i+CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)]
        
        # Send each chunk with a header: "client_id|seq_num|<chunk_length>"
        for seq_num, chunk in enumerate(chunks):
            header = f"1|{seq_num}|{len(chunk)}"  # using "1" as a dummy client id
            conn.send(header.encode())
            conn.send(chunk)
        
        # Send the checksum to the client
        conn.send(checksum.encode())
    finally:
        conn.close()
        server_sock.close()

class TestClient(unittest.TestCase):
    def test_upload_file(self):
        # Create a dummy file for testing
        file_path = "dummy_test_file.txt"
        file_content = "This is a test file."
        with open(file_path, "w") as f:
            f.write(file_content)

        # Start the dummy server in a separate thread
        server_thread = threading.Thread(target=dummy_server, daemon=True)
        server_thread.start()

        # Give the dummy server a moment to start
        time.sleep(0.5)

        # Create the client and attempt to upload the file
        client = Client(file_path)
        try:
            client.upload_file()  # This should complete without exceptions
            self.assertTrue(True)  # If we reach here, the test passes.
        except Exception as e:
            self.fail(f"Client.upload_file() raised an exception: {e}")
        finally:
            # Clean up the dummy file after the test
            os.remove(file_path)
            # Optionally wait for the server thread to finish
            server_thread.join(timeout=1)

if __name__ == "__main__":
    unittest.main()
