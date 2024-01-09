import socket
import os
from FTPresponse import *
from datetime import datetime
from time import strftime, localtime
import shutil
import tqdm
import logging


def format_file_info(file_path):
    file_stat = os.stat(file_path)
    file_size = file_stat.st_size
    access_time = datetime.fromtimestamp(file_stat.st_atime)

    # Determine the nesting level based on the number of separators in the file_path
    nesting_level = file_path.count(os.path.sep)

    # Indent the file/directory representation based on the nesting level
    indentation = " " * nesting_level
    access_time_minutes = access_time.strftime("%Y-%m-%d %H:%M")
    # Include the file/directory name in the formatted output
    file_info = f"{indentation}{os.path.basename(file_path)}\t{file_size} bytes\t{access_time_minutes}"
    return file_info

    ###########################
    # file_stat = os.stat(file_path)
    # file_size = file_stat.st_size
    # access_time = datetime.fromtimestamp(file_stat.st_atime)
    # # You can customize the information displayed based on your requirements
    # file_info = f"{os.path.basename(file_path)}\t{file_size} bytes\t{access_time}"
    # return file_info


def send_directory_listing(directory_path):
    file_list = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_list.append(format_file_info(file_path))
        for subdir in dirs:
            dir_path = os.path.join(root, subdir)
            file_list.append(format_file_info(dir_path))

    return file_list


