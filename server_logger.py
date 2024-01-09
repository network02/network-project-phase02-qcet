import logging
import os

class Logger:
    def __init__(self, root_directory):
        self.log_filename = 'ftp_server_log.txt'
        self.root_directory = root_directory
        self.logger_report = None


    def setup_logging(self):
        # Create a logger
        self.logger = logging.getLogger('ftp_server')
        self.logger.setLevel(logging.INFO)
        # Create a file handler and set the formatter
        log_file_path = os.path.join(self.root_directory, self.log_filename)
        self.logger_report = log_file_path
        if not os.path.exists(log_file_path):
            # If it doesn't exist, create an empty log file
            with open(log_file_path, 'w'):
                pass
        file_handler = logging.FileHandler(log_file_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        # Add the file handler to the logger
        self.logger.addHandler(file_handler)

    def log_command(self, username, command):
        # Log the executed command
        self.logger.info(f'User {username}: {command}')
