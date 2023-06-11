# Dokumentasi Protokol

## Daftar Protokol
1. [Auth - Login User](#auth---login-user)
2. [Private Messaging](#private-messaging)
3. [Group Messaging](#group-messaging)
4. [Private Send/Receive File](#private-sendreceive-file)
5. [Group Send/Receive File](#group-sendreceive-file)
6. [Inbox](#inbox)
7. [Real-time Online/Offline Status](#real-time-onlineoffline-status)
8. [Delete Last Message](#delete-last-message)
9. [Forward Message](#forward-message)
10. [Reply Message](#reply-message)

## Satu Server

### Auth - Login User

#### Command
```
AUTH <username> <password>
```
#### Example
```
AUTH messi surabaya
```
#### Result
```
#Jika otentikasi berhasil
AUTH_SUCCESS <user_id>

#Jika otentikasi gagal
AUTH_FAIL <error_message>
```

### Private Messaging

#### Command
```
SEND <username_dest> <message>
```
#### Example
```
SEND messi apa kabar si
```

### Group Messaging

#### Command
```
SENDGROUP <username_dest 1>, <username_dest 2>, ... , <username_dest (n)> <message>
```
#### Example
```
SENDGROUP messi, henderson, lineker apa kabar rekk
```

### Private Send/Receive File

#### Command
```
SENDFILE <username_dest 1> <file_path>
```
#### Example
```
SENDFILE messi gambar.jpg
```

### Group Send/Receive File

#### Command
```
SENDGROUPFILE <username_dest 1>, <username_dest 2>, ... , <username_dest (n)> <file_path>
```
#### Example
```
SENDGROUPFILE messi, henderson, lineker gambar.jpg
```

### Inbox

#### Command
```
INBOX
```
#### Example
```
INBOX
```

### Real-time Online/Offline Status

#### Command
```
GETPRESENCE <username_dest>
```
#### Example
```
GETPRESENCE messi
```
#### Result
```
#Jika berhasil
PRESENCE_STATUS <username> <online_status>
```

### Delete Last Message

#### Command
```
DELETELASTMESSAGE
```
#### Example
```
DELETELASTMESSAGE
```

### Forward Message - Belum dicoba

#### Command
```
FORWARDMESSAGE <username_dest> <message_id>
```
#### Example
```
FORWARDMESSAGE messi 11062023M

```

### Reply Message - Belum dicoba

#### Command
```
REPLYMESSAGE <message_id> <reply_message>
```
#### Example
```
REPLYMESSAGE 11062023M baik si

```

## Dengan Server lain

### Add Realm

#### Command
```
ADDREALM <realm_name> <ipaddress_dest> <port_dest>
```
#### Example
```
ADDREALM realm2 0.tcp.ap.ngrok.io 18553
```

### Private Messaging

#### Command
```
SENDPRIVATEREALM <realm_name> <username_dest> <message>
```
#### Example
```
SENDPRIVATEREALM realm2 messi haloo
```

### Group Messaging

#### Command
```
SENDGROUPREALM <realm_name> <username_dest 1>, <username_dest 2>, ... , <username_dest (n)> <message>
```
#### Example
```
SENDGROUPREALM realm2 messi, henderson, lineker apa kabar rekk
```

### Private Send/Receive File

#### Command
```
SENDFILEREALM <realm_name> <username_dest 1> <file_path>
```
#### Example
```
SENDFILEREALM realm2 messi gambar2.jpg
```

### Group Send/Receive File

#### Command
```
SENDGROUPFILE <realm_name> <username_dest 1>, <username_dest 2>, ... , <username_dest (n)> <file_path>
```
#### Example
```
SENDGROUPFILE realm2 messi, henderson, lineker gambar2.jpg
```

### Inbox

#### Command
```
GETREALMINBOX <realm_name>
```
#### Example
```
GETREALMINBOX realm2
```
