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

            # Reassemble file chunks sent back by the server.
            received_data = b""
            while True:
                # Read the header for each chunk.
                header = self.client_socket.recv(1024).decode().strip()
                if header == "END":
                    break  # End marker received.
                parts = header.split("|")
                if len(parts) != 4:
                    break  # Improper header; assume end of chunks.
                # Unpack header parts: client_id, sequence number, chunk length, and expected chunk checksum.
                _, seq_num, chunk_length, expected_chunk_checksum = parts
                chunk_length = int(chunk_length)
                # Receive the specified chunk of data.
                chunk = self.client_socket.recv(chunk_length)
                # Compute the checksum of the received chunk.
                actual_chunk_checksum = hashlib.sha256(chunk).hexdigest()
                if actual_chunk_checksum == expected_chunk_checksum:
                    # If valid, send OK and append the chunk.
                    self.client_socket.send("OK".encode())
                    received_data += chunk
                else:
                    # If corrupted, request retransmission.
                    print(f"Chunk {seq_num} corrupted. Requesting retransmission.")
                    self.client_socket.send("RESEND".encode())
                    # Do not append; the server will resend the same chunk.

            # Receive the overall checksum from the server.
            overall_checksum = self.client_socket.recv(1024).decode().strip()

            # Verify the overall checksum.
            computed_checksum = hashlib.sha256(received_data).hexdigest()
            if computed_checksum == overall_checksum:
                print(f"File transfer successful. Checksum verified: {overall_checksum}")
            else:
                print(f"Checksum mismatch. Expected: {overall_checksum}, Computed: {computed_checksum}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.client_socket.close()

if __name__ == "__main__":
    file_path = input("Enter file path to upload: ")
    client = Client(file_path)
    client.upload_file()
