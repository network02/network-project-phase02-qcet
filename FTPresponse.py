import socket
import os


class FTPResponse:
    def __init__(self, control_socket):
        self.control_socket = control_socket

    def public_send(self, code, message):
        response = f"{code} {message}\r\n"
        self.control_socket.send(response.encode("utf-8"))
        return

    def send_220(self, message):  # service ready for new user.
        self.public_send("#220.", message)
        return

    def send_221(self, message):  # Service closing control connection.
        self.public_send("#221.", message)
        return

    def send_421(self, message):  # Service not available, closing control connection.
        self.public_send("#421.", message)  # This may be a reply to any command if the service knows it  must shut down.
        return

    def send_125(self, message):  # Data connection already open; transfer starting.
        self.public_send("#125.", message)
        return

    def send_225(self, message):  # Data connection open; no transfer in progress.
        self.public_send("#225.", message)
        return

    def send_425(self, message):  # Can't open data connection.
        self.public_send("#425", message)
        return

    def send_226(self, message):  # Closing data connection Requested file action successful (for example, file transfer or file abort).
        self.public_send("#226.", message)
        return

    def send_230(self, message):  # User logged in, proceed.
        self.public_send("#230.", message)
        return

    def send_530(self, message):  # Not logged in.
        self.public_send('#530.', message)
        return

    def send_331(self, message):  # Username okay, need password.
        self.public_send('#331.', message)
        return

    def send_332(self, message):  # Need account for login.
        self.public_send('#332.', message)
        return

    def send_532(self, message):  # Need account for storing files.
        self.public_send('#532.', message)
        return

    def send_100(self, message): # user already exists for  registeration
        self.public_send('#100.', message)
        return

    def send_120(self, message): # Not Logged in as admin
        self.public_send('#120.', message)
        return

    def send_10(self, message): # control message for deleting
        self.public_send('#10.',message)
        return

    def send_500(self, message):
        self.public_send('#500.',message) #bad request
        return
    def send_200(self, message):
        self.public_send('#200', message) #Directory Created

    def send_250(self, message):
        self.public_send('#250', message) # the current directory