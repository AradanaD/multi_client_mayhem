# 


import socket
import os
import hashlib
from utils import SERVER_HOST, SERVER_PORT, CHUNK_SIZE

class Client:
    def __init__(self, file_path):
        self.file_path = file_path
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def upload_file(self):
        try:
            self.client_socket.connect((SERVER_HOST, SERVER_PORT))
            file_name = os.path.basename(self.file_path)
            file_size = os.path.getsize(self.file_path)

            # Send combined metadata (file name and file size)
            metadata = f"{file_name}|{file_size}"
            self.client_socket.send(metadata.encode())

            # Wait for ACK from the server
            ack = self.client_socket.recv(1024).decode().strip()
            if ack != "ACK":
                raise Exception("Did not receive proper ACK from server")

            # Send file data (in binary mode)
            with open(self.file_path, "rb") as file:
                while True:
                    chunk = file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    self.client_socket.send(chunk)

            # Receive file chunks (sent back by the server) and reassemble file
            received_data = b""
            while True:
                # Read the header for each chunk
                header = self.client_socket.recv(1024).decode().strip()
                if not header:
                    break  # No more data
                parts = header.split("|")
                if len(parts) != 3:
                    break  # Improper header; assume end of chunks
                # Unpack header parts (client_id, seq_num, chunk_size)
                _, _, chunk_size = parts
                # Read the specified chunk of data
                chunk = self.client_socket.recv(int(chunk_size))
                received_data += chunk

            # Receive checksum from server
            checksum = self.client_socket.recv(1024).decode().strip()

            # Verify checksum
            computed_checksum = hashlib.sha256(received_data).hexdigest()
            if computed_checksum == checksum:
                print(f"File transfer successful. Checksum verified: {checksum}")
            else:
                print(f"Checksum mismatch. Expected: {checksum}, Computed: {computed_checksum}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.client_socket.close()

if __name__ == "__main__":
    file_path = input("Enter file path to upload: ")
    client = Client(file_path)
    client.upload_file()
