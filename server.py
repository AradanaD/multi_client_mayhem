# import socket
# import threading
# import hashlib
# import random
# import os
# from utils import CHUNK_SIZE, SERVER_HOST, SERVER_PORT, simulate_network_error

# class Server:
#     def __init__(self):
#         self.clients = {}
#         self.lock = threading.Lock()

#     def handle_client(self, client_socket, client_id):
#         try:
#             # Receive file metadata
#             file_name = client_socket.recv(1024).decode()
#             file_size = int(client_socket.recv(1024).decode())
#             print(f"Client {client_id}: Uploading {file_name} ({file_size} bytes)")

#             # Receive file data
#             file_data = b""
#             while len(file_data) < file_size:
#                 chunk = client_socket.recv(CHUNK_SIZE)
#                 if not chunk:
#                     break
#                 file_data += chunk

#             # Simulate network error (drop or corrupt chunks)
#             if simulate_network_error():
#                 print(f"Simulating network error for Client {client_id}")
#                 file_data = self.corrupt_data(file_data)

#             # Compute checksum
#             checksum = hashlib.sha256(file_data).hexdigest()

#             # Split file into chunks
#             chunks = [file_data[i:i + CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)]

#             # Send chunks back to client
#             for seq_num, chunk in enumerate(chunks):
#                 client_socket.send(f"{client_id}|{seq_num}|{len(chunk)}".encode())
#                 client_socket.send(chunk)

#             # Send checksum
#             client_socket.send(checksum.encode())

#             print(f"Client {client_id}: File transfer complete. Checksum: {checksum}")

#         except Exception as e:
#             print(f"Client {client_id}: Error - {e}")
#         finally:
#             client_socket.close()

#     def corrupt_data(self, data):
#         # Randomly corrupt a byte in the data
#         if data:
#             index = random.randint(0, len(data) - 1)
#             data = data[:index] + bytes([data[index] ^ 0xFF]) + data[index + 1:]
#         return data

#     def start(self):
#         server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         server_socket.bind((SERVER_HOST, SERVER_PORT))
#         server_socket.listen(5)
#         print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

#         client_id = 0
#         while True:
#             client_socket, addr = server_socket.accept()
#             print(f"Accepted connection from {addr}")
#             client_id += 1
#             threading.Thread(target=self.handle_client, args=(client_socket, client_id)).start()

# if __name__ == "__main__":
#     server = Server()
#     server.start()


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

            # Send ACK to client so it can begin sending file data
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

            # Compute checksum for the received file data
            checksum = hashlib.sha256(file_data).hexdigest()

            # Split file data into chunks for sending back
            chunks = [file_data[i:i+CHUNK_SIZE] for i in range(0, len(file_data), CHUNK_SIZE)]

            # Send each chunk back with a header (client_id, sequence number, chunk size)
            for seq_num, chunk in enumerate(chunks):
                header = f"{client_id}|{seq_num}|{len(chunk)}"
                client_socket.send(header.encode())
                client_socket.send(chunk)

            # Send the computed checksum to the client
            client_socket.send(checksum.encode())

            print(f"Client {client_id}: File transfer complete. Checksum: {checksum}")

        except Exception as e:
            print(f"Client {client_id}: Error - {e}")
        finally:
            client_socket.close()

    def corrupt_data(self, data):
        # Randomly corrupt a byte in the data
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
