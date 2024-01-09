class MenuDisplay:
    def __init__(self, mode):
        self.flag_title = mode
        self.title = "\nMenu:"

    def show_menu(self):

        if self.flag_title == "User":
            print ("User Dashboard")
        else:
            print ("Admin Dashboard")

        print(self.title)
        print("1. LIST - List of files and directories")
        print("2. RETR - Retrieve a file from the server")
        print("3. STOR - Store a file on the server")
        print("4. DELE - Delete at the server site")
        print("5. MKD  - Make a directory")
        print("6. RMD  - Remove a directory")
        print("7. PWD  - Print working directory")
        print("8. CWD  - Change working directory")
        print("9. CDUP - Change to parent directory")

        if self.flag_title == 'Admin':
            print("10.LU   - List of users")
            print("11.REPORT            ")

        print("q. QUIT - Disconnect from the server")









