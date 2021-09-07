import socket
from threading import Thread
from scripts.network import Network, Packet
from copy import deepcopy

class Server:
    def __init__(self, server, port):

        self.SERVER = server
        self.PORT = port
        self.CLIENTS = {}
        self.IDLE_CLIENTS = {}
        self.connection_id = 0

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.start()

    def start(self):
        try:
            self.socket.bind((self.SERVER, self.PORT))
        except socket.error as e:
            print(e)

        self.socket.listen(10)
        print('Waiting for a connection, Server Started')
        while True:
            conn, addr = self.socket.accept()
            self.connection_id += 1
            print('Connected to:', addr)
            thread = Thread(target=self.threaded_client, args=(conn,))
            thread.start()

    def threaded_client(self, connection):
        # create a network object with the connection and add to client list
        network = Network(self.SERVER, self.PORT, is_client=False, connection=connection, connection_id=self.connection_id)
        self.CLIENTS[self.connection_id] = network
        is_connected = True
        while is_connected:
            is_connected = network.is_connected  # when the connection ends, break the loop
            self.handle_incoming_data(network.recv_data, network)
            self.clear_data_list(network.recv_data)
        self.CLIENTS.pop(self.connection_id)  # remove the client from the clients list and exit the function

    def handle_incoming_data(self, data_packet_list, client_network):
        # find all unread data packets and add them to a list
        unread_data_packet_list = [packet for packet in data_packet_list if not packet.is_read]
        data_list = [(packet.id, packet.get_data()) for packet in unread_data_packet_list]  # get a list of the data not the packets
        # look for server and table commands and handle appropriately
        for data in data_packet_list:
            if type(data.data).__name__  == 'str':  # only continue checking data if it is type string
                parsed_data = data.data.split(' ')
                if parsed_data[0] == 'ServerCMD':
                    self.handle_server_cmd(parsed_data[1], client_network)
                elif parsed_data[0] == 'TableCMD':
                    self.handle_table_cmd(parsed_data[1], client_network)

    def clear_data_list(self, data_packet_list):
        # create a list of unread packets then replace the current data packet list
        new_list = filter(lambda packet: not packet.is_read, data_packet_list)
        data_packet_list = new_list

    def handle_server_cmd(self, command, client_network):
        if command == 'Disconnect':
            client_network.disconnect()

    def handle_table_cmd(self, command, client_network):
        pass


def print_periodically(network):
    import time
    while True:
        time.sleep(11)
        print('sending: instructions from server')
        network.send('instructions from server')

s = Server('192.168.1.139', 5555)
s.start()

