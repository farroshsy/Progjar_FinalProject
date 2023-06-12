import socket
import os
import json
import base64
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Server'))

# from chat import Chat

TARGET_IP = "localhost"
TARGET_PORT = 9999


class ChatClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (TARGET_IP, TARGET_PORT)
        self.sock.connect(self.server_address)
        self.tokenid = ""

    def proses(self, cmdline):
        j = cmdline.split(" ")
        try:
            command = j[0].strip()
            if command == 'register':
                username = j[1].strip()
                password = j[2].strip()
                name = j[3].strip()
                country = j[4].strip()
                return self.register_user(username, password, name, country)
            
            elif (command == 'auth'):
                username = j[1].strip()
                password = j[2].strip()
                return self.login(username, password)
            
            elif (command == 'send'):
                usernameto = j[1].strip()
                message = ""
                for w in j[2:]:
                    message = "{} {}" . format(message, w)
                return self.sendmessage(usernameto, message)
            
            elif (command == 'sendfile'):
                usernameto = j[1].strip()
                filepath = j[2].strip()
                return self.send_file(usernameto, filepath)
            
            elif (command == 'getfile'):
                return self.get_file()
            
            elif command == 'creategroup':
                group_name = j[1].strip()
                return self.create_group(group_name)
            
            elif command == 'getgroup':
                return self.get_group()

            elif command == 'joingroup':
                group_name = j[1].strip()
                return self.join_group(group_name)

            elif command == 'exitgroup':
                group_name = j[1].strip()
                return self.exit_group(group_name)

            elif command == 'invitegroup':
                group_name = j[1].strip()
                username = j[2].strip()
                return self.invite_group(group_name, username)

            elif (command == 'sendgroup'):
                usernamesto = j[1].strip()
                message = ""
                for w in j[2:]:
                    message = "{} {}" . format(message, w)
                return self.send_group_message(usernamesto, message)
           
            elif (command == 'sendgroupfile'):
                usernamesto = j[1].strip()
                filepath = j[2].strip()
                return self.send_group_file(usernamesto, filepath)
            
            elif command == 'getpresence':
                username = j[1].strip()
                return self.get_presence(username)
            
            elif command == 'deletelastmessage':
                username = j[1].strip()

            elif command == 'forwardmessage':
                source_username = j[1].strip()
                destination_username = j[2].strip()
                result = self.forward_message(
                    source_username, destination_username)
                return result
            
            elif command == 'replymessage':
                username = j[1].strip()
                message = ' '.join(j[2:]).strip()
                result = self.reply_message(username, message)
                return result
            
            elif (command == 'addrealm'):
                realmid = j[1].strip()
                realm_address = j[2].strip()
                realm_port = j[3].strip()
                return self.add_realm(realmid, realm_address, realm_port)
            
            elif (command == 'sendprivaterealm'):
                realm_name = j[1].strip()
                username_dest = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}".format(message, w)
                return self.send_private_realm_message(realm_name, username_dest, message)
            
            elif (command == 'sendfilerealm'):
                realm_name = j[1].strip()
                username_dest = j[2].strip()
                file_path = j[3].strip()
                return self.send_file_to_realm(realm_name, username_dest, file_path)
            
            elif (command == 'sendgrouprealm'):
                realm_name = j[1].strip()
                usernames_to = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}".format(message, w)
                return self.send_group_realm_message(realm_name, usernames_to, message)
            
            elif (command == 'sendgroupfilerealm'):
                realm_name = j[1].strip()
                usernames_to = j[2].strip()
                file_path = j[3].strip()
                return self.send_group_file_to_realm(realm_name, usernames_to, file_path)
            
            elif (command == 'inbox'):
                return self.inbox()
            
            elif (command == 'getrealminbox'):
                realm_name = j[1].strip()
                return self.get_realm_inbox(realm_name)
            
            elif command == 'getnotifications':
                return self.get_notifications()
            
            else:
                return "*Maaf, command tidak benar"
        except IndexError:
            return "-Maaf, command tidak benar"

    def sendstring(self, string):
        try:
            self.sock.sendall(string.encode())
            receivemsg = ""
            while True:
                data = self.sock.recv(64)
                print("diterima dari server", data)
                if (data):
                    # data harus didecode agar dapat di operasikan dalam bentuk string
                    receivemsg = "{}{}" . format(receivemsg, data.decode())
                    if receivemsg[-4:] == '\r\n\r\n':
                        print("end of string")
                        return json.loads(receivemsg)
        except:
            self.sock.close()
            return {'status': 'ERROR', 'message': 'Gagal'}
        
    def register_user(self, username, password, name, country):
        if self.tokenid != "":
            return "Error, already logged in"
        
        string = "register {} {} {} {} \r\n".format(username, password, name, country)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "User registered successfully"
        else:
            return "Error, {}".format(result['message'])

    def login(self, username, password):
        string = "auth {} {} \r\n" . format(username, password)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            self.tokenid = result['tokenid']
            return "username {} logged in, token {} " .format(username, self.tokenid)
        else:
            return "Error, {}" . format(result['message'])

    def send_file(self, usernameto="xxx", filepath="xxx"):
        if (self.tokenid == ""):
            return "Error, not authorized"

        if not os.path.exists(filepath):
            return {'status': 'ERROR', 'message': 'File not found'}

        with open(filepath, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)
        string = "sendfile {} {} {} {}\r\n" . format(
            self.tokenid, usernameto, filepath, encoded_content)

        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "file sent to {}" . format(usernameto)
        else:
            return "Error, {}" . format(result['message'])
        
    def get_file(self):
        if (self.tokenid == ""):
            return "Error, not authorized"
        string = "getfile {} \r\n" . format(self.tokenid)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            msg = result['messages']
            user_from = next(iter(msg))
            file_name = msg[user_from][0]
            encoded_file = msg[user_from][1]

            if 'b' in encoded_file[0]:
                with open(file_name, "wb") as fh:
                    fh.write(base64.b64decode(encoded_file[2:-1]))
            else:     
                tail = encoded_file.split()
            return "{}" . format(json.dumps(msg))
        else:
            return "Error, {}" . format(result['message'])
        
    def sendmessage(self, usernameto="xxx", message="xxx"):
        if self.tokenid == "":
            return "Error, not authorized"
        
        # Replacing emoticons
        emoticon_mapping = {
            ":)": "🙂",
            ":(": "☹️",
            ":D": "😁",
            "T_T": "😭",
        }
        for emoticon, replacement in emoticon_mapping.items():
            if emoticon in message:
                message = message.replace(emoticon, replacement)

        string = "send {} {} {} \r\n".format(self.tokenid, usernameto, message)
        result = self.sendstring(string)
        
        if result["status"] == "OK":
            return "Message sent to {}".format(usernameto)
        else:
            return "Error: {}".format(result["message"])

    def send_private_realm_message(self, realm_name, username_dest, message):
        if self.token_id == "":
            return "Error, not authorized"
        string = "send_private_realm {} {} {} {}\r\n".format(self.token_id, realm_name, username_dest, message)
        result = self.send_string(string)
        if result['status'] == 'OK':
            return "Message sent to realm {}".format(realm_name)
        else:
            return "Error: {}".format(result['message'])

    def send_file_to_realm(self, realm_name, username_dest, file_path):
        if self.token_id == "":
            return "Error, not authorized"

        if not os.path.exists(file_path):
            return {'status': 'ERROR', 'message': 'File not found'}

        with open(file_path, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content).decode('utf-8')
        string = "send_file_realm {} {} {} {} {}\r\n".format(
            self.token_id, realm_name, username_dest, file_path, encoded_content)
        result = self.send_string(string)
        if result['status'] == 'OK':
            return "File sent to realm {}".format(realm_name)
        else:
            return "Error: {}".format(result['message'])

    def create_group(self, group_name):
        if self.tokenid == "":
            return "Error, not authorized"

        string = f"creategroup {self.tokenid} {group_name}\r\n"
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return f"Group '{group_name}' created successfully"
        else:
            return f"Error, {result['message']}"


    def get_group(self):
        if self.tokenid == "":
            return "Error, not authorized"

        string = f"getgroup {self.tokenid}\r\n"
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return f"Groups: {', '.join(result['groups'])}"
        else:
            return f"Error, {result['message']}"


    def join_group(self, group_name):
        if self.tokenid == "":
            return "Error, not authorized"

        string = f"joingroup {self.tokenid} {group_name}\r\n"
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return f"Joined group '{group_name}' successfully"
        else:
            return f"Error, {result['message']}"


    def exit_group(self, group_name):
        if self.tokenid == "":
            return "Error, not authorized"

        string = f"exitgroup {self.tokenid} {group_name}\r\n"
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return f"Exited group '{group_name}' successfully"
        else:
            return f"Error, {result['message']}"


    def invite_group(self, group_name, username):
        if self.tokenid == "":
            return "Error, not authorized"

        string = f"invitegroup {self.tokenid} {group_name} {username}\r\n"
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return f"Invited user '{username}' to group '{group_name}' successfully"
        else:
            return f"Error, {result['message']}"


    def get_notifications(self):
        if self.tokenid == "":
            return "Error, not authorized"

        string = f"getnotifications {self.tokenid}\r\n"
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return f"Unopened message notifications: {result['notifications']}"
        else:
            return f"Error, {result['message']}"

    def send_group_message(self, usernames_to="xxx", message="xxx"):
        if (self.tokenid == ""):
            return "Error, not authorized"
        string = "sendgroup {} {} {} \r\n" . format(
            self.tokenid, usernames_to, message)
        print(string)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "message sent to {}" . format(usernames_to)
        else:
            return "Error, {}" . format(result['message'])

    def send_group_file(self, usernames_to="xxx", filepath="xxx"):
        if (self.tokenid == ""):
            return "Error, not authorized"

        if not os.path.exists(filepath):
            return {'status': 'ERROR', 'message': 'File not found'}

        with open(filepath, 'rb') as file:
            file_content = file.read()
            # Decode byte-string to UTF-8 string
            encoded_content = base64.b64encode(file_content)

        string = "sendgroupfile {} {} {} {}\r\n" . format(
            self.tokenid, usernames_to, filepath, encoded_content)

        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "file sent to {}" . format(usernames_to)
        else:
            return "Error, {}" . format(result['message'])
        
    def get_presence(self, username):
        string = "getpresence {}\r\n".format(username)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return result['message']
        else:
            return "Error, {}".format(result['message'])
        
    def add_realm(self, realmid, realm_address, realm_port):
        if (self.tokenid == ""):
            return "Error, not authorized"
        string = "addrealm {} {} {} \r\n" . format(
            realmid, realm_address, realm_port)
        result = self.sendstring(string)
        if result['status'] == 'OK':
            return "Realm {} added" . format(realmid)
        else:
            return "Error, {}" . format(result['message'])

    def send_group_realm_message(self, realm_name, usernames_to, message):
        if self.token_id == "":
            return "Error, not authorized"
        string = "send_group_realm {} {} {} {}\r\n".format(
            self.token_id, realm_name, usernames_to, message)
        result = self.send_string(string)
        if result['status'] == 'OK':
            return "Message sent to group {} in realm {}".format(usernames_to, realm_name)
        else:
            return "Error: {}".format(result['message'])

    def send_group_file_to_realm(self, realm_name, usernames_to, file_path):
        if self.token_id == "":
            return "Error, not authorized"
        if not os.path.exists(file_path):
            return {'status': 'ERROR', 'message': 'File not found'}

        with open(file_path, 'rb') as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content).decode('utf-8')
        string = "send_group_file_realm {} {} {} {} {}\r\n".format(
            self.token_id, realm_name, usernames_to, file_path, encoded_content)
        result = self.send_string(string)
        if result['status'] == 'OK':
            return "File sent to group {} in realm {}".format(usernames_to, realm_name)
        else:
            return "Error: {}".format(result['message'])

    def inbox(self):
        if self.tokenid == "":
            return "Error, not authorized"

        string = "inbox {} \r\n".format(self.tokenid)
        result = self.sendstring(string)

        if result['status'] == 'OK':
            messages = result['messages']
            emoji_mapping = {
                "\ud83d\ude42": "🙂",
                "\ud83d\ude01": "😁",
                "\u2639\ufe0f": "☹️",
                "\ud83d\ude2d": "😭"
            }
            for user, msgs in messages.items():
                for msg in msgs:
                    for emoji, replacement in emoji_mapping.items():
                        msg['msg'] = msg['msg'].replace(emoji, replacement)

            return messages
        else:
            return "Error, {}".format(result['message'])
        
    def notification(self, messages):
        unread_messages = {}
        for user, msgs in messages.items():
            unread_msgs = [msg for msg in msgs if not msg.get('read', False)]
            if unread_msgs:
                unread_messages[user] = unread_msgs
        return unread_messages
        
    def get_realm_inbox(self, realm_name):
        if self.token_id == "":
            return "Error, not authorized"

        string = "get_realm_inbox {} {}\r\n".format(self.token_id, realm_name)
        print("Sending: " + string)
        result = self.send_string(string)
        print("Received: " + str(result))

        if result['status'] == 'OK':
            messages = result['messages']
            unread_messages = self.get_unread_messages(messages)  # Get unread messages using the get_unread_messages method
            if not unread_messages:
                return "No new notifications"

            output = "New Notifications from realm {}:\n".format(realm_name)
            for user, msgs in unread_messages.items():
                output += "User: {}\n".format(user)
                for msg in msgs:
                    output += "Message: {}\n".format(msg["msg"])

            # Handle new message received from realm separately
            new_messages = result['new_messages']
            if new_messages:
                output += "New Message from Realm {}: {}\n".format(realm_name, new_messages)

            return output
        else:
            return "Error: {}".format(result['message'])


if __name__ == "__main__":
    cc = ChatClient()
    # j = Chat()
    while True:
        print("\n")
        cmdline = input("Command {}:" . format(cc.tokenid))
        print(cc.proses(cmdline))
