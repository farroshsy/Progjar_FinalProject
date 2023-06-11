import json

def sendstring(sock, string):
    try:
        sock.sendall(string.encode())
        receivemsg = ""
        while True:
            data = sock.recv(64)
            print("diterima dari server", data)
            if data:
                # data harus didecode agar dapat dioperasikan dalam bentuk string
                receivemsg = "{}{}".format(receivemsg, data.decode())
                if receivemsg[-4:] == '\r\n\r\n':
                    print("end of string")
                    return json.loads(receivemsg)
    except Exception as e:
        sock.close()
        return {'status': 'ERROR', 'message': 'Gagal'}

if __name__ == "__main__":
    sock = None
    string = ""

    result = sendstring(sock, string)
    print(result)
