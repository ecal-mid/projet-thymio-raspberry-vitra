import socket
import threading
import SocketServer
import time


ip, port = "10.11.11.35", 4500


def client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    try:
        sock.sendall(message)
        response = sock.recv(1024)
        print "Received: {}".format(response)
    finally:
        sock.close()


client(ip, port, "STOP\r")
