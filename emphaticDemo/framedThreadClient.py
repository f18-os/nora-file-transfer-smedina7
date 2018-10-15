#! /usr/bin/env python3

# Echo client program
import os
import socket, sys, re
import params
from framedSock import FramedStreamSock
from threading import Thread
import time

switchesVarDefaults = (
    (('-s', '--server'), 'server', "localhost:50001"),
    (('-d', '--debug'), "debug", False),  # boolean (set if present)
    (('-?', '--usage'), "usage", False),  # boolean (set if present)
)

progname = "framedClient"
paramMap = params.parseParams(switchesVarDefaults)

server, usage, debug = paramMap["server"], paramMap["usage"], paramMap["debug"]

if usage:
    params.usage()

try:
    serverHost, serverPort = re.split(":", server)
    serverPort = int(serverPort)
except:
    print("Can't parse server:port from '%s'" % server)
    sys.exit(1)


class ClientThread(Thread):
    def __init__(self, serverHost, serverPort, debug):
        Thread.__init__(self, daemon=False)
        self.serverHost, self.serverPort, self.debug = serverHost, serverPort, debug
        self.start()

    def run(self):
        s = None
        for res in socket.getaddrinfo(serverHost, serverPort, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                print("creating sock: af=%d, type=%d, proto=%d" % (af, socktype, proto))
                s = socket.socket(af, socktype, proto)
            except socket.error as msg:
                print(" error: %s" % msg)
                s = None
                continue
            try:
                print(" attempting to connect to %s" % repr(sa))
                s.connect(sa)
            except socket.error as msg:
                print(" error: %s" % msg)
                s.close()
                s = None
                continue
            break

        if s is None:
            print('could not open socket')
            sys.exit(1)

        client_file = input("What file do you want to send:\n")

        if not os.path.exists(client_file):
            print("File %s doesn't exist! Exiting" % client_file)
            sys.exit(1)

        fs = FramedStreamSock(s, debug=debug)

        # sending name of file first so that server can verify
        print("sendind file: " + client_file)
        fs.sendmsg(client_file)

        # if file exits..
        if fs.receivemsg() == b"ERROR File already exists... Exiting.":
            print(fs.receivemsg())
            sys.exit(1)  # exit

        # #if server says it's ready
        if fs.receivemsg() == b"Ready":
            print("Sending...")

        f = open(client_file, "rb")
        byte = f.read(100)
        while byte:
            fs.sendmsg(byte)
            print("Sending copy of...", fs.receivemsg())
            byte = f.read(100)


for i in range(100):
    ClientThread(serverHost, serverPort, debug)
