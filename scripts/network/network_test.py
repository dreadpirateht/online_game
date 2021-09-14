import socket
from scripts.network.network import Network, Packet
from time import sleep

ip = socket.gethostbyname(socket.gethostname())
n = Network(ip, 5555)
while True:
    cmd = input('Command to send to server: ')
    n.send(cmd)
    sleep(2)
