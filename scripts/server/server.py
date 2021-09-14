import socket
from threading import Thread
from scripts.network.network import Network


class Server:
    def __init__(self, server, port):

        self.ip = server
        self.port = port
        self.clients = {}
        self.idle_clients = {}
        self.tables = {}
        self.connection_id = 0

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.start()

    def start(self):
        try:
            self.socket.bind((self.ip, self.port))
        except socket.error as e:
            print(e)

        self.socket.listen(10)
        print('Waiting for a connection, Server Started')
        idle_thread = Thread(target=self.remove_timed_out_clients)
        idle_thread.start()
        
        while True:
            conn, addr = self.socket.accept()
            self.connection_id += 1
            print('Connected to:', addr)
            thread = Thread(target=self.threaded_client, args=(conn,))
            thread.start()

    def threaded_client(self, connection):
        # create a network object with the connection and add to client list
        network = Network(self.ip, self.port, is_client=False, connection=connection, connection_id=self.connection_id)
        self.clients[self.connection_id] = network
        is_connected = True
        while is_connected:
            is_connected = network.is_connected  # when the connection ends, break the loop
            self.handle_incoming_data(network.recv_data, network)
            self.clear_data_list(network.recv_data)
        if not network.full_disconnect:  # if this was not an intentional disconnect, handle as a soft disconnect
            self.idle_clients[network.id] = network  # soft disconnect means add to idle_clients remove from clients
            self.clients.pop(network.id)
            network.start_idle_timer(300)
            print('Client %i soft disconnected from server' % network.id)

    def handle_incoming_data(self, data_packet_list, client_network):
        # find all unread data packets and add them to a list
        unread_data_packet_list = [packet for packet in data_packet_list if not packet.is_read]
        data_list = [(packet.id, packet.get_data()) for packet in unread_data_packet_list]  # get a list of the data
        # look for server and table commands and handle appropriately
        if data_list != []:
            print('Data received')
        for data in data_list:
            print('Client Id %i sent a packet to the server' % client_network.id)
            if type(data[1]).__name__ == 'str':  # only continue checking data if it is type string

                parsed_data = data[1].split(' ')
                if parsed_data[0] == 'ServerCMD':
                    print('Server command  %s received from connection ID %i' % (parsed_data[1], client_network.id))
                    self.handle_server_cmd(parsed_data, client_network)
                elif parsed_data[0] == 'TableCMD':
                    self.handle_table_cmd(parsed_data, client_network)

    def clear_data_list(self, data_packet_list):
        # create a list of unread packets then replace the current data packet list
        new_list = filter(lambda packet: not packet.is_read, data_packet_list)
        data_packet_list = new_list

    def handle_server_cmd(self, command, client_network):
        if command[1] == 'Disconnect':
            self.clients.pop(client_network.id)
            client_network.disconnect()
        if command[1] == 'SoftDisconnect':
            client_network.soft_disconnect()
        if command[1] == 'Reconnect':
            try:
                old_id = int(command[2])
                print('Attempting to reconnect to id %i' % old_id)
                old_net = self.idle_clients[old_id]
                client_network.reconnect(old_net)  # change the new network parameters to the old ones server side
                self.clients[old_id] = client_network
                self.idle_clients.pop(old_id)  # remove from idle list and add to client list
            except socket.error as e:
                print('Error attempting to reconnect to client id %i' % int(command[2]))
                print(e)

    def handle_table_cmd(self, command, client_network):
        pass

    def remove_timed_out_clients(self):
        while True:
            for client_id, client in self.idle_clients.items():
                if client.timed_out:
                    self.idle_clients.pop(client_id)
