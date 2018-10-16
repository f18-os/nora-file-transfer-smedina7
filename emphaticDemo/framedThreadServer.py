#! /usr/bin/env python3
import sys, os, socket, params, time
from threading import Thread
from framedSock import FramedStreamSock

switchesVarDefaults = (
    (('-l', '--listenPort'), 'listenPort', 50001),
    (('-d', '--debug'), "debug", False),  # boolean (set if present)
    (('-?', '--usage'), "usage", False),  # boolean (set if present)
)

progname = "echoserver"
paramMap = params.parseParams(switchesVarDefaults)

debug, listenPort = paramMap['debug'], paramMap['listenPort']

if paramMap['usage']:
    params.usage()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # listener socket
bindAddr = ("127.0.0.1", listenPort)
lsock.bind(bindAddr)
lsock.listen(5)
print("listening on:", bindAddr)


class ServerThread(Thread):
    requestCount = 0  # one instance / class

    def __init__(self, sock, debug):
        Thread.__init__(self, daemon=True)
        self.fsock, self.debug = FramedStreamSock(sock, debug), debug
        self.start()

    def run(self):
        while True:
            lock.acquire(True, -1)
            msg = self.fsock.receivemsg()
            if not msg:
                if self.debug: print(self.fsock, "server thread done")
                return
            requestNum = ServerThread.requestCount
            time.sleep(0.001)
            ServerThread.requestCount = requestNum + 1

            # verify if the file exists already
            # first var will be the name of the file

            file_n = self.fsock.receivemsg()

            if os.path.exists(file_n):
                print("ERROR File already exists.. Exiting.")
                self.fsock.sendmsg(b"ERROR File already exists... Exiting.")
                sys.exit(1)

            rd = ("Ready (%d)" % (requestNum)).encode
            self.fsock.sendmsg(rd)

            # create/open file
            f = open(file_n, "wb")

            # save the rest of the messages in a new variable
            file = self.fsock.receivemsg()

            print("Copying..." + msg.decode())

            f.write(file)

            file = ("%s! (%d)" % (file, requestNum)).encode()
            self.fsock.sendmsg(file)
            lock.release()


while True:
    sock, addr = lsock.accept()
    ServerThread(sock, debug)