class ClientHandler:
    def __init__(self, control_socket, client, data_port, authenticate_user, register_user, admin_username,
                 admin_password,
                 user_credentials, session_manager, root_directory, logger):
        self.client_address = client
        self.control_socket = control_socket
        self.data_port = data_port
        self.data_socket = None
        self.data_connection = None
        self.cwd = root_directory  # r'F:\Server_Cloud'
        self.root_directory = root_directory  # r'F:\Server_Cloud'
        self.ftp_response = FTPResponse(self.control_socket)
        self.authenticate_user = authenticate_user
        self.register_user = register_user
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.current_user = None
        self.admin_mode = False
        self.user_credentials = user_credentials
        self.session_manager = session_manager
        self.logger = logger

    def USER(self, username):
        self.current_user = username
        if self.current_user == self.admin_username:
            self.admin_mode = True
        self.ftp_response.send_331(f"User {username} is received. Password required")
        return

    def PASS(self, password):
        result, explanation = self.authenticate_user(self.current_user, password)
        if result:
            if self.current_user == self.admin_username and self.admin_password == password:
                self.admin_mode = True
            self.ftp_response.send_230("User Logged in")

        else:
            if explanation.startswith("Session"):
                self.ftp_response.send_530("This account has another active session")
            else:
                self.ftp_response.send_530("Logging Failed")

        return

    def REGISTER(self, password):
        Result = self.register_user(self.current_user, password)
        if Result:
            self.ftp_response.send_230("User registered ")

        else:
            self.ftp_response.send_100("Username already exists")

        return

    def handle_admin_command(self, command):
        if not self.admin_mode:
            self.ftp_response.send_120("Not Logged in as admin")

        # Add Admin-specific commands like REPORT
        if command.upper() == "LU":
            user_list = "\n".join(self.user_credentials.user_credentials.keys())
            self.ftp_response.send_10(f"User list :\n{user_list}")
        else:
            self.ftp_response.send_500("Command not found")

        return

    @property
    def open_data_socket(self):
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.bind(('127.0.0.1', self.data_port))
        return data_socket

    def start_data_connection(self):
        self.data_socket = self.open_data_socket
        # self.ftp_response.send_225("Data connection established")

    def start_data_listener(self):
        self.data_socket.listen(25)
        self.data_connection, client_address = self.data_socket.accept()
        print(f"Data connection established with {client_address}")

    def stop_data_listener(self):
        if self.data_socket:
            self.data_socket.close()
            self.data_connection.close()
            self.data_connection = None
            self.data_socket = None
            print("Data connection closed")

    def close_data_connection(self):
        if self.data_socket:
            self.data_socket.close()
            self.data_socket = None
            if self.data_connection:
                self.data_connection.close()
                self.data_connection = None

    def LIST(self, path=""):

        try:
            if self.data_socket:
                self.close_data_connection()
            if not path:
                directory_path = self.cwd
            elif os.path.isabs(path):
                directory_path = path
            else:
                if path.startswith('...'):
                    path_split = path.split("...")
                    path = path_split[1]
                else:
                    pass
                directory_path = self.cwd + path
                # if path.startswith('...'):
                #     path = os.path.basename(os.path.normpath(path))
                # else:
                #     pass
                # directory_path = os.path.join(self.cwd, path)
                # # print("yes")

            check_path = self.path_modfication(directory_path)
            if os.path.commonpath([self.root_directory, check_path]) != self.root_directory:
                self.ftp_response.send_500("Cannot change to directory beyond the root directory")
                return

            # print(directory_path)
            if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
                self.ftp_response.send_500(f"Directory not found: {directory_path}")
                return

            # file_list = send_directory_listing(directory_path)

            # file_list = os.listdir(directory_path)
            # file_info_list = [self.format_file_info(os.path.join(directory_path, file)) for file in file_list]

            self.start_data_connection()
            self.ftp_response.send_225("Data connection Created")
            self.start_data_listener()
            for dirpath, dirnames, filenames in os.walk(directory_path):

                for name in dirnames + filenames:
                    entry_path = os.path.join(dirpath, name)
                    entry_stat = os.stat(entry_path)
                    entry_time = strftime('%Y-%m-%d %H:%M', localtime(entry_stat.st_mtime))

                    # Check if the entry is a file to get its size
                    flag = False
                    if os.path.isfile(entry_path):
                        entry_size = entry_stat.st_size
                    else:
                        entry_size = 0
                        flag = True
                    en = ""
                    entry_path = os.path.join(dirpath, name)
                    formatted_path = entry_path.ljust(50)
                    formatted_size = f"{entry_size} bytes".ljust(15)
                    formatted_time = entry_time.ljust(25)
                    if flag:
                        en = f"{formatted_path}  {formatted_size}   {formatted_time}"
                    else:
                        en = f"{formatted_path}  {formatted_size}   {formatted_time}"
                    self.data_connection.send(en.encode("utf-8") + b'\n')

            self.ftp_response.send_226("Transfer completed")

        except Exception as error:
            print(f"Error handling LIST command: {error}")
            self.ftp_response.send_500(f"Error handling LIST command: {error}")
        finally:
            self.stop_data_listener()

    def MKD(self, path):
        if os.path.isabs(path):
            # Absolute path
            new_directory_path = path
        else:
            # Relative path
            # if path.startswith('...'):
            #     path = os.path.basename(os.path.normpath(path))
            # else:
            #     pass
            # new_directory_path = os.path.join(self.cwd, path)
            if path.startswith('...'):
                path_split = path.split("...")
                path = path_split[1]
            else:
                pass
            new_directory_path = self.cwd + path
        try:
            check_path = self.path_modfication(new_directory_path)
            if os.path.commonpath([self.root_directory, check_path]) != self.root_directory:
                self.ftp_response.send_500("Cannot make change to directory beyond the root directory")
                return
            os.makedirs(new_directory_path)
            self.ftp_response.send_200(f"Directory created: {new_directory_path}")
        except FileExistsError:
            self.ftp_response.send_500(f"Directory already exists: {new_directory_path}")
        except Exception as error:
            print(f"Error creating directory: {error}")
            self.ftp_response.send_500(f"Error creating directory: {error}")

    def RMD(self, path):

        if os.path.isabs(path):
            directory_to_remove = path
        else:
            # if path.startswith('...'):
            #     path = os.path.basename(os.path.normpath(path))
            # else:
            #     pass
            # directory_to_remove = os.path.join(self.cwd, path)
            if path.startswith('...'):
                path_split = path.split("...")
                path = path_split[1]
            else:
                pass

            directory_to_remove = self.cwd + path

        try:
            check_path = self.path_modfication(directory_to_remove)
            if os.path.commonpath([self.root_directory, check_path]) != self.root_directory:
                self.ftp_response.send_500("Cannot remove directory beyond the root directory")
                return
            # Only admin can remove none empty directories
            if self.admin_mode:
                shutil.rmtree(directory_to_remove)
            else:
                os.rmdir(directory_to_remove)

            self.ftp_response.send_200(f"Directory removed: {directory_to_remove}")
        except FileNotFoundError:
            self.ftp_response.send_500(f"Directory not found: {directory_to_remove}")
        except OSError as error:
            if error.errno == 145:
                print(f"Error removing directory: {error} for {self.client_address}")
                self.ftp_response.send_500(f"Error removing directory: {error}.Contact Admin to remove")
            else:
                print(f"Error removing directory: {error} for {self.client_address}")
                self.ftp_response.send_500(f"Error removing directory: {error}")

    def current_path(self):
        current_directory = os.path.relpath(self.cwd, start=self.root_directory)
        formatted_path = os.path.join(self.root_directory, current_directory)
        formatted_path = os.path.normpath(formatted_path)
        return formatted_path

    def path_modfication(self, path):
        current_directory = os.path.relpath(path, start=self.root_directory)
        formatted_path = os.path.join(self.root_directory, current_directory)
        formatted_path = os.path.normpath(formatted_path)
        return formatted_path

    def PWD(self, path):
        try:
            # current_directory = os.path.relpath(self.cwd, start=self.root_directory)
            # print (f"the current pwd is {current_directory}")
            # formatted_path = os.path.join(self.root_directory, current_directory)
            # formatted_path = os.path.normpath(formatted_path)
            self.ftp_response.send_250(f"{self.cwd} is the current directory")

        except Exception as error:
            print(f"Error handling PWD command: {error}")
            self.ftp_response.send_500(f"Error handling PWD command: {error}")

    def CWD(self, path):
        try:

            if os.path.isabs(path):
                new_directory_path = path
            else:
                if path.startswith('...'):
                    # path = os.path.basename(os.path.normpath(path))
                    path_split = path.split("...")
                    path = path_split[1]
                else:
                    pass

                # new_directory_path = os.path.join(self.cwd, path)
                new_directory_path = self.cwd + path

            if os.path.exists(new_directory_path) and os.path.isdir(new_directory_path):
                check_path = self.path_modfication(new_directory_path)
                if os.path.commonpath([self.root_directory, check_path]) != self.root_directory:
                    self.ftp_response.send_500("Cannot change to directory beyond the root directory")
                    return
                self.cwd = new_directory_path
                self.cwd = self.current_path()
                self.ftp_response.send_250(f"Directory changed to {self.cwd}")
            else:
                self.ftp_response.send_500(f"Directory not found: {new_directory_path}")
        except OSError as error:
            print(f"Error changing working directory: {error} for {self.client_address}")
            self.ftp_response.send_500(f"Error changing working directory: {error}")

    def QUIT(self, path):
        if self.current_user in self.session_manager:
            self.session_manager[self.current_user] = False
            self.ftp_response.send_530("Logging off")

    def CDUP(self, path):
        try:
            print(f"root is {self.root_directory}")
            if self.cwd == self.root_directory:
                self.ftp_response.send_250(f"Current directory is already the root directory: {self.cwd}")
                return
            # Use os.path.dirname to get the parent directory of the current working directory
            # drive, path = os.path.splitdrive(self.cwd)
            # print(f"the path and driver is {path} and {drive}")
            parent_directory = os.path.dirname(self.cwd)
            # print(f"parent directory {parent_directory}")
            # # Normalize paths to use backslashes and check if the drive letters are the same
            # current_path = os.path.normpath(self.cwd)
            # print(current_path)
            # parent_path = os.path.normpath(parent_directory)
            # print(parent_path)

            # Check if the new directory is within the root directory
            if os.path.commonpath([self.root_directory, parent_directory]) == self.root_directory:
                self.cwd = parent_directory
                self.ftp_response.send_200(f"Directory changed to its parent : {parent_directory} ")
            else:
                self.ftp_response.send_500(f"Invalid parent directory: {parent_directory}")

        except Exception as error:
            print(f"Error handling CDUP command: {error}")
            self.ftp_response.send_500(f"Error handling CDUP command: {error}")

    def RETR(self, path):

        try:
            if self.data_socket:
                self.close_data_connection()

            if os.path.isabs(path):
                # if "home" in path:
                new_directory_path = path
            else:
                if path.startswith('...'):
                    path_split = path.split("...")
                    path = path_split[1]
                else:
                    pass

                new_directory_path = self.cwd + path

            check_path = self.path_modfication(new_directory_path)
            if os.path.commonpath([self.root_directory, check_path]) != self.root_directory:
                self.ftp_response.send_500("Cannot address to directory beyond the root directory")
                return

            if 'ftp_server_log.txt' in new_directory_path:
                if not self.admin_mode:
                    self.ftp_response.send_500("Permission denied. You can't manipulate this file.")
                    return
            try:
                print(new_directory_path)
                if os.path.isfile(new_directory_path):
                    try:

                        with open(new_directory_path, 'rb') as file:
                            file_size = os.path.getsize(new_directory_path)
                            self.start_data_connection()
                            self.ftp_response.send_225(
                                f"Opening data connection for RETR. The file size is {file_size} byte")
                            self.start_data_listener()
                            # Send the file contents through the data connection
                            data = file.read()
                            self.data_connection.sendall(data)
                            self.ftp_response.send_226("Transfer completed")

                    except Exception as error:
                        print(f"Download failed due to {error}")
                        self.ftp_response.send_500(f"Error : {error}")
                else:
                    raise ValueError(f"{new_directory_path} is not file")

            except ValueError as error:
                print(f"Error : {error}")
                self.ftp_response.send_500(f"Error : {error}")

        except Exception as error:
            print(f"Error retrieve command: {error}")
            self.ftp_response.send_500(f"Error retrieve command: {error}")
        finally:
            self.stop_data_listener()

        return

    def STOR(self, path):
        print(path)
        path, file = os.path.split(path)
        try:
            if self.data_socket:
                self.close_data_connection()

            if os.path.isabs(path):
                file_directory = path
            else:
                if path.startswith("..."):
                    path_split = path.split("...")
                    path = path_split[1]
                else:
                    pass
                file_directory = self.cwd + path

            if os.path.exists(file_directory) and os.path.isdir(file_directory):
                check_path = self.path_modfication(file_directory)
                if os.path.commonpath([self.root_directory, check_path]) != self.root_directory:
                    self.ftp_response.send_500("Cannot address to directory beyond the root directory")
                    return

                local_file_path = os.path.join(file_directory, file)
                if 'ftp_server_log.txt' in local_file_path:
                    if not self.admin_mode:
                        self.ftp_response.send_500("Permission denied. You can't manipulate this file.")
                        return

                with open(local_file_path, 'wb') as file:
                    self.start_data_connection()
                    self.ftp_response.send_225("Data connection established")
                    self.start_data_listener()
                    # progress = tqdm.tqdm(range(filesize), f"Receiving {local_file_path}", unit="B", unit_scale=True,unit_divisor=1024)
                    # data = self.data_connection.recv(4096)
                    # data = b""
                    # chunk = self.data_connection.recv(4096)
                    # data = self.data_connection.recv(4096)

                    while True:
                        data = self.data_connection.recv(4096)
                        if not data or data == b"EOF":
                            break
                        file.write(data)
                        # progress.update(len(data))
                        # if not data:
                        #     break not data or
                        # print("1") not data or

                    # while True:
                    #     print("1")
                    #     chunk = self.data_connection.recv(4096)
                    #     if not chunk:
                    #         print("2")
                    #         break
                    #     data += chunk
                    #
                    # print(f"The data is {data}")
                    # file.write(data)
                    self.ftp_response.send_226("File uploaded successfully ")
            else:
                self.ftp_response.send_500(f"Directory not found to upload : {file_directory}")

        except Exception as error:
            print(error)
            self.ftp_response.send_500(f" Error store command: {error} ")
        finally:
            self.stop_data_listener()

    def DELE(self, path):

        print(path)
        path, file = os.path.split(path)
        try:

            if os.path.isabs(path):
                file_directory = path
            else:
                if path.startswith("..."):
                    path_split = path.split("...")
                    path = path_split[1]
                else:
                    pass
                file_directory = self.cwd + path

            if os.path.exists(file_directory) and os.path.isdir(file_directory):
                check_path = self.path_modfication(file_directory)
                if os.path.commonpath([self.root_directory, check_path]) != self.root_directory:
                    self.ftp_response.send_500("Cannot address to directory beyond the root directory")
                    return
                local_file_path = os.path.join(file_directory, file)
                if 'ftp_server_log.txt' in local_file_path:
                    if not self.admin_mode:
                        self.ftp_response.send_500("Permission denied. You can't manipulate this file.")
                        return
                print(local_file_path)
                confirm_message = "Do you really wish to delete? Y/N"
                self.ftp_response.send_10(confirm_message)

                answer = self.control_socket.recv(1024).decode("utf-8")
                if answer == 'Y' or 'y':
                    os.remove(local_file_path)
                    response = "The file deleted successfully."
                    self.ftp_response.send_226(response)

                else:
                    response = "File deleting Canceled"
                    self.ftp_response.send_226(response)
            else:
                self.ftp_response.send_500(f"Directory file not found to delete : {file_directory}")
        except Exception as error:
            print(error)
            self.ftp_response.send_500(f" Error store command: {error} ")
        finally:
            self.stop_data_listener()

    # admin premium commands
    def LU(self, path):

        try:
            if self.data_socket:
                self.close_data_connection()
            else:

                self.start_data_connection()
                self.ftp_response.send_225("Data connection Created")
                self.start_data_listener()
                max_username_length = max(len(username) for username in self.user_credentials.user_credentials.keys())
                user_list = list(
                    self.user_credentials.user_credentials.items())  # "\n".join(self.user_credentials.user_credentials.items())
                user_list_str = "\n".join(
                    [f"Username: {username.ljust(max_username_length)}    ,   Password: {password}" for
                     username, password in
                     user_list])  # "\n".join([f"Username: {user[0]}   Password: {user[1]}" for user in user_list])
                self.data_connection.send(user_list_str.encode("utf-8"))
                self.ftp_response.send_226("Transfer completed")
        except Exception as e:
            print(f"Error handling LU command: {e}")
            self.ftp_response.send_500(f"Error handling LU command: {e}")
        finally:
            self.stop_data_listener()

    def REPORT(self, path):
        try:
            if self.data_socket:
                self.close_data_connection()

            # Read the log file and send it to the client
            with open(self.logger.logger_report, 'rb') as log_file:
                log_contents = log_file.read()
                self.start_data_connection()
                self.ftp_response.send_225("Data connection established for logger")
                self.start_data_listener()
                self.data_connection.send(log_contents)
                self.ftp_response.send_226("Loggerr sent successfully")

        except FileNotFoundError:
            # Log file not found, send an appropriate response
            self.ftp_response.send_500('Log file not found')

        finally:
            self.stop_data_listener()

    def start(self):
        self.ftp_response.send_220("Connected To FTP Server")
        while True:

            command_coming_from_client = self.control_socket.recv(1024).decode(
                "utf-8").strip()  # Returns a new string with leading and trailing whitespaces removed.

            if not command_coming_from_client:
                self.ftp_response.send_500("Bad request")
                break
            else:
                command_separated_parts = command_coming_from_client.split(" ", 1)
                command_opcode = command_separated_parts[0].upper()

                arguments = ""
                if command_opcode == "USER" or command_opcode == "PASS" or command_opcode == "MKD" or command_opcode == "RMD" or \
                        command_opcode == "CWD" or command_opcode == "RETR" or command_opcode == "STOR" or command_opcode == "DELE":
                    arguments = command_separated_parts[1]
                    arguments = arguments.replace('/', "\\")
                elif command_opcode == "LIST" and 4 < len(command_coming_from_client):
                    arguments = command_separated_parts[1]
                else:
                    # if self.admin_mode:
                    #  self.handle_admin_command(command_opcode)
                    pass
                # if self.admin_mode:
                #     self.handle_admin_command(command_opcode)
                # else:

                if hasattr(self, f"{command_opcode}"):
                    self.logger.log_command(self.current_user, command_coming_from_client)
                    getattr(self, f"{command_opcode}")(arguments)
                else:
                    self.ftp_response.send_500("Command not Found")

        self.control_socket.close()
        print(f"control socket closed for {self.client_address}")
