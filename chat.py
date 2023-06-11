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
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threading.Thread.__init__(self)

    def run(self):
        self.sock.connect((self.target_realm_address, self.target_realm_port))
        while True:
            # Menerima data dari realm lain
            data = self.sock.recv(1024)
            if data:
                command = data.decode()
                response = self.chat.proses(command)
                # Mengirim balasan ke realm lain
                self.sock.sendall(json.dumps(response).encode())
            # Check if there are messages to be sent
            while not self.queue.empty():
                msg = self.queue.get()
                self.sock.sendall(json.dumps(msg).encode())

    def put(self, msg):
        self.queue.put(msg)


class Chat:
    def __init__(self):
        self.sessions = {}
        self.users = {}
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
            elif (command == 'realm'):
                realm_id = j[1].strip()
                if realm_id in self.realms:
                    return self.realms[realm_id].proses(" ".join(j[2:]))
                else:
                    return {'status': 'ERROR', 'message': 'Realm Tidak Ada'}
            elif (command == 'addrealm'):
                realm_id = j[1].strip()
                target_realm_address = j[2].strip()
                target_realm_port = int(j[3].strip())
                self.add_realm(realm_id, target_realm_address,
                               target_realm_port)
                return {'status': 'OK'}
            elif (command == 'recvrealm'):
                realm_id = j[1].strip()
                realm_dest_address = j[2].strip()
                realm_dest_port = int(j[3].strip())
                return self.recv_realm(realm_id, realm_dest_address, realm_dest_port, data)
            elif (command == 'sendrealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                logging.warning("SENDREALM: session {} send message from {} to {} in realm {}".format(
                    sessionid, self.sessions[sessionid]['username'], usernameto, realm_id))
                return self.send_realm_message(sessionid, realm_id, usernameto, message)
            elif (command == 'sendprivaterealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                print(message)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDPRIVATEREALM: session {} send message from {} to {} in realm {}".format(
                    sessionid, usernamefrom, usernameto, realm_id))
                return self.send_realm_message(sessionid, realm_id, usernamefrom, usernameto, message, data)
            elif (command == 'recvrealmprivatemsg'):
                usernamefrom = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                print(message)
                logging.warning("RECVREALMPRIVATEMSG: recieve message from {} to {} in realm {}".format(
                    usernamefrom, usernameto, realm_id))
                return self.recv_realm_message(realm_id, usernamefrom, usernameto, message, data)
            elif (command == 'sendfilerealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                filepath = j[4].strip()
                encoded_file = j[5].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDFILEREALM: session {} send file from {} to {} in realm {}".format(
                    sessionid, usernamefrom, usernameto, realm_id))
                return self.send_file_realm(sessionid, realm_id, usernamefrom, usernameto, filepath, encoded_file, data)
            elif (command == 'recvfilerealm'):
                usernamefrom = j[1].strip()
                realm_id = j[2].strip()
                usernameto = j[3].strip()
                filepath = j[4].strip()
                encoded_file = j[5].strip()
                logging.warning("RECVFILEREALM: recieve file from {} to {} in realm {}".format(
                    usernamefrom, usernameto, realm_id))
                return self.recv_file_realm(realm_id, usernamefrom, usernameto, filepath, encoded_file, data)
            elif (command == 'sendgrouprealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(',')
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDGROUPREALM: session {} send message from {} to {} in realm {}".format(
                    sessionid, usernamefrom, usernamesto, realm_id))
                return self.send_group_realm_message(sessionid, realm_id, usernamefrom, usernamesto, message, data)
            elif (command == 'recvrealmgroupmsg'):
                usernamefrom = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(',')
                message = ""
                for w in j[4:]:
                    message = "{} {}".format(message, w)
                logging.warning("RECVGROUPREALM: send message from {} to {} in realm {}".format(
                    usernamefrom, usernamesto, realm_id))
                return self.recv_group_realm_message(realm_id, usernamefrom, usernamesto, message, data)
            elif (command == 'sendgroupfilerealm'):
                sessionid = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(',')
                filepath = j[4].strip()
                encoded_file = j[5].strip()
                usernamefrom = self.sessions[sessionid]['username']
                logging.warning("SENDGROUPFILEREALM: session {} send file from {} to {} in realm {}".format(
                    sessionid, usernamefrom, usernamesto, realm_id))
                return self.send_group_file_realm(sessionid, realm_id, usernamefrom, usernamesto, filepath, encoded_file, data)
            elif (command == 'recvgroupfilerealm'):
                usernamefrom = j[1].strip()
                realm_id = j[2].strip()
                usernamesto = j[3].strip().split(',')
                filepath = j[4].strip()
                encoded_file = j[5].strip()
                logging.warning("SENDGROUPFILEREALM: recieve file from {} to {} in realm {}".format(
                    usernamefrom, usernamesto, realm_id))
                return self.recv_group_file_realm(realm_id, usernamefrom, usernamesto, filepath, encoded_file, data)
            elif (command == 'getrealminbox'):
                sessionid = j[1].strip()
                realmid = j[2].strip()
                username = self.sessions[sessionid]['username']
                logging.warning(
                    "GETREALMINBOX: {} from realm {}".format(sessionid, realmid))
                return self.get_realm_inbox(username, realmid)
            elif (command == 'getrealmchat'):
                realmid = j[1].strip()
                username = j[2].strip()
                logging.warning("GETREALMCHAT: from realm {}".format(realmid))
                return self.get_realm_chat(realmid, username)
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
        if (username not in self.users):
            return {'status': 'ERROR', 'message': 'User Tidak Ada'}
        if (self.users[username]['password'] != password):
            return {'status': 'ERROR', 'message': 'Password Salah'}
        tokenid = str(uuid.uuid4())
        self.sessions[tokenid] = {
            'username': username, 'userdetail': self.users[username]}
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
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)

        if (s_fr == False or s_to == False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        message = {'msg_from': s_fr['nama'],
                   'msg_to': s_to['nama'], 'msg': message}
        outqueue_sender = s_fr['outgoing']
        inqueue_receiver = s_to['incoming']
        try:
            outqueue_sender[username_from].put(message)
        except KeyError:
            outqueue_sender[username_from] = Queue()
            outqueue_sender[username_from].put(message)
        try:
            inqueue_receiver[username_from].put(message)
        except KeyError:
            inqueue_receiver[username_from] = Queue()
            inqueue_receiver[username_from].put(message)
        return {'status': 'OK', 'message': 'Message Sent'}
    # EndRegion ========================== Send Private Chat =============================

    # Region ============================= Send Group Chat =============================
    def send_group_message(self, sessionid, username_from, group_usernames, message):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        if s_fr is False:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        for username_dest in group_usernames:
            s_to = self.get_user(username_dest)
            if s_to is False:
                continue
            message = {'msg_from': s_fr['nama'],
                       'msg_to': s_to['nama'], 'msg': message}
            outqueue_sender = s_fr['outgoing']
            inqueue_receiver = s_to['incoming']
            try:
                outqueue_sender[username_from].put(message)
            except KeyError:
                outqueue_sender[username_from] = Queue()
                outqueue_sender[username_from].put(message)
            try:
                inqueue_receiver[username_from].put(message)
            except KeyError:
                inqueue_receiver[username_from] = Queue()
                inqueue_receiver[username_from].put(message)
        return {'status': 'OK', 'message': 'Message Sent'}
    # EndRegion ========================== Send Group Chat =============================

    # Region ============================= Get Inbox =============================
    def get_inbox(self, username):
        s_fr = self.get_user(username)
        incoming = s_fr['incoming']
        msgs = {}
        for users in incoming:
            msgs[users] = []
            while not incoming[users].empty():
                msgs[users].append(s_fr['incoming'][users].get_nowait())
        return {'status': 'OK', 'messages': msgs}
    # EndRegion ========================== Get Inbox =============================

    # Region ============================= Send File to User =============================
    def send_file(self, sessionid, username_from, username_dest, filepath, encoded_file):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}

        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)

        if s_fr is False or s_to is False:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        filename = os.path.basename(filepath)
        message = {
            'msg_from': s_fr['nama'],
            'msg_to': s_to['nama'],
            'file_name': filename,
            'file_content': encoded_file
        }

        outqueue_sender = s_fr['outgoing']
        inqueue_receiver = s_to['incoming']
        try:
            outqueue_sender[username_from].put(json.dumps(message))
        except KeyError:
            outqueue_sender[username_from] = Queue()
            outqueue_sender[username_from].put(json.dumps(message))
        try:
            inqueue_receiver[username_from].put(json.dumps(message))
        except KeyError:
            inqueue_receiver[username_from] = Queue()
            inqueue_receiver[username_from].put(json.dumps(message))

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
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        if s_fr is False:
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        filename = os.path.basename(filepath)
        for username_dest in usernames_dest:
            s_to = self.get_user(username_dest)
            if s_to is False:
                continue
            message = {
                'msg_from': s_fr['nama'],
                'msg_to': s_to['nama'],
                'file_name': filename,
                'file_content': encoded_file
            }

            outqueue_sender = s_fr['outgoing']
            inqueue_receiver = s_to['incoming']
            try:
                outqueue_sender[username_from].put(json.dumps(message))
            except KeyError:
                outqueue_sender[username_from] = Queue()
                outqueue_sender[username_from].put(json.dumps(message))
            try:
                inqueue_receiver[username_from].put(json.dumps(message))
            except KeyError:
                inqueue_receiver[username_from] = Queue()
                inqueue_receiver[username_from].put(json.dumps(message))

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
    
    # Region ============================= Add Realm =============================
    def add_realm(self, realm_id, target_realm_address, target_realm_port):
        self.realms[realm_id] = RealmCommunicationThread(
            self, target_realm_address, target_realm_port)
        self.realms[realm_id].start()
    # EndRegion ========================== Add Realm =============================

    # Region ============================= Recv Realm =============================
    def recv_realm(self, realm_id, realm_dest_address, realm_dest_port, data):
        self.realms[realm_id] = RealmCommunicationThread(
            self, realm_dest_address, realm_dest_port)
        return {'status': 'OK'}
    # EndRegion ========================== Recv Realm =============================
    
    # Region ============================= Send Realm Message =============================
    def send_realm_message(self, sessionid, realm_id, username_to, message):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ada'}
        username_from = self.sessions[sessionid]['username']
        message = {'msg_from': username_from,
                   'msg_to': username_to, 'msg': message}
        self.realms[realm_id].put(message)
        self.realms[realm_id].queue.put(message)
        return {'status': 'OK', 'message': 'Message Sent to Realm'}
    # EndRegion ========================== Send Realm Message =============================

    # Region ============================= Recv Realm Message =============================
    def recv_realm_message(self, realm_id, username_from, username_dest, message, data):
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if (s_fr==False or s_to==False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        message = { 'msg_from': s_fr['nama'], 'msg_to': s_to['nama'], 'msg': message }
        self.realms[realm_id].put(message)
        return {'status': 'OK', 'message': 'Message Sent to Realm'}
    # EndRegion ========================== Recv Realm Message =============================
    
    # Region ============================= Send File to Realm =============================
    def send_file_realm(self, sessionid, realm_id, username_from, username_dest, filepath, encoded_file, data):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if (s_fr==False or s_to==False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        
        filename = os.path.basename(filepath)
        message = {
            'msg_from': s_fr['nama'],
            'msg_to': s_to['nama'],
            'file_name': filename,
            'file_content': encoded_file
        }
        self.realms[realm_id].put(message)
        
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
        print(file_destination)
        j = data.split()
        j[0] = "recvfilerealm"
        j[1] = username_from
        data = ' '.join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {'status': 'OK', 'message': 'File Sent to Realm'}
    # EndRegion ========================== Send File to Realm =============================

    # Region ============================= Recv File from Realm =============================
    def recv_file_realm(self, realm_id, username_from, username_dest, filepath, encoded_file, data):
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        s_to = self.get_user(username_dest)
        if (s_fr==False or s_to==False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}
        
        filename = os.path.basename(filepath)
        message = {
            'msg_from': s_fr['nama'],
            'msg_to': s_to['nama'],
            'file_name': filename,
            'file_content': encoded_file
        }
        self.realms[realm_id].put(message)
        
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
        
        return {'status': 'OK', 'message': 'File Received to Realm'}
    # EndRegion ========================== Recv File from Realm =============================
    
    # Region ============================= Send Realm Group Message =============================
    def send_group_realm_message(self, sessionid, realm_id, group_usernames, message):
        if sessionid not in self.sessions:
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if realm_id not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ada'}
        username_from = self.sessions[sessionid]['username']
        for username_to in group_usernames:
            message = {'msg_from': username_from,
                       'msg_to': username_to, 'msg': message}
            self.realms[realm_id].put(message)
            self.realms[realm_id].queue.put(message)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}
    # EndRegion ========================== Send Realm Group Message =============================

    # Region ============================= Recv Realm Group Message =============================
    def recv_group_realm_message(self, realm_id, username_from, usernames_to, message, data):
        if realm_id not in self.realms:
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {'msg_from': s_fr['nama'],
                       'msg_to': s_to['nama'], 'msg': message}
            self.realms[realm_id].put(message)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}
    # EndRegion ========================== Recv Realm Group Message =============================

    # Region ============================= Send Realm Group File =============================
    def send_group_file_realm(self, sessionid, realm_id, username_from, usernames_to, filepath, encoded_file, data):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)

        if (s_fr == False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        filename = os.path.basename(filepath)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {
                'msg_from': s_fr['nama'],
                'msg_to': s_to['nama'],
                'file_name': filename,
                'file_content': encoded_file
            }
            self.realms[realm_id].put(message)

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

        j = data.split()
        j[0] = "recvgroupfilerealm"
        j[1] = username_from
        data = ' '.join(j)
        data += "\r\n"
        self.realms[realm_id].sendstring(data)
        return {'status': 'OK', 'message': 'Message Sent to Group in Realm'}
    # EndRegion ========================== Send Realm Group File =============================

    # Region ============================= Recv Realm Group File =============================
    def recv_group_file_realm(self, realm_id, username_from, usernames_to, filepath, encoded_file, data):
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ditemukan'}
        s_fr = self.get_user(username_from)

        if (s_fr == False):
            return {'status': 'ERROR', 'message': 'User Tidak Ditemukan'}

        filename = os.path.basename(filepath)
        for username_to in usernames_to:
            s_to = self.get_user(username_to)
            message = {
                'msg_from': s_fr['nama'],
                'msg_to': s_to['nama'],
                'file_name': filename,
                'file_content': encoded_file
            }
            self.realms[realm_id].put(message)

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
    def get_realm_inbox(self, sessionid, realm_id):
        if (sessionid not in self.sessions):
            return {'status': 'ERROR', 'message': 'Session Tidak Ditemukan'}
        if (realm_id not in self.realms):
            return {'status': 'ERROR', 'message': 'Realm Tidak Ada'}
        username = self.sessions[sessionid]['username']
        msgs = []
        while not self.realms[realm_id].empty():
            msgs.append(self.realms[realm_id].get_nowait())
        return {'status': 'OK', 'messages': msgs}


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
