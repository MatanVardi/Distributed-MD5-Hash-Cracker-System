
import socket
from protocol import protocol

class Server:
    def __init__(self):
        self.protocol = protocol.Protocol()
        self.clients = {}

    def create_server_rsp(self, cmd, client_socket):
        if cmd.startswith("NAME "):
            username = cmd[5:].strip()
            self.clients[client_socket] = username
            return f"Name saved: {username}"

        return "Server received message"

    def main(self):
        server_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        server_socket.bind((self.protocol.IP, self.protocol.PORT))
        server_socket.listen()

        print("Server is up and running")

        client_socket, client_address = server_socket.accept()
        print(f"Client connected: {client_address}")

        with client_socket:
            while True:
                valid_msg, message = self.protocol.get_msg(client_socket)

                if not valid_msg:
                    break

                print(f"Server got {message}")

                response = self.create_server_rsp(
                    message, client_socket
                )

                response_msg = self.protocol.create_msg(response)
                client_socket.sendall(response_msg.encode())


if __name__ == "__main__":
    Server().main()
