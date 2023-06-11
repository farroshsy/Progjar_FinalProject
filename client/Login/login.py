from ..SendString.sendString import sendstring

def login(sock, username, password):
    string = "auth {} {} \r\n".format(username, password)
    result = sendstring(sock, string)
    if result['status'] == 'OK':
        tokenid = result['tokenid']
        return "username {} logged in, token {}".format(username, tokenid)
    else:
        return "Error, {}".format(result['message'])

if __name__ == "__main__":
    sendstring = lambda x: None
    username = ""
    password = ""

    result = login(username, password, sendstring)
    print(result)