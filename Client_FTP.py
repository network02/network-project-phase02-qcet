import os
import socket
import time
from tqdm import tqdm
from Menu_Display import *


def handle_username(username):
    if len(username) == 0:
        return False
    return True


def handle_password(password):
    if len(password) == 0:
        return False
    return True


def create_data_socket():
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return data_socket


class FTPClient:
    def __init__(self, host_ip, control_port, data_port):
        self.host = host_ip
        self.control_port = control_port
        self.data_port = data_port
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.data_socket = None
        self.menu = None
        self.admin_mode = False

        self.root_directory = os.path.abspath('Client_FTP.py')
        self.project_location = os.path.dirname(os.path.abspath(__name__))
        self.drive, self.path = os.path.splitdrive(self.project_location)
        self.relative_root_directory = os.path.join(self.drive, '\client_local_file')
        self.client_local_file = self.relative_root_directory

    def connect(self):
        self.control_socket.connect((self.host, self.control_port))
        response = self.control_socket.recv(1024).decode("utf-8")
        print(response)

    def send_command(self, command):
        self.control_socket.send(command.encode("utf-8"))
        response = self.control_socket.recv(1024).decode("utf-8")
        print(response)
        return response

    def start_data_connection(self):
        self.data_socket = create_data_socket()
        self.data_socket.connect((self.host, self.data_port))

    def stop_data_connection(self):
        if self.data_socket:
            self.data_socket.close()
            self.data_socket = None

    def register_user(self):
        os.system("cls")
        username = input("Enter username: ")
        if handle_username(username):
            self.send_command(f"USER {username}")
            password = input("Enter password: ")
            if handle_password(password):
                self.send_command(f"REGISTER {password}")
                print("Redirecting to Home ...")
                time.sleep(3.0)
                os.system("cls")
            else:
                print("Password can't be empty! ...")
                print("Redirecting to Home ...")
                time.sleep(3.0)
                os.system("cls")
        else:
            print("Username can't be empty! ...")
            print("Redirecting to Home ...")
            time.sleep(3.0)
            os.system("cls")
        return

    def handle_data_transfer(self, flag=False, local_file_path=None):
        data = b""
        while True:
            chunk = self.data_socket.recv(4096)
            if not chunk:
                break
            data += chunk

        if flag:

            with open(local_file_path, 'wb') as local_file:
                local_file.write(data)
        else:
            print(data.decode("utf-8"))

    def list_files(self, command):
        os.system("cls")

        response = self.send_command(command)
        if response.startswith("#225"):
            self.start_data_connection()
            self.handle_data_transfer()
            response = self.control_socket.recv(1024).decode("utf-8")
        else:
            print("could not find specified directory")

        if response.startswith("#226"):
            print(response)

        self.stop_data_connection()
        input("Enter to continue ... ")

    def make_directory(self, command):
        os.system("cls")
        response = self.send_command(command)
        if response.startswith("#200"):
            print("Directory successfully created")
        else:
            print(f"Error creating directory: {response}")

        input("Enter to continue ... ")
        return

    def remove_directory(self, command):
        response = self.send_command(command)
        if response.startswith("#200"):
            print(f"Directory removed")
        else:
            print(f"Error removing directory: {response}")
        input("Enter to continue ... ")
        return

    def print_working_directory(self, command):
        response = self.send_command(command)
        if response.startswith("#250"):
            pass
        else:
            print(f"Error retrieving current directory: {response}")
        input("Enter to continue ... ")

    def change_working_directory(self, command):
        response = self.send_command(command)
        if response.startswith("#250"):
            pass
        else:
            print(f"Error changing current working directory: {response} ")

        input("Enter to continue ... ")

    def change_to_parent_directory(self, command):
        response = self.send_command(command)
        if response.startswith("#200") or response.startswith("#250"):
            pass
        else:
            print(f"Error changing to parent directory: {response} ")
        input("Enter to continue ... ")

    def retrieve_from_server(self, command):
        os.system("cls")
        response = self.send_command(command)
        if response.startswith("#225"):
            file_size_extractor = response.split(" ")
            file_size_extractor = file_size_extractor[10]
            self.start_data_connection()
            name = input("Enter the file name / folder name to save the downloaded file: ")
            name.replace('/', "\\")
            try:
                if os.path.isabs(name):
                    new_directory_path = name
                elif name.startswith('...'):
                    path_split = name.split("...")
                    name = path_split[1]
                    new_directory_path = self.client_local_file + name
                else:
                    new_directory_path = os.path.join(self.client_local_file, name)

                print(new_directory_path)

                data = b""
                with tqdm(total=int(file_size_extractor), unit='B', unit_scale=True, desc='Downloading') as progress_bar:
                    while True:
                        chunk = self.data_socket.recv(4096)
                        progress_bar.update(len(chunk))
                        time.sleep(0.01)
                        if not chunk:
                            break
                        data += chunk

                with open(new_directory_path, 'wb') as local_file:
                    local_file.write(data)
                #self.handle_data_transfer(True, new_directory_path)
                response = self.control_socket.recv(1024).decode("utf-8")
            except Exception as e:
                print(e)
        else:
            print("Could not get from server")

        if response.startswith("#226"):
            print("\n")
            print(response)

        self.stop_data_connection()
        input("Enter to continue ... ")

    def store_on_server(self, command):
        os.system("cls")
        opcode = command[0]
        client_path = command[1].replace('/', "\\")
        server_path = command[2]
        try:

            if os.path.isabs(client_path):
                directory_file = client_path

            elif client_path.startswith("..."):
                path_split = client_path.split("...")
                name = path_split[1]
                directory_file = self.client_local_file + name
            else:
                directory_file = os.path.join(self.client_local_file, client_path)

            print(directory_file)

            if os.path.isfile(directory_file):
                p = opcode + " " + server_path

                filesize = os.path.getsize(directory_file)

                response = self.send_command(p)
                if response.startswith("#225"):
                    self.start_data_connection()
                    #time.sleep(5.0)
                    #progress = tqdm.tqdm(range(filesize), f"Sending {directory_file}", unit="B", unit_scale=True, unit_divisor=1024)

                    with open(directory_file, 'rb') as file:
                        bytes_read = file.read(4096)
                        with tqdm(total=filesize, unit='B', unit_scale=True, desc='Uploading') as progress_bar:
                            while bytes_read :
                                self.data_socket.sendall(bytes_read)
                                progress_bar.update(len(bytes_read))
                                time.sleep(0.02)
                                bytes_read = file.read(4096)
                            self.data_socket.sendall(b"EOF")


                    #print("waiting")
                    response = self.control_socket.recv(1024).decode("utf-8")

                    if response.startswith("#226"):
                        print(response)
                    else:
                        print(f"The error is {response}")

                else:
                    print(f"The error is {response} ")

            else:
                raise ValueError(f"{directory_file} is not a file")

        except ValueError as error:
            print(error)
        except Exception as error:
            print(error)
        finally:
            self.stop_data_connection()

        input("Enter to continue ... ")

    def delete_on_server(self, command):
        os.system("cls")
        response = self.send_command(command)
        if response.startswith("#10"):
            reply = input()
            self.control_socket.send(reply.upper().encode("utf-8"))
            response =self.control_socket.recv(1024).decode("utf-8")
            print(response)
        else:
            pass

        input("Enter to continue ... ")


    # admin mode functions
    def list_of_users(self, command):
        os.system("cls")
        response = self.send_command(command)
        if response.startswith("#225"):
            self.start_data_connection()
            self.handle_data_transfer()
            response = self.control_socket.recv(1024).decode("utf-8")
        else:
            print("Could not get from server")

        if response.startswith("#226"):
            print("\n")
            print(response)

        self.stop_data_connection()
        input("Enter to continue ... ")

    def report_of_users_commands(self, command):
        os.system("cls")
        response = self.send_command(command)
        if response.startswith("#225"):
            self.start_data_connection()
            print("Server Log")
            self.handle_data_transfer()
            response = self.control_socket.recv(1024).decode("utf-8")
            if response.startswith("#226"):
                print(response)
        else:
            print("Could not get logs from server")

        self.stop_data_connection()
        input("Enter to continue ... ")


    ############################################################
    def command_redirector(self, command, command_opcode):
        try:
            if command_opcode == "LIST":
                self.list_files(command)
                return True
            elif command_opcode == "MKD":
                if len(command) > 3:
                    self.make_directory(command)
                    return True
                else:
                    raise ValueError("Directory name isn't specified")
            elif command_opcode == "RMD":
                if len(command) > 3:
                    self.remove_directory(command)
                    return True
                else:
                    raise ValueError("Directory name isn't specified")
            elif command_opcode == "PWD":
                if len(command) > 3:
                    raise ValueError("PWD doesn't need any specifications or white spaces")
                else:
                    self.print_working_directory(command)
                    return True
            elif command_opcode == "CWD":
                if len(command) > 3:
                    self.change_working_directory(command)
                    return True
                else:
                    raise ValueError("Directory name isn't specified")
            elif command_opcode == "CDUP":
                if len(command) == 4:
                    self.change_to_parent_directory(command)
                    return True
                else:
                    raise ValueError("Directory name doesn't need to be specified")

            elif command_opcode == "RETR":
                if len(command) > 4:
                    self.retrieve_from_server(command)
                    return True
                else:
                    raise ValueError("You need to specify the directory name")

            elif command_opcode == "STOR":
                splitted_command = command.split(" ")
                if len(splitted_command) < 3:
                    raise ValueError("The command must be like STOR /client_path /server_path")
                else:
                    self.store_on_server(splitted_command)
                    return True
            elif command_opcode == "DELE":
                if len(command) > 4:
                    self.delete_on_server(command)
                    return True
                else:
                    raise ValueError("The command must be like DELE /server_file_path")

            # for admin mode:
            elif command_opcode == "LU":
                if self.admin_mode:
                    if len(command) > 2:
                        raise ValueError("LU doesn't need any specifications or white spaces")
                    else:
                        self.list_of_users(command)
                        return True
                else:
                    raise ValueError("Your account does not support this command")

            elif command_opcode == "REPORT":
                if self.admin_mode:
                    if len(command) > 6 :
                        raise ValueError("REPORT doesn't need any specifications or white spaces")
                    else:
                        self.report_of_users_commands(command)
                        return True

            elif command_opcode == "QUIT":
                if len(command) == 4:
                    self.send_command(command)
                    print("Exiting Menu ...")
                    time.sleep(2.0)
                    return False
                else:
                    raise ValueError("QUIT doesn't need suffix")

            else:
                raise ValueError("Unknown command specified")

        except ValueError as error:
            print(f"The Error is {error}")
            time.sleep(2.0)
            return True

    def login_user(self):
        os.system("cls")
        username = input("Enter username:")
        if handle_username(username):
            self.send_command(f"USER {username}")
            password = input("Enter password:")
            if handle_password(password):
                result = self.send_command(f"PASS {password}")
                if "User" in result:
                    self.handling_user_admin_command("User")
                else:
                    print("Authentication Failed!! ...\n")
                    print("Redirecting to Home ...")
                    time.sleep(3.0)
                    os.system("cls")

            else:
                print("Password can't be empty! ...")
                print("Redirecting to Home ...")
                time.sleep(3.0)
                os.system("cls")

        else:
            print("Username can't be empty! ...")
            print("Redirecting to Home ...")
            time.sleep(3.0)
            os.system("cls")
        return

    def handling_user_admin_command(self, flag):
        Result = True
        while Result:
            print("Redirecting to menu ... ")
            time.sleep(2.0)
            os.system("cls")
            self.menu = MenuDisplay(flag)
            self.menu.show_menu()
            print("Please Write your command: ")
            command = input()
            command_seperated_parts = command.split(" ", 1)
            command_opcode = command_seperated_parts[0].upper()
            Result = self.command_redirector(command, command_opcode)

        print("Redirecting to Home")
        time.sleep(3.0)
        os.system("cls")

    def switch_to_admin_mode(self):
        os.system("cls")
        username = input("Enter admin username: ")
        if handle_username(username):
            self.send_command(f"USER {username}")
            password = input("Enter admin password: ")
            if handle_password(password):
                result = self.send_command(f"PASS {password}")
                if "User" in result:
                    self.admin_mode = True
                    self.handling_user_admin_command("Admin")

                else:
                    print("Authentication Failed!! ...\n")
                    print("Redirecting to Home ...")
                    time.sleep(3.0)
                    os.system("cls")
            else:
                print("Password can't be empty! ...")
                print("Redirecting to Home ...")
                time.sleep(3.0)
                os.system("cls")
        else:
            print("Username can't be empty! ...")
            print("Redirecting to Home ...")
            time.sleep(3.0)
            os.system("cls")

    def admin_command(self, command):
        self.send_command(command)

    def start(self):
        self.connect()

        if not os.path.exists(self.client_local_file):
            os.makedirs(self.client_local_file)

        while True:
            print("Welcome To FTP server")
            print("Enter appropriate number to proceed:")  # add exception handler
            print("1.Register")
            print("2.Login")
            print("3.Admin")
            print("4.Exit")
            try:
                choice = input()
                if choice == '1':
                    self.register_user()
                    # os.system("cls")
                elif choice == '2':
                    self.login_user()
                    # os.system("cls")
                elif choice == '3':
                    self.switch_to_admin_mode()
                    # os.system("cls")
                elif choice == '4':
                    print("Existing the program ...")
                    break

                else:
                    raise ValueError("Key wrong pressed")

            except ValueError as error:
                os.system("cls")
                print(f"The Error is {error}")
                print("please enter a valid choice!")



if __name__ == "__main__":
    client = FTPClient("127.0.0.1", 21, 20)
    client.start()
