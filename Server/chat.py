import sys
import os
from os.path import join, dirname, realpath
import json
import uuid
import logging
from queue import Queue
import threading
import socket
from datetime import datetime
import base64


class RealmCommunicationThread(threading.Thread):
    def __init__(self, chat, target_realm_address, target_realm_port):
        self.chat = chat
        self.target_realm_address = target_realm_address
        self.target_realm_port = target_realm_port
        self.queue = Queue()  # Queue for outgoing messages to the other realm
        self.sock = None
        threading.Thread.__init__(self)

    @property
    def queue(self):
        return self._queue
    
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(
                (self.target_realm_address, self.target_realm_port))
            return True
        except socket.error:
            return False

    def run(self):
        if not self.sock:
            return

        try:
            while True:
                # Receiving data from the other realm
                data = self.sock.recv(1024)
                if data:
                    command = data.decode()
                    response = self.chat.proses(command)
                    # Sending a response to the other realm
                    self.sock.sendall(json.dumps(response).encode())

                # Check if there are messages to be sent
                while not self.queue.empty():
                    msg = self.queue.get()
                    self.sock.sendall(json.dumps(msg).encode())

        except socket.error:
            # Handle socket errors here
            print("Socket error occurred")
        finally:
            # Close the socket when the thread ends or an error occurs
            self.sock.close()

    def put(self, msg):
        self.queue.put(msg)


