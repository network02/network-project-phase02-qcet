import socket
import os


class UserCredentials:
    def __init__(self, user_database_file="user_credentials.txt"):
        self.user_database_file = user_database_file
        self.user_credentials = {}
        self.load_user_credentials()

    def load_user_credentials(self):

        if os.path.exists(self.user_database_file):
            with open(self.user_database_file, 'r') as file:
                for line in file:
                    username, password = line.strip().split(':')
                    self.user_credentials[username]= password
        else:
            with open(self.user_database_file, 'w'):
                pass
        return

    def save_user_credentials(self):
        with open(self.user_database_file, 'w') as file:
            for username, password in self.user_credentials.items():
                file.write(f"{username}:{password}\n")

        return

    def authenticate_user(self, username, password):
        return username in self.user_credentials and self.user_credentials[username] == password

    def user_registration(self, username, password):
        if username not in self.user_credentials:
            self.user_credentials[username] = password
            self.save_user_credentials()
            return True
        else:
            return False


