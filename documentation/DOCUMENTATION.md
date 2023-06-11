# DOCUMENTATION

Documentation by Kelompok 2.
<br />

## <b>Table of Contents</b>

<hr />

### Satu Server

1. [REGISTER - Register User](#register---register-user)
2. [AUTH - Login User](#auth---login-user)
3. [SEND - Private Messaging](#private-messaging)
4. [SENDGROUP - Group Messaging](#sendgroup---group-messaging)
5. [SENDFILE - Private Send/Receive File](#sendfile---private-sendreceive-file)
6. [SENDGROUPFILE - Group Send/Receive File](#sendgroupfile---group-sendreceive-file)
7. [INBOX - Receive Messages](#inbox---receive-messages)
8. [GETPRESENCE - Real-time Online/Offline Status](#getpresence---real-time-onlineoffline-status)
9. [DELETE - Delete Last Message](#delete---delete-last-message)
10. [FORWARD - Forward Message](#forwardmessage---forward-message-belum-dicoba)
11. [REPLYMESSAGE - Reply Message](#replymessage---reply-message-belum-dicoba)

### Antar Server

1. [ADDREALM - Realm Connection](#addrealm---realm-connection)
2. [SENDPRIVATEREALM - Private Messaging](#sendprivaterealm---private-messaging)
3. [SENDGROUPREALM - Group Messaging](#sendgrouprealm---group-messaging)
4. [SENDFILEREALM - Private Send/Receive File](#sendfilerealm---private-sendreceive-file)
5. [SENDGROUPFILE - Group Send/Receive File](#sendgroupfile---group-sendreceive-file-1)

<br />

## <b>Satu Server</b>

<hr />

### `REGISTER` - Register User

Digunakan untuk mendaftarkan user baru.

#### Command

```
REGISTER <username> <password> <name> <country>
```

#### Example

```
REGISTER titus 12345678 Titus Testing Indonesia
```

#### Result

```
#Jika registrasi berhasil
User registered successfully

#Jika registrasi gagal
<error_message>
```

<br />

### `AUTH` - Login User

Digunakan untuk melakukan login user agar dapat melakukan komunikasi.

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

<br />

### `SEND` - Private Messaging

#### Command

```
SEND <username_dest> <message>
```

#### Example

```
SEND messi apa kabar si
```

<br />

### `SENDGROUP` - Group Messaging

#### Command

```
SENDGROUP <username_dest 1>, <username_dest 2>, ... , <username_dest (n)> <message>
```

#### Example

```
SENDGROUP messi, henderson, lineker apa kabar rekk
```

<br />

### `SENDFILE` - Private Send/Receive File

#### Command

```
SENDFILE <username_dest 1> <file_path>
```

#### Example

```
SENDFILE messi gambar.jpg
```

<br />

### `SENDGROUPFILE` - Group Send/Receive File

#### Command

```
SENDGROUPFILE <username_dest 1>, <username_dest 2>, ... , <username_dest (n)> <file_path>
```

#### Example

```
SENDGROUPFILE messi, henderson, lineker gambar.jpg
```

<br />

### `INBOX` - Receive Messages

#### Command

```
INBOX
```

#### Example

```
INBOX
```

<br />

### `GETPRESENCE` - Real-time Online/Offline Status

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

<br />

### `DELETE` - Delete Last Message

#### Command

```
DELETELASTMESSAGE
```

#### Example

```
DELETELASTMESSAGE
```

<br />

### `FORWARDMESSAGE` - Forward Message (Belum Dicoba)

#### Command

```
FORWARDMESSAGE <username_dest> <message_id>
```

#### Example

```
FORWARDMESSAGE messi 11062023M

```

<br />

### `REPLYMESSAGE` - Reply Message (Belum Dicoba)

#### Command

```
REPLYMESSAGE <message_id> <reply_message>
```

#### Example

```
REPLYMESSAGE 11062023M baik si

```

<br />

## <b>Antar Server</b>

<hr />

### `ADDREALM` - Realm Connection

#### Command

```
ADDREALM <realm_name> <ipaddress_dest> <port_dest>
```

#### Example

```
ADDREALM realm2 0.tcp.ap.ngrok.io 18553
```

<br />

### `SENDPRIVATEREALM` - Private Messaging

#### Command

```
SENDPRIVATEREALM <realm_name> <username_dest> <message>
```

#### Example

```
SENDPRIVATEREALM realm2 messi haloo
```

<br />

### `SENDGROUPREALM` - Group Messaging

#### Command

```
SENDGROUPREALM <realm_name> <username_dest 1>, <username_dest 2>, ... , <username_dest (n)> <message>
```

#### Example

```
SENDGROUPREALM realm2 messi, henderson, lineker apa kabar rekk
```

<br />

### `SENDFILEREALM` - Private Send/Receive File

#### Command

```
SENDFILEREALM <realm_name> <username_dest 1> <file_path>
```

#### Example

```
SENDFILEREALM realm2 messi gambar2.jpg
```

<br />

### `SENDGROUPFILE` - Group Send/Receive File

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