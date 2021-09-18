"""
This file will contain a table_server class which inherits from server, and overwrites a few functions to deal
with assigning multiple game clients to a table object, and passing information back and forth between that table object
"""


from scripts.network.network import Network
from scripts.server.server import Server
from threading import Thread

class Table_Server(Server):
    def __init__(self, ip, port, max_table_size=4, min_table_size=2):
        super().__init__(ip, port)
        # add parameters needed to use table functionality
        self.max_table_size = max_table_size
        self.min_table_size = min_table_size
        self.tables = {}
        self.is_assigning_tables = True
        # start two new threads to deal with the table assigning and removing
        table_assignment_thread = Thread(target=self.assign_tables)
        table_assignment_thread.start()
        idle_table_thread = Thread(target=self.remove_idle_tables)
        idle_table_thread.start()
        # overwrite functions that need to be changed
        self.threaded_client = self.table_threaded_client
        self.stop = self.new_stop

    def new_stop(self):
        self.running = False
        self.is_assigning_tables = False  # this line is the only change to this method from the original
        for client in self.clients:
            client.disconnect()
        self.log('Server Stopped')

    def table_threaded_client(self, connection):  # this method needs to use a Table_Network instead of regular network
        # create a network object with the connection and add to client list
        network = Table_Network(self.ip, self.port, is_client=False,
                                connection=connection, connection_id=self.connection_id)
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

    def assign_tables(self):
        while self.is_assigning_tables:
            # Copy the clients dictionary so that mutating by the other threads wont throw an error during iteration
            client_network_dic = self.clients.copy()
            table_client_list = []
            for client_id, client_net in client_network_dic.items():
                if client_net.assigned_to_table:
                    continue  # This client is already assigned to a table skip this iteration
                elif len(table_client_list) < self.max_table_size:
                    table_client_list.append(client_net)  # Add this unassigned client to the table client list
                    if len(table_client_list) == self.max_table_size:
                        self.create_table(table_client_list)  # The table is full, create a table object
                        table_client_list = []  # Reset the list
            # After all clients have been iterated over, if the min amt of people are in the list create a table anyway
            if len(table_client_list) >= self.min_table_size:
                self.create_table(table_client_list)

    def create_table(self, client_list):
        pass

    def remove_idle_tables(self):
        pass


class Table_Network(Network):
    def __init__(self, ip, port, is_client=True, connection=None, connection_id=None):
        super().__init__(ip, port, is_client=is_client, connection=connection, connection_id=connection_id)
        self.assigned_to_table = False
        self.table_id = None
