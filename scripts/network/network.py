"""
This file will house a network class that will make connections between a server and clients
"""

import socket
from threading import Thread
from pickle import dumps, loads
from time import time


class Network:
    def __init__(self, host, port, is_client=True, connection=None, connection_id=None):
        self.HEADER_LENGTH = 128
        self.packet_id = 0
        self.is_client = is_client
        self.full_disconnect = False
        self.timed_out = False
        self.host = host
        self.port = port
        self.connection = connection
        self.id = connection_id
        self.addr = (self.host, self.port)
        # by default, this object is being used by a client
        if self.is_client:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.id = self.connect()
            print('Connection ID:', self.id)
        else:  # this is a server side connection
            self.send(self.id)
        self.recv_data = []
        self.is_connected = True
        self.listening_thread = Thread(target=self.listen, daemon=True)
        self.listening_thread.start()

    def connect(self):
        try:
            self.connection.connect(self.addr)
            return self.recieve().data  # receive the client id
        except socket.error as e:
            print(e)

    def send(self, data):
        try:
            header, enc_data = self.get_encoded_header_and_msg(data)
            self.connection.send(header)
            self.connection.send(enc_data)

        except socket.error as e:
            print(e)

    def recieve(self):
        # first recieve header
        header_len = loads(self.connection.recv(self.HEADER_LENGTH))
        # now recieve the data and return
        return loads(self.connection.recv(header_len))

    def listen(self):
        if self.is_client:
            print('Listening for data')
        while self.is_connected:
            try:
                data = self.recieve()
                self.recv_data.append(data)
                # print(self.recv_data)
            except socket.error as e:  # we are disconnected
                print(e)
                self.is_connected = False
                if self.is_client:
                    print('Disconnected from server')
                else:
                    print('Client id %s disconnected' % self.id)
        self.connection.close()

    def get_encoded_header_and_msg(self, data_to_send):
        # first place data into a packet object
        self.packet_id += 1
        packet = Packet(data_to_send, self.packet_id)
        # next encode the message and then create an encoded header
        enc_msg = dumps(packet)
        msg_len = len(enc_msg)  # integer len of the encoded message
        header = dumps(msg_len)  # the header should be an int of the message length in bytes
        header += b' ' * (self.HEADER_LENGTH - len(header))  # pad the header with blank bytes for the rest of the len
        return header, enc_msg

    def reconnect(self, old_network):
        try:
            print('Attempting to reconnect to server via connection ID:', old_network.id)
            self.id = old_network.id
            self.recv_data = old_network.recv_data
            self.packet_id = old_network.packet_id
            print('Successfully reconnected to server')
        except socket.error as e:
            print('Error Reconnecting to server: ', e)

    def disconnect(self):
        self.is_connected = False
        self.connection.close()
        print('Disconnected from server')

    def soft_disconnect(self):
        self.is_connected = False
        self.connection.close()
        print('Soft Disconnected from server')

    def clear_read_packets(self):
        new_recv_list = []
        for packet in self.recv_data:
            if not packet.is_read:
                new_recv_list.append(packet)
        self.recv_data = new_recv_list

    def start_idle_timer(self, sec_to_be_idle):
        start_time = time()
        while not self.timed_out:
            if time() - start_time > sec_to_be_idle:
                self.timed_out = True


class Packet:
    def __init__(self, data, packet_id):
        self.data = data
        self.id = packet_id
        self.is_read = False

    def get_data(self):
        self.is_read = True
        return self.data

    def __str__(self):
        return 'packet_id: %i, %s' % (self.id, str(self.data))

    def __repr__(self):
        return 'packet_id: %i, %s' % (self.id, str(self.data))


if __name__ == '__main__':
    n = Network('192.168.1.139', 5555)
    import time
    while True:
        print()
        time.sleep(5)
        n.send('sending')
