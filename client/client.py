import socket
from protocol import protocol
import sys

class Client:
    def __init__(self):
        self.protocol = protocol.Protocol()

    def main(self):
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.connect(("127.0.0.1", self.protocol.PORT))
        user_input = input("Enter your name: ")
        message = self.protocol.create_msg(user_input)
        my_socket.send(message.encode("utf-8"))
        
        while True:
            user_input = input("Enter message: ")
            message = self.protocol.create_msg(user_input)
            my_socket.send(message.encode("utf-8"))
            if user_input == "EXIT":
                print("Client exit \n bye")
                my_socket.close()
                sys.exit()
            valid_msg, cmd = self.protocol.get_msg(my_socket)
            if valid_msg:
                print(f"Server response: {cmd}")
            else:
                print("Response not valid\n")
                
if __name__ == "__main__":
    Client().main()
                
                
        