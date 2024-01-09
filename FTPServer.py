import socket
import os
import threading
from client_handler import *
from user_cridentials import *
from server_logger import *

class FTPServer:
    def __init__(self, host, control_port, data_port):
        self.host = host
        self.control_port = control_port
        self.data_port = data_port
        self.session_manager = {}
        self.total_clients = 1000
        self.client_counter = 0
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.control_port))
        self.server_socket.listen()
        print(f"Server is listening on {host} : port number is : {control_port}")
        # self.server_socket_data = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.server_socket_data.bind((self.host, self.data_port))
        # self.server_socket_data.listen()
        # User Authentication
        self.user_credentials = UserCredentials()
        # Admin username and password
        self.admin_username = "admin"
        self.admin_password = "admin1234"

        # Set the initial root directory
        self.root_directory = os.path.abspath('FTPServer.py')
        self.project_location = os.path.dirname(os.path.abspath(__name__))
        self.drive, self.path = os.path.splitdrive(self.project_location)
        # print(self.drive)
        self.relative_root_directory = os.path.join(self.drive, '\home')
        self.root_directory = self.relative_root_directory
        self.logger = Logger(self.root_directory)
        self.logger.setup_logging()

    def authenticate_user(self, username, password):
        if username in self.session_manager and self.session_manager[username]:
            return False, "Session Failing"
        else:
            if self.user_credentials.authenticate_user(username, password):
                self.session_manager[username] = True
                return True, "Ok"
            elif username == self.admin_username and password == self.admin_password:
                self.session_manager[username] = True
                return True, "Ok"
            else:
                return False, "OOPS"

    def register_user(self, username, password):
        return self.user_credentials.user_registration(username, password)

    def start_client_handler(self, control_socket, client):
        Client_Handler = ClientHandler(control_socket, client, self.data_port,
                                       self.authenticate_user, self.register_user,
                                       self.admin_username, self.admin_password, self.user_credentials,
                                       self.session_manager, self.root_directory, self.logger)
        Client_Handler.start()

    def start_server(self):
        # Check if the root directory exists
        # print(self.relative_root_directory)
        if not os.path.exists(self.relative_root_directory):
            # print("yes")
            os.makedirs(self.relative_root_directory)
        else:
            pass
        while True:
            self.client_counter += 1
            authorization_socket, client_address_ip = self.server_socket.accept()
            # data_transferring_socket , addre_c = self.server_socket_data.accept()
            # print(f"DATA Connection Accepted from {addre_c} # client number is {self.client_counter}")
            print(f"Connection Accepted from {client_address_ip} # client number is {self.client_counter}")
            client_threat = threading.Thread(target=self.start_client_handler,
                                             args=(authorization_socket, client_address_ip))

            client_threat.start()

            if self.client_counter > 1000:
                break


if __name__ == "__main__":
    server = FTPServer("127.0.0.1", 21, 20)
    server.start_server()
# python FTPServer.py
