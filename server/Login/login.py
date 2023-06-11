import uuid

def autentikasi_user(users, sessions, connectedUsers, username, password):
    if username not in users:
        return {'status': 'ERROR', 'message': 'User Tidak Ada'}
    if users[username]['password'] != password:
        return {'status': 'ERROR', 'message': 'Password Salah'}
    tokenid = str(uuid.uuid4())
    sessions[tokenid] = {'username': username, 'userdetail': users[username]}
    connectedUsers[username] = True
    return {'status': 'OK', 'tokenid': tokenid}

if __name__ == "__main__":
    users = {}  
    sessions = {}  
    connectedUsers = {}  
    username = ""  
    password = ""  

    result = autentikasi_user(users, sessions, connectedUsers, username, password)
    print(result)