class Chat:
    def __init__(self):
        self.sessions = {}
        self.users = {}
        self.connectedUsers = {}
        self.realms = {}
        self.load_user_data() # Load user data from db/user.json file

    # Region ============================= Load User Data =============================
    def load_user_data(self):
        try:
            with open('./db/user.json', 'r') as file:
                self.users = json.load(file)
        except FileNotFoundError:
            self.users = {}
    # End Region ============================= Load User Data =============================

    # Region ============================= Save User to JSON =============================
    def save_user_data(self):
        with open('./db/user.json', 'w') as file:
            json.dump(self.users, file, indent=4)
    # End Region ============================= Save User to JSON =============================
    
    # Region ============================= Register User =============================
    def add_user(self, username, user_data):
        self.users[username] = user_data
        self.save_user_data()
    # End Region ============================= Register User =============================

    # Region ============================= Command List =============================
    def proses(self, data):
        j = data.split(" ")
        try:
            command = j[0].strip()
            if command == 'register':
                username = j[1].strip()
                password = j[2].strip()
                name = j[3].strip()
                country = j[4].strip()
                logging.warning("REGISTER: register {} {} {} {}" . format(username, password, name, country))
                return self.register_user(username, password, name, country)
            
            elif (command == 'auth'):
                username = j[1].strip()
                password = j[2].strip()
                logging.warning(
                    "AUTH: auth {} {}" . format(username, password))
                return self.autentikasi_user(username, password)
            
            elif (command == 'send'):
                sessionid = j[1].strip()
                usernameto = j[2].strip()
                message = ""
                for w in j[3:]:
                    message = "{} {}" . format(message, w)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SEND: session {} send message from {} to {}" . format(
                    sessionid, usernamefrom, usernameto))
                return self.send_message(sessionid, usernamefrom, usernameto, message)
            
            elif (command == 'inbox'):
                sessionid = j[1].strip()
                username = self.sessions[sessionid]['username']
                logging.warning("INBOX: {}" . format(sessionid))
                return self.get_inbox(username)
            
            elif (command == 'sendgroup'):
                sessionid = j[1].strip()
                group_usernames = j[2].strip().split(',')
                message = ""
                for w in j[3:]:
                    message = "{} {}" . format(message, w)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SEND: session {} send message from {} to {}" . format(
                    sessionid, usernamefrom, group_usernames))
                return self.send_group_message(sessionid, usernamefrom, group_usernames, message)
            
            elif (command == 'sendfile'):
                sessionid = j[1].strip()
                usernameto = j[2].strip()
                filepath = j[3].strip()
                encoded_file = j[4].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDFILE: session {} send file from {} to {}" . format(
                    sessionid, usernamefrom, usernameto))
                return self.send_file(sessionid, usernamefrom, usernameto, filepath, encoded_file)
            
            elif (command == 'sendgroupfile'):
                sessionid = j[1].strip()
                usernamesto = j[2].strip().split(',')
                filepath = j[3].strip()
                encoded_file = j[4].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDGROUPFILE: session {} send file from {} to {}" . format(
                    sessionid, usernamefrom, usernamesto))
                return self.send_group_file(sessionid, usernamefrom, usernamesto, filepath, encoded_file)
            
            elif command == 'getpresence':
                username = j[1].strip()
                logging.warning("GETPRESENCE: get presence for user {}".format(username))
                return self.get_presence(username)
            
            elif command == 'deletelastmessage':
                username = j[1].strip()
                result = self.delete_last_message(username)
                logging.warning("DELETELASTMESSAGE: delete last message for user {}".format(username))
                return result
            
            elif command == 'forwardmessage':
                source_username = j[1].strip()
                destination_username = j[2].strip()
                result = self.forward_message(source_username, destination_username)
                logging.warning("FORWARDMESSAGE: forward message from {} to {}".format(source_username, destination_username))
                return result
            
            elif command == 'replymessage':
                username = j[1].strip()
                message = ' '.join(j[2:]).strip()
                result = self.reply_message(username, message)
                logging.warning("REPLYMESSAGE: reply message for user {}".format(username))
                return result
            
            elif (command == 'realm'):
                realm_id = j[1].strip()
                if realm_id in self.realms:
                    return self.realms[realm_id].proses(" ".join(j[2:]))
                else:
                    return {'status': 'ERROR', 'message': 'Realm Tidak Ada'}
                
            elif (command == 'addrealm'):
                realm_name = j[1].strip()
                ipaddress_dest = j[2].strip()
                port_dest = int(j[3].strip())
                self.add_realm(realm_name, ipaddress_dest, port_dest)
                return {'status': 'OK'}
            
            elif (command == 'recvrealm'):
                realm_name = j[1].strip()
                ipaddress_dest = j[2].strip()
                port_dest = int(j[3].strip())
                return self.recv_realm(realm_name, ipaddress_dest, port_dest, data)
            
            elif command == 'removerealm':
                realm_name = j[1].strip()
                return self.remove_realm(realm_name)

            elif command == 'sendrealm':
                sessionid = j[1].strip()
                realm_name = j[2].strip()
                username_dest = j[3].strip()
                message = " ".join(j[4:])
                logging.warning("SENDREALM: session {} sends a message from {} to {} in realm {}".format(
                    sessionid, self.sessions[sessionid]['username'], username_dest, realm_name))
                return self.send_realm_message(sessionid, realm_name, username_dest, message)

            elif command == 'sendprivaterealm':
                sessionid = j[1].strip()
                realm_name = j[2].strip()
                username_dest = j[3].strip()
                message = " ".join(j[4:])
                username_from = self.sessions[sessionid]['username']
                logging.warning("SENDPRIVATEREALM: session {} sends a message from {} to {} in realm {}".format(
                    sessionid, username_from, username_dest, realm_name))
                return self.send_realm_message(sessionid, realm_name, username_dest, message)

            elif command == 'recvrealmprivatemsg':
                username_from = j[1].strip()
                realm_name = j[2].strip()
                username_dest = j[3].strip()
                message = " ".join(j[4:])
                logging.warning("RECVREALMPRIVATEMSG: received message from {} to {} in realm {}".format(
                    username_from, username_dest, realm_name))
                return self.recv_realm_message(realm_name, username_from, username_dest, message, data)
  
            elif command == 'sendfilerealm':
                sessionid = j[1].strip()
                realm_name = j[2].strip()
                username_dest = j[3].strip()
                file_path = j[4].strip()
                encoded_file = j[5].strip()
                username_depart = self.sessions[sessionid]['username']
                logging.warning("SENDFILEREALM: session {} sends a file from {} to {} in realm {}".format(
                    sessionid, username_depart, username_dest, realm_name))
                return self.send_file_realm(sessionid, realm_name, username_depart, username_dest, file_path, encoded_file, data)


            elif command == 'recvfilerealm':
                username_depart = j[1].strip()
                realm_name = j[2].strip()
                username_dest = j[3].strip()
                file_path = j[4].strip()
                encoded_file = j[5].strip()
                logging.warning("RECVFILEREALM: received file from {} to {} in realm {}".format(
                    username_depart, username_dest, realm_name))
                return self.recv_file_realm(realm_name, username_depart, username_dest, file_path, encoded_file, data)

            elif command == 'sendgrouprealm':
                sessionid = j[1].strip()
                realm_name = j[2].strip()
                usernames_dest = j[3].strip().split(',')
                message = " ".join(j[4:])
                username_depart = self.sessions[sessionid]['username']
                logging.warning("SENDGROUPREALM: session {} sends a message from {} to {} in realm {}".format(
                    sessionid, username_depart, usernames_dest, realm_name))
                return self.send_group_realm_message(sessionid, realm_name, username_depart, usernames_dest, message, data)

            elif command == 'recvrealmgroupmsg':
                username_depart = j[1].strip()
                realm_name = j[2].strip()
                usernames_dest = j[3].strip().split(',')
                message = " ".join(j[4:])
                logging.warning("RECVGROUPREALM: received message from {} to {} in realm {}".format(
                    username_depart, usernames_dest, realm_name))
                return self.recv_group_realm_message(realm_name, username_depart, usernames_dest, message, data)

            elif command == 'sendgroupfilerealm':
                sessionid = j[1].strip()
                realm_name = j[2].strip()
                usernames_dest = j[3].strip().split(',')
                file_path = j[4].strip()
                encoded_file = j[5].strip()
                username_depart = self.sessions[sessionid]['username']
                logging.warning("SENDGROUPFILEREALM: session {} sends a file from {} to {} in realm {}".format(
                    sessionid, username_depart, usernames_dest, realm_name))
                return self.send_group_file_realm(sessionid, realm_name, username_depart, usernames_dest, file_path, encoded_file, data)

            elif command == 'recvgroupfilerealm':
                username_depart = j[1].strip()
                realm_name = j[2].strip()
                usernames_dest = j[3].strip().split(',')
                file_path = j[4].strip()
                encoded_file = j[5].strip()
                logging.warning("RECVGROUPFILEREALM: received file from {} to {} in realm {}".format(
                    username_depart, usernames_dest, realm_name))
                return self.recv_group_file_realm(realm_name, username_depart, usernames_dest, file_path, encoded_file, data)

            elif command == 'getrealminbox':
                sessionid = j[1].strip()
                realm_name = j[2].strip()
                username = self.sessions[sessionid]['username']
                logging.warning("GETREALMINBOX: {} from realm {}".format(
                    sessionid, realm_name))
                return self.get_realm_inbox(username, realm_name)

            elif command == 'getrealmchat':
                realm_name = j[1].strip()
                username = j[2].strip()
                logging.warning("GETREALMCHAT: from realm {}".format(realm_name))
                return self.get_realm_chat(realm_name, username)

            
            else:
                print(command)
                return {'status': 'ERROR', 'message': '**Protocol Tidak Benar'}
            
        except KeyError:
            return {'status': 'ERROR', 'message': 'Informasi tidak ditemukan'}
        except IndexError:
            return {'status': 'ERROR', 'message': '--Protocol Tidak Benar'}
    # EndRegion ========================== Command List ==========================
        
    # Region ============================= Register New User =============================
    def register_user(self, username, password, name, country):
        if username in self.users:
            return {'status': 'ERROR', 'message': 'Username already exists'}

        new_user = {
            "nama": name,
            "negara": country,
            "password": password,
            "incoming": {},
            "outgoing": {}
        }

        # Save new user to user.json file
        try:
            with open('./db/user.json', 'r+') as file:
                data = json.load(file)
                data[username] = new_user
                file.seek(0)
                json.dump(data, file, indent=4)
                file.truncate()
        except FileNotFoundError:
            return {'status': 'ERROR', 'message': 'user.json file not found'}
        except json.JSONDecodeError:
            return {'status': 'ERROR', 'message': 'user.json file is not valid JSON'}

        self.users[username] = new_user

        return {'status': 'OK', 'message': 'User registered successfully'}
    # EndRegion ========================== Register New User =============================

    # Region ============================= Login User =============================
    def autentikasi_user(self, username, password):
        if username not in self.users:
            return {'status': 'ERROR', 'message': 'User Tidak Ada'}
        if self.users[username]['password'] != password:
            return {'status': 'ERROR', 'message': 'Password Salah'}
        tokenid = str(uuid.uuid4())
        self.sessions[tokenid] = {'username': username, 'userdetail': self.users[username]}
        self.connectedUsers[username] = True
        return {'status': 'OK', 'tokenid': tokenid}
    # EndRegion ========================== Login User =============================

    # Region ============================= Get User =============================
    def get_user(self, username):
        if (username not in self.users):
            return False
        return self.users[username]
    # EndRegion ========================== Get User =============================

    # Region ============================= Send Private Chat =============================
    def send_message(self, sessionid, username_from, username_dest, message):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}

        sender = self.get_user(username_from)
        receiver = self.get_user(username_dest)

        if not sender or not receiver:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        message = {
            'msg_from': sender['nama'],
            'msg_to': receiver['nama'],
            'msg': message,
            'timestamp': timestamp
        }

        outqueue_sender = sender.setdefault('outgoing', {})
        inqueue_receiver = receiver.setdefault('incoming', {})

        outqueue_sender.setdefault(username_from, Queue()).put(message)
        inqueue_receiver.setdefault(username_from, Queue()).put(message)

        return {'status': 'OK', 'message': 'Message Sent'}

    # EndRegion ========================== Send Private Chat =============================

    # Region ============================= Send Group Chat =============================
    def send_group_message(self, sessionid, username_from, group_usernames, message):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}

        sender = self.get_user(username_from)

        if not sender:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for username_dest in group_usernames:
            receiver = self.get_user(username_dest)

            if not receiver:
                continue

            message_data = {
                'msg_from': sender['nama'],
                'msg_to': receiver['nama'],
                'msg': message,
                'timestamp': timestamp
            }

            outqueue_sender = sender.setdefault('outgoing', {})
            inqueue_receiver = receiver.setdefault('incoming', {})

            outqueue_sender.setdefault(username_from, Queue()).put(message_data)
            inqueue_receiver.setdefault(username_from, Queue()).put(message_data)

        return {'status': 'OK', 'message': 'Message Sent'}

    # EndRegion ========================== Send Group Chat =============================

    # Region ============================= Get Inbox =============================
    def get_inbox(self, username):
        user = self.get_user(username)

        if not user:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        incoming = user.setdefault('incoming', {})
        msgs = {}

        for user in incoming:
            msgs[user] = []

            while not incoming[user].empty():
                msgs[user].append(incoming[user].get_nowait())

        return {'status': 'OK', 'messages': msgs}

    # EndRegion ========================== Get Inbox =============================

    # Region ============================= Send File to User =============================
    def send_file(self, sessionid, username_from, username_dest, filepath, encoded_file):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}

        sender = self.get_user(username_from)
        receiver = self.get_user(username_dest)

        if not sender or not receiver:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        filename = os.path.basename(filepath)
        message = {
            'msg_from': sender['nama'],
            'msg_to': receiver['nama'],
            'file_name': filename,
            'file_content': encoded_file
        }

        outqueue_sender = sender.setdefault('outgoing', {})
        inqueue_receiver = receiver.setdefault('incoming', {})

        outqueue_sender.setdefault(username_from, Queue()).put(json.dumps(message))
        inqueue_receiver.setdefault(
            username_from, Queue()).put(json.dumps(message))

        # Simpan file ke folder dengan nama yang mencerminkan waktu pengiriman dan nama asli file
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        folder_name = f"{now}_{username_from}_{username_dest}_{filename}"
        folder_path = join(dirname(realpath(__file__)), 'files/')
        os.makedirs(folder_path, exist_ok=True)
        folder_path = join(folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        file_destination = os.path.join(folder_path, filename)

        if 'b' in encoded_file[0]:
            msg = encoded_file[2:-1]

            with open(file_destination, "wb") as fh:
                fh.write(base64.b64decode(msg))
        else:
            tail = encoded_file.split()

        return {'status': 'OK', 'message': 'File Sent'} 
    # EndRegion ========================== Send File to User =============================

    # Region ============================= Send File to Group =============================
    def send_group_file(self, sessionid, username_from, usernames_dest, filepath, encoded_file):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}

        sender = self.get_user(username_from)

        if not sender:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        filename = os.path.basename(filepath)

        for username_dest in usernames_dest:
            receiver = self.get_user(username_dest)

            if not receiver:
                continue

            message = {
                'msg_from': sender['nama'],
                'msg_to': receiver['nama'],
                'file_name': filename,
                'file_content': encoded_file
            }

            outqueue_sender = sender.setdefault('outgoing', {})
            inqueue_receiver = receiver.setdefault('incoming', {})

            outqueue_sender.setdefault(
                username_from, Queue()).put(json.dumps(message))
            inqueue_receiver.setdefault(
                username_from, Queue()).put(json.dumps(message))

            # Simpan file ke folder dengan nama yang mencerminkan waktu pengiriman dan nama asli file
            now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            folder_name = f"{now}_{username_from}_{username_dest}_{filename}"
            folder_path = join(dirname(realpath(__file__)), 'files/')
            os.makedirs(folder_path, exist_ok=True)
            folder_path = join(folder_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            file_destination = os.path.join(folder_path, filename)

            if 'b' in encoded_file[0]:
                msg = encoded_file[2:-1]

                with open(file_destination, "wb") as fh:
                    fh.write(base64.b64decode(msg))
            else:
                tail = encoded_file.split()

        return {'status': 'OK', 'message': 'File Sent'}
    # EndRegion ========================== Send File to Group =============================
   
    # Region ============================= Get Presence Status =============================
    def get_presence(self, username):
        if username in self.users:
            user_data = self.users[username]
            if username in self.connectedUsers:
                presence = 'online'
            elif 'presence' in user_data:
                presence = user_data['presence']
            else:
                presence = 'offline'
            return {'status': 'OK', 'message': 'User {} is currently {}'  . format(username, presence)}
        else:
            return {'status': 'ERROR', 'message': 'User tidak ditemukan'}
    # EndRegion ========================== Get Presence Status =============================

    # Region ============================= Delete Last Message =============================
    def delete_last_message(self, username):
        inbox = self.get_inbox(username)

        if not inbox:
            return {'status': 'ERROR', 'message': 'Inbox is empty'}

        last_message = inbox.pop()
        deleted_message = last_message['message']

        self.update_inbox(username, inbox)

        return {'status': 'SUCCESS', 'message': 'Last message deleted', 'deleted_message': deleted_message}
    # EndRegion ========================== Delete Last Message =============================

    # Region ============================= Forward Message =============================
    def forward_message(self, session_id, username_from, username_to, message_id):
        if session_id not in self.sessions:
            return {'status': 'ERROR', 'message': 'Invalid session ID'}

        if username_from not in self.users or username_to not in self.users:
            return {'status': 'ERROR', 'message': 'Invalid usernames'}

        inbox_from = self.get_inbox(username_from)

        forwarded_message = None
        for message in inbox_from:
            if message['id'] == message_id:
                forwarded_message = message
                break

        if not forwarded_message:
            return {'status': 'ERROR', 'message': 'Message not found'}

        inbox_to = self.get_inbox(username_to)
        inbox_to.append(forwarded_message)
        self.update_inbox(username_to, inbox_to)

        return {'status': 'SUCCESS', 'message': 'Message forwarded'}
    # EndRegion ========================== Forward Message =============================

    # Region ============================= Reply Message =============================
    def reply_message(self, username, message):
        if username not in self.users:
            return {'status': 'ERROR', 'message': 'Invalid username'}

        inbox = self.get_inbox(username)

        if not inbox:
            return {'status': 'ERROR', 'message': 'No messages in inbox'}

        last_message = inbox[-1]  

        if 'replyable' in last_message and last_message['replyable']:
            last_message['reply'] = message

            inbox[-1] = last_message
            self.update_inbox(username, inbox)

            return {'status': 'SUCCESS', 'message': 'Message replied'}
        else:
            return {'status': 'ERROR', 'message': 'Last message is not replyable'}
    # EndRegion ========================== Reply Message =============================

    # Region ============================= Add Realm =============================
    def add_realm(self, realm_name, ipaddress_dest, port_dest):
        if realm_name in self.realms:
            return {'status': 'ERROR', 'message': 'Realm already exists'}

        realm_thread = RealmCommunicationThread(self, ipaddress_dest, port_dest)
        self.realms[realm_name] = realm_thread

        if realm_thread.connect():
            realm_thread.start()
            return {'status': 'OK', 'message': 'Realm added and connected successfully'}
        else:
            del self.realms[realm_name]
            return {'status': 'ERROR', 'message': 'Failed to connect to the realm'}

    # EndRegion ========================== Add Realm =============================

    # Region ============================= Recv Realm =============================
    def recv_realm(self, realm_name, ipaddress_dest, port_dest, data):
        if realm_name in self.realms:
            return {'status': 'ERROR', 'message': 'Realm already exists'}

        realm_thread = RealmCommunicationThread(self, ipaddress_dest, port_dest)
        self.realms[realm_name] = realm_thread

        if realm_thread.connect():
            return {'status': 'OK', 'message': 'Realm received and connected successfully'}
        else:
            del self.realms[realm_name]
            return {'status': 'ERROR', 'message': 'Failed to connect to the realm'}
    # EndRegion ========================== Recv Realm =============================
   
    # Region ============================= Remove Realm =============================
    def remove_realm(self, realm_name):
        if realm_name not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm does not exist'}

        realm_thread = self.realms[realm_name]
        realm_thread.stop()
        del self.realms[realm_name]

        return {'status': 'OK', 'message': 'Realm removed successfully'}
    # EndRegion ========================== Remove Realm =============================

    # Region ============================= Send Realm Message =============================
    def send_realm_message(self, sessionid, realm_name, username_dest, message):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if realm_name not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ada'}
        username_depart = self.sessions[sessionid]['username']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message_data = {
            'msg_from': username_depart,
            'msg_to': username_dest,
            'msg': message,
            'timestamp': timestamp
        }
        realm_thread = self.realms[realm_name]
        realm_thread.put(message_data)
        return {'status': 'OK', 'message': 'Message Sent to Realm'}
    # EndRegion ========================== Send Realm Message =============================

    # Region ============================= Recv Realm Message =============================
    def recv_realm_message(self, realm_name, username_depart, username_dest, message, data):
        if realm_name not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_depart)
        s_to = self.get_user(username_dest)
        if s_fr is False or s_to is False:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message_data = {
            'msg_from': s_fr['nama'],
            'msg_to': s_to['nama'],
            'msg': message,
            'timestamp': timestamp
        }
        realm_thread = self.realms[realm_name]
        realm_thread.put(message_data)
        return {'status': 'OK', 'message': 'Message Sent to Realm'}
    # EndRegion ========================== Recv Realm Message =============================
    
   # Region ============================= Send File to Realm =============================
    def send_file_realm(self, sessionid, realm_name, username_depart, username_dest, file_path, encoded_file, data):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if realm_name not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_depart)
        s_to = self.get_user(username_dest)
        if s_fr is False or s_to is False:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        filename = os.path.basename(file_path)
        message = {
            'msg_from': s_fr['nama'],
            'msg_to': s_to['nama'],
            'file_name': filename,
            'file_content': encoded_file
        }
        realm_thread = self.realms[realm_name]
        realm_thread.put(message)

        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        folder_name = f"{now}_{username_depart}_{username_dest}_{filename}"
        folder_path = join(dirname(realpath(__file__)), 'files/')
        os.makedirs(folder_path, exist_ok=True)
        folder_path = join(folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        file_destination = os.path.join(folder_path, filename)
        if 'b' in encoded_file[0]:
            msg = encoded_file[2:-1]
            with open(file_destination, "wb") as fh:
                fh.write(msg)
        else:
            with open(file_destination, "w") as fh:
                fh.write(encoded_file)

        return {'status': 'OK', 'message': 'File Sent to Realm'}
    # EndRegion ========================== Send File to Realm =============================

    def validate_file_path(file_path):
        if not os.path.exists(file_path):
            return False
        return True


    def validate_encoded_file(encoded_file):
        try:
            base64.b64decode(encoded_file)
            return True
        except:
            return False

    # Region ============================= Recv File from Realm =============================
    def recv_file_realm(self, realm_name, username_depart, username_dest, file_path, encoded_file, data):
        if realm_name not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_depart)
        s_to = self.get_user(username_dest)
        if s_fr is False or s_to is False:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        filename = os.path.basename(file_path)
        # Validate inputs
        if not self.validate_file_path(file_path):
            return {'status': 'ERROR', 'message': 'Invalid file path'}

        if not self.validate_encoded_file(encoded_file):
            return {'status': 'ERROR', 'message': 'Invalid encoded file'}
        
        message = {
            'msg_from': s_fr['nama'],
            'msg_to': s_to['nama'],
            'file_name': filename,
            'file_content': encoded_file
        }
        realm_thread = self.realms[realm_name]
        realm_thread.put(message)

        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        folder_name = f"{now}_{username_depart}_{username_dest}_{filename}"
        folder_path = join(dirname(realpath(__file__)), 'files/')
        os.makedirs(folder_path, exist_ok=True)
        folder_path = join(folder_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        file_destination = os.path.join(folder_path, filename)
        if 'b' in encoded_file[0]:
            msg = encoded_file[2:-1]
            with open(file_destination, "wb") as fh:
                fh.write(base64.b64decode(msg))
        else:
            tail = encoded_file.split()

        return {'status': 'OK', 'message': 'File Received from Realm'}
    # EndRegion ========================== Recv File from Realm =============================
    
    # Region ============================= Send Realm Group Message =============================
    def send_group_realm_message(self, sessionid, realm_name, group_usernames, message):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if realm_name not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ada'}
        username_from = self.sessions[sessionid]['username']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for username_to in group_usernames:
            message_data = {
                'msg_from': username_from,
                'msg_to': username_to,
                'msg': message,
                'timestamp': timestamp
            }
            realm_thread = self.realms[realm_name]
            realm_thread.put(message_data)
            realm_thread.queue.put(message_data)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}
    # EndRegion ========================== Send Realm Group Message =============================

    # Region ============================= Recv Realm Group Message =============================
    def recv_group_realm_message(self, realm_name, username_from, usernames_to, message, data):
        if realm_name not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message_data = {
                'msg_from': s_fr['nama'],
                'msg_to': s_to['nama'],
                'msg': message,
                'timestamp': timestamp
            }
            realm_thread = self.realms[realm_name]
            realm_thread.put(message_data)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}
    # EndRegion ========================== Recv Realm Group Message =============================

    # Region ============================= Send Realm Group File =============================
    def send_group_file_realm(self, sessionid, realm_name, username_depart, usernames_dest, file_path, encoded_file, data):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if realm_name not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_depart)

        if s_fr == False:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        filename = os.path.basename(file_path)
        for username_to in usernames_dest:
            s_to = self.get_user(username_to)
            message_data = {
                'msg_from': s_fr['nama'],
                'msg_to': s_to['nama'],
                'file_name': filename,
                'file_content': encoded_file
            }
            realm_thread = self.realms[realm_name]
            realm_thread.put(message_data)

            now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            folder_name = f"{now}_{username_depart}_{username_to}_{filename}"
            folder_path = join(dirname(realpath(__file__)), 'files/')
            os.makedirs(folder_path, exist_ok=True)
            folder_path = join(folder_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            file_destination = os.path.join(folder_path, filename)
            if 'b' in encoded_file[0]:
                msg = encoded_file[2:-1]

                with open(file_destination, "wb") as fh:
                    fh.write(base64.b64decode(msg))
            else:
                tail = encoded_file.split()

        j = data.split()
        j[0] = "recvgroupfilerealm"
        j[1] = username_depart
        data = ' '.join(j)
        data += "\r\n"
        realm_thread.sendstring(data)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}
    # EndRegion ========================== Send Realm Group File =============================

    # Region ============================= Recv Realm Group File =============================
    def recv_group_file_realm(self, realm_name, username_from, usernames_to, file_path, encoded_file, data):
        if realm_name not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)

        if s_fr == False:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        filename = os.path.basename(file_path)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message_data = {
                'msg_from': s_fr['nama'],
                'msg_to': s_to['nama'],
                'file_name': filename,
                'file_content': encoded_file
            }
            realm_thread = self.realms[realm_name]
            realm_thread.put(message_data)

            now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            folder_name = f"{now}_{username_from}_{username_to}_{filename}"
            folder_path = join(dirname(realpath(__file__)), 'files/')
            os.makedirs(folder_path, exist_ok=True)
            folder_path = join(folder_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            file_destination = os.path.join(folder_path, filename)
            if 'b' in encoded_file[0]:
                msg = encoded_file[2:-1]

                with open(file_destination, "wb") as fh:
                    fh.write(base64.b64decode(msg))
            else:
                tail = encoded_file.split()

        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}
    # EndRegion ========================== Recv Realm Group File =============================

    # Region ============================= Get Realm Inbox =============================
    def get_realm_inbox(self, sessionid, realm_name):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if realm_name not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ada'}

        username = self.sessions[sessionid]['username']
        msgs = []

        while not self.realms[realm_name].empty():
            msgs.append(self.realms[realm_name].get_nowait())

        return {'status': 'OK', 'messages': msgs}
    # EndRegion ========================== Get Realm Inbox =============================


if __name__ == "__main__":
    j = Chat()
    sesi = j.proses("auth messi surabaya")
    print(sesi)
    # sesi = j.autentikasi_user('messi','surabaya')
    # print sesi
    tokenid = sesi['tokenid']
    print(j.proses("send {} henderson hello gimana kabarnya son " . format(tokenid)))
    print(j.proses("send {} messi hello gimana kabarnya mess " . format(tokenid)))

    # print j.send_message(tokenid,'messi','henderson','hello son')
    # print j.send_message(tokenid,'henderson','messi','hello si')
    # print j.send_message(tokenid,'lineker','messi','hello si dari lineker')

    print("isi mailbox dari messi")
    print(j.get_inbox('messi'))
    print("isi mailbox dari henderson")
    print(j.get_inbox('henderson'))

    # print(j.proses("addrealm realm1 127.0.0.1 8889"))
    # print(j.proses("sendrealm {} realm1 henderson hello gimana kabarnya son " . format(tokenid)))
    # print(j.proses("getrealminbox {} realm1" . format(tokenid)))
