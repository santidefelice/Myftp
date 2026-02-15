from socket import *
import sys
import re

server2 = "inet.cs.fiu.edu"
#username = "alpha"################      USERNAME
#password = "fishy"###########           PASSWORD
#workingDirectory = ""  #######        CHANGE WORKING DIRECTORY
#remoteDirectoryFile = ""########       LIST
#fileName = "" ##########              FILENAME
#FTPSession = "" ###########          FTP SESSION

#clientSocket = socket(AF_INET, SOCK_STREAM)
#socket.login(username, password)
#socket.bind(server)
#socket.connect(client)


def getSocketInfo():
    hostname = gethostname()
    ip = gethostbyname(hostname)
    print(f'Hostname: {hostname}')
    print(f'IP: {ip}')

def quitFunction(clientSocket):
    command = "quit"
    data = sendCommand(clientSocket, command)
    print(data)

def sendCommand(clientSocket, command):
    full_cmd = command + "\r\n"
    dataOut = full_cmd.encode("utf-8")
    clientSocket.sendall(dataOut)
    data = receiveData(clientSocket)
    return data

def receiveData(clientSocket):
    dataIn = clientSocket.recv(1024)
    data = dataIn.decode("utf-8")
    return data

def modePASV(clientSocket):
    command = "PASV\r\n"
    clientSocket.sendall(command.encode("utf-8"))
    data = receiveData(clientSocket)

    status = 0
    dataSocket = None

    if data.startswith("227"):
        status = 227
        # Parse (h1,h2,h3,h4,p1,p2)
        match = re.search(r'\((\d+,\d+,\d+,\d+,(\d+),(\d+))\)', data)
        if match:
            vals = match.group(1).split(',')
            ip = '.'.join(vals[:4])
            port = (int(vals[4]) << 8) + int(vals[5])

            dataSocket = socket(AF_INET, SOCK_STREAM)
            dataSocket.connect((ip, port))

    return status, dataSocket


def listFiles(clientSocket):
    pasvStatus, dataSocket = modePASV(clientSocket)

    if pasvStatus == 227:

        command = "ls\r\n"
        response = sendCommand(clientSocket, command)
        print(response)

        if response.startswith('150') or response.startswith('125'):
            fileList = b""
            while True:
                chunk =dataSocket.recv(4096)
                if not chunk:
                    break
                fileList += chunk

            print(fileList.decode("utf-8"))
            dataSocket.close()

            finalResponse = receiveData(clientSocket)
            print(finalResponse)
        else:
            print("Failed to list files")
            dataSocket.close()
            return False
    else:
        print("Failed to establish data connection")
        dataSocket.close()
        return False
    return True

def changeDirectory(clientSocket, directory):
    command = f"cd {directory}\r\n"
    response = sendCommand(clientSocket, command)
    print(response)

def getFiles(clientSocket, fileName):
    pasvStatus, dataSocket = modePASV(clientSocket)

    if pasvStatus == 227:
        command = f"get {fileName}\r\n"
        response = sendCommand(clientSocket, command)
        print(response)

        if response.startswith('150') or response.startswith('125'):
            fileData = b""
            while True:
                chunk = dataSocket.recv(4096)
                if not chunk:
                    break
                fileData += chunk

            with open(fileName, "wb") as f:
                f.write(fileData)

            dataSocket.close()

            finalResponse = receiveData(clientSocket)
            print(finalResponse)

        else:
            print("Failed to get file")
            dataSocket.close()
            return False
    else:
        print("Failed to establish data connection")
        dataSocket.close()
        return False
    return True

def putFiles(clientSocket, fileName):
    with open(fileName, "rb") as f:
        fileData = f.read()


    pasvStatus, dataSocket = modePASV(clientSocket)

    if pasvStatus == 227:
        command = f"put {fileName}\r\n"
        response = sendCommand(clientSocket, command)
        print(response)

        if response.startswith('150') or response.startswith('125'):
            dataSocket.sendall(fileData)
            dataSocket.close()


            finalResponse = receiveData(clientSocket)
            print(finalResponse)
        else:
            print("Failed to put file")
            dataSocket.close()
            return False
    else:
        print("Failed to establish data connection")
        dataSocket.close()


