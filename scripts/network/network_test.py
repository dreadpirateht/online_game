import socket
from scripts.network.network import Network, Packet
from time import sleep

ip = socket.gethostbyname(socket.gethostname())
n = Network(ip, 5555)
while True:
    dat_type = input('Data Type of command to send to server: ')
    data = input('Data to send to server')
    n.send(data, data_type=dat_type)
    sleep(2)
