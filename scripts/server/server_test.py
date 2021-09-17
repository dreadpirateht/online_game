"""
This file will contain a function meant to create a server object on my work laptop
"""
from scripts.server.server import Server
import socket

ip = socket.gethostbyname(socket.gethostname())

server = Server(ip, 5555)
server.start()
