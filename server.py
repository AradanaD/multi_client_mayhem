import socket
import threading
import hashlib
import random
import os
from utils import CHUNK_SIZE, SERVER_HOST, SERVER_PORT, simulate_network_error

class Server:
    def __init__(self):
        self.clients = {}
        self.lock = threading.Lock()

    def handle_client(self, client_socket, client_id):
        try:
            # Receive combined metadata (file name and file size)
            metadata = client_socket.recv(1024).decode().strip()
            file_name, file_size_str = metadata.split("|")
            file_size = int(file_size_str)
            print(f"Client {client_id}: Uploading {file_name} ({file_size} bytes)")

            # Send ACK so the client can start sending file data
            client_socket.send("ACK".encode())

            # Receive file data in binary mode
            file_data = b""
            while len(file_data) < file_size:
                chunk = client_socket.recv(CHUNK_SIZE)
                if not chunk:
                    break
                file_data += chunk

            # Optionally simulate a network error (corrupt file data)
            if simulate_network_error():
                print(f"Simulating network error for Client {client_id}")
                file_data = self.corrupt_data(file_data)

            # Compute overall checksum for the received file data
            overall_checksum = hashlib.sha256(file_data).hexdigest()

            # Split file data into chunks for sending back
            chunks = [file_data[i:i+CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)]

            # Send each chunk back with a header containing:
            # client_id | sequence number | chunk length | chunk checksum
            for seq_num, chunk in enumerate(chunks):
                chunk_checksum = hashlib.sha256(chunk).hexdigest()
                header = f"{client_id}|{seq_num}|{len(chunk)}|{chunk_checksum}"
                client_socket.send(header.encode())
                client_socket.send(chunk)

                # Wait for acknowledgment from the client for this chunk.
                # If the client sends "RESEND", resend the same header and chunk.
                ack = client_socket.recv(1024).decode().strip()
                while ack != "OK":
                    print(f"Resending chunk {seq_num} to Client {client_id} upon request.")
                    client_socket.send(header.encode())
                    client_socket.send(chunk)
                    ack = client_socket.recv(1024).decode().strip()

            # Send an end marker to indicate that all chunks have been sent.
            client_socket.send("END".encode())

            # Send the overall checksum to the client.
            client_socket.send(overall_checksum.encode())

            print(f"Client {client_id}: File transfer complete. Overall Checksum: {overall_checksum}")

        except Exception as e:
            print(f"Client {client_id}: Error - {e}")
        finally:
            client_socket.close()

    def corrupt_data(self, data):
        # Randomly corrupt one byte in the data.
        if data:
            index = random.randint(0, len(data) - 1)
            data = data[:index] + bytes([data[index] ^ 0xFF]) + data[index+1:]
        return data

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((SERVER_HOST, SERVER_PORT))
        server_socket.listen(5)
        print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

        client_id = 0
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Accepted connection from {addr}")
            client_id += 1
            threading.Thread(target=self.handle_client, args=(client_socket, client_id)).start()

if __name__ == "__main__":
    server = Server()
    server.start()