def deleteFiles(clientSocket, fileName):
    command = f"delete {fileName}\r\n"
    response = sendCommand(clientSocket, command)
    print(response)




def main():

    getSocketInfo()
    if len(sys.argv) < 2:
        print("Usage: python myftp.py <server-name>")
        return

    HOST = sys.argv[1]
    clientSocket = socket(AF_INET, SOCK_STREAM)

    try:
        clientSocket.connect((HOST, 21))
    except Exception as e:
        print(f"Failed to connect to {HOST}: {e}")
        return

    dataIn = receiveData(clientSocket)
    #dataIn = clientSocket.recv(1024)
    print(dataIn)

    status = 0
    if dataIn.startswith("220"):
        status = 220
        username = input("Username: ")
        dataIn = sendCommand(clientSocket, f"USER {username}")
        print(dataIn)
        if dataIn.startswith("331"):
            status = 331
            pw = input("Password: ")
            dataIn = sendCommand(clientSocket, f"PASS {pw}")
            print(dataIn)
            if dataIn.startswith("230"):
                status = 230

    if status == 230:
        while True:
            cmd_input = input("myftp>").strip().split(maxsplit=1)
            if not cmd_input: continue

            action = cmd_input[0].lower()
            arg = cmd_input[1] if len(cmd_input) > 1 else ""

            if action == "quit":
                quitFTP(clientSocket)
                break

            elif action == "ls":
                p_status, dataSock = modePASV(clientSocket)
                if p_status == 227:
                    print(sendCommand(clientSocket, "LIST"))
                    payload = ""
                    while True:
                        chunk = dataSock.recv(4096).decode("utf-8")
                        if not chunk: break
                        payload += chunk
                    dataSock.close()
                    print(payload)
                    print(receiveData(clientSocket))

            elif action == "cd":
                print(sendCommand(clientSocket, f"CWD {arg}"))

            elif action == "delete":
                print(sendCommand(clientSocket, f"DELE {arg}"))

            elif action in ["get", "put"]:
                p_status, dataSock = modePASV(clientSocket)
                if p_status == 227:
                    if action == "get":
                        print(sendCommand(clientSocket, f"RETR {arg}"))
                        with open(arg, "wb") as f:
                            bytes_count = 0
                            while True:
                                chunk = dataSock.recv(4096)
                                if not chunk: break
                                f.write(chunk)
                                bytes_count += len(chunk)
                    dataSock.close()
                    print(receiveData(clientSocket))
                    print(f"Success: {bytes_count} bytes transferred.")
                else:  # put
                    try:
                        with open(arg, "rb") as f:
                            file_content = f.read()
                        print(sendCommand(clientSocket, f"STOR {arg}"))
                        dataSock.sendall(file_content)
                        dataSock.close()
                        print(receiveData(clientSocket))
                        print(f"Success: {len(file_content)} bytes transferred.")
                    except FileNotFoundError:
                        print("Local file not found.")
                        dataSock.close()

    print("Disconnecting...")
    clientSocket.close()

#def printFunc():
#    print(f"file {fileName}")

"""

retrieveFilename()
printFunc()
print(f"file {fileName}")

print("File Name: " + fileName)

s


list = ["picture.jpg", "list.img", "note.pnyb"]

print("print")

print("\n")
print(list)
print(list[2])
word = ""
##for (i = 0; i < 3; i++){
##    word +1 list[i]
##}

for x in range(len(list)):
    word += list[x]

print(word)

print("Username: " + username)
print("Password: " + password)
print("Server: " + server)
newServer = ""
newUsername = ""
newPassword = ""

input("New server:" + newServer)
input("username:" + newUsername)
input("password" + password)

changeWorkingDirectory()
retrieveFilename()
storeFilename()
deleteFilename()
quitFunction()
"""
if __name__ == "__main__":
    main()