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
        response = sendCommand(clientSocket, "LIST")
        print(response)

        if response.startswith('150') or response.startswith('125'):
            payload = ""
            while True:
                chunk = dataSocket.recv(4096).decode("utf-8")
                if not chunk:
                    break
                payload += chunk

            print(payload)
            dataSocket.close()

            finalResponse = receiveData(clientSocket)
            print(finalResponse)
            return True
        else:
            print("Failed to list files")
            dataSocket.close()
            return False
    else:
        print("Failed to establish data connection")
        if dataSocket:
            dataSocket.close()
        return False

def changeDirectory(clientSocket, directory):
    response = sendCommand(clientSocket, f"CWD {directory}")
    print(response)
    return response

def getFiles(clientSocket, fileName):
    pasvStatus, dataSocket = modePASV(clientSocket)

    if pasvStatus == 227:
        response = sendCommand(clientSocket, f"RETR {fileName}")
        print(response)

        if response.startswith('150') or response.startswith('125'):
            bytes_count = 0
            with open(fileName, "wb") as f:
                while True:
                    chunk = dataSocket.recv(4096)
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_count += len(chunk)

            dataSocket.close()

            finalResponse = receiveData(clientSocket)
            print(finalResponse)
            print(f"Success: {bytes_count} bytes transferred.")
            return True
        else:
            print("Failed to get file")
            dataSocket.close()
            return False
    else:
        print("Failed to establish data connection")
        if dataSocket:
            dataSocket.close()
        return False

def putFiles(clientSocket, fileName):
    try:
        with open(fileName, "rb") as f:
            file_content = f.read()
    except FileNotFoundError:
        print("Local file not found.")
        return False

    pasvStatus, dataSocket = modePASV(clientSocket)

    if pasvStatus == 227:
        response = sendCommand(clientSocket, f"STOR {fileName}")
        print(response)

        if response.startswith('150') or response.startswith('125'):
            dataSocket.sendall(file_content)
            dataSocket.close()

            finalResponse = receiveData(clientSocket)
            print(finalResponse)
            print(f"Success: {len(file_content)} bytes transferred.")
            return True
        else:
            print("Failed to put file")
            dataSocket.close()
            return False
    else:
        print("Failed to establish data connection")
        if dataSocket:
            dataSocket.close()
        return False


def deleteFiles(clientSocket, fileName):
    response = sendCommand(clientSocket, f"DELE {fileName}")
    print(response)
    return response




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
                quitFunction(clientSocket)
                break

            elif action == "ls":
                listFiles(clientSocket)

            elif action == "cd":
                if arg:
                    changeDirectory(clientSocket, arg)
                else:
                    print("Usage: cd <directory>")

            elif action == "delete":
                if arg:
                    deleteFiles(clientSocket, arg)
                else:
                    print("Usage: delete <filename>")

            elif action == "get":
                if arg:
                    getFiles(clientSocket, arg)
                else:
                    print("Usage: get <filename>")

            elif action == "put":
                if arg:
                    putFiles(clientSocket, arg)
                else:
                    print("Usage: put <filename>")

    print("Disconnecting...")
    clientSocket.close()

if __name__ == "__main__":
    main()