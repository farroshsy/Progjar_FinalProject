def register_user(username, password, name, country, tokenid, sendstring):
    # Code for user registration
    if tokenid != "":
        return "Error, already logged in"
    
    string = "register {} {} {} {} \r\n".format(username, password, name, country)
    result = sendstring(string)
    if result['status'] == 'OK':
        return "User registered successfully"
    else:
        return "Error, {}".format(result['message'])

if __name__ == "__main__":
    tokenid = ""
    sendstring = lambda x: None
    username = ""
    password = ""
    name = ""
    country = ""

    result = register_user(username, password, name, country, tokenid, sendstring)
    print(result)