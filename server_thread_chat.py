from socket import *
import socket
import threading
import time
import sys
import json
import logging
from chat import Chat

chatserver = Chat()


class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address, client_status):
        self.connection = connection
        self.address = address
        self.client_status = client_status  # Reference to the client status dictionary
        threading.Thread.__init__(self)

    def run(self):
        rcv = ""
        while True:
            data = self.connection.recv(32)
            if data:
                d = data.decode()
                rcv = rcv + d
                if rcv[-2:] == '\r\n':
                    # end of command, process string
                    logging.warning("data dari client: {}".format(rcv))
                    hasil = json.dumps(chatserver.proses(rcv))
                    hasil = hasil + "\r\n\r\n"
                    logging.warning("balas ke client: {}".format(hasil))
                    self.connection.sendall(hasil.encode())
                    rcv = ""
            else:
                # Client disconnected, set status as offline and break the loop
                self.client_status[self.address] = "offline"
                break
        self.connection.close()



class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.client_status = {}  # Track client status
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(('localhost', 9999))
        self.my_socket.listen(1)
        while True:
            self.connection, self.client_address = self.my_socket.accept()
            logging.warning("connection from {}".format(self.client_address))

            # Set client status as online
            self.client_status[self.client_address] = "online"

            clt = ProcessTheClient(
                self.connection, self.client_address, self.client_status)
            clt.start()
            self.the_clients.append(clt)

def main():
    svr = Server()
    svr.start()


if __name__ == "__main__":
    main()
