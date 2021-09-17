import socket
from threading import Thread
from scripts.network.network import Network
import datetime
import os


class Server:
    def __init__(self, server, port):

        self.ip = server
        self.port = port
        self.clients = {}
        self.idle_clients = {}
        self.tables = {}
        self.connection_id = 0
        self.running = False

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        try:
            self.socket.bind((self.ip, self.port))
        except socket.error as e:
            self.log(e)

        self.socket.listen(10)
        self.log('Waiting for a connection, Server Started')
        idle_thread = Thread(target=self.remove_timed_out_clients)
        idle_thread.start()
        self. running = True

        while self.running:
            conn, addr = self.socket.accept()
            self.connection_id += 1
            self.log('Connected to: ' + str(addr) + '    Client ID: ' + str(self.connection_id))
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
            self.update_data_list(network)
        if not network.full_disconnect:  # if this was not an intentional disconnect, handle as a soft disconnect
            self.log('Client %i soft disconnected from server' % network.id)
            self.idle_clients[network.id] = network  # soft disconnect means add to idle_clients remove from clients
            self.clients.pop(network.id)
            network.start_idle_timer(300)

    def handle_incoming_data(self, data_packet_list, client_network):
        # find all unread data packets and add them to a list
        unread_data_packet_list = [packet for packet in data_packet_list if not packet.is_read]
        data_list = [(packet.id, packet.get_data(), packet.data_type) for packet in unread_data_packet_list]
        # look for server and table commands and handle appropriately
        for data in data_list:
            self.log('Client Id %i sent a packet of type %s to the server' % (client_network.id, data[2]))
            if data[2] != 'ServerCMD':
                self.handle_other_data_types(data, client_network)
            elif data[2] == 'ServerCMD':
                self.handle_server_cmd(data[1].split(' '), client_network)

    def handle_other_data_types(self, data, client_net):
        pass  # this function is meant to be overwritten since its specific to the type of game running on the server

    def update_data_list(self, client_network):
        # create a list of unread packets then replace the current data packet list
        new_list = list(filter(lambda packet: not packet.is_read, client_network.recv_data))
        client_network.recv_data = new_list

    def handle_server_cmd(self, command, client_network):
        if command[0] == 'Disconnect':
            self.clients.pop(client_network.id)
            client_network.disconnect()
        elif command[0] == 'SoftDisconnect':
            client_network.soft_disconnect()
        elif command[0] == 'Reconnect':
            try:
                old_id = int(command[1])
                self.log('Attempting to reconnect to id %i' % old_id)
                old_net = self.idle_clients[old_id]
                client_network.reconnect(old_net)  # change the new network parameters to the old ones server side
                self.clients[old_id] = client_network
                self.idle_clients.pop(old_id)  # remove from idle list and add to client list
            except socket.error as e:
                self.log('Error attempting to reconnect to client id %i' % int(command[2]))
                self.log(e)
        else:
            self.handle_additional_server_commands(command, client_network)

    def handle_additional_server_commands(self, command, client_network):
        pass

    def remove_timed_out_clients(self):
        while self.running:
            remove_id_list = []
            items_list = self.idle_clients.items()
            for client_id, client in items_list:
                if client.timed_out:
                    remove_id_list.append(client_id)
            for item in remove_id_list:
                self.idle_clients.pop(item)
                self.log('Client id %i timed out and is no longer idle' % item)

    def stop(self):
        self.running = False
        for client in self.clients:
            client.disconnect()
        self.log('Server Stopped')

    def log(self, comment_to_log):
        print(comment_to_log)
        log_thread = Thread(target=self.add_to_log_file, args=(comment_to_log,))
        log_thread.start()

    def add_to_log_file(self, comment):
        path = os.getcwd() +'\\logs\\'
        # get the current date and time
        d_t = datetime.datetime.now()
        filename = 'server_log_' + str(d_t.date()) + '.txt'
        # if this logfile already exists, then open it in append mode, otherwise create with write mode
        if os.path.exists(path + filename):
            file = open(path + filename, 'a')
        else:
            file = open(path + filename, 'w')
        line_to_write = str(d_t.time()) + ': ' + comment + '\n'
        file.write(line_to_write)
        file.close()
