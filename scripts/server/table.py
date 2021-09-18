"""
This file will contain the table class to be used for communicating game info between players and the server
"""


class Table:

    def __init__(self, client_network_list, table_id):
        self.table_id = table_id
        self.client_list = client_network_list
        # Assign each client to a player object


class Player:

    def __init__(self, client_network, player_number):
        self.net = client_network
        self.player_number = player_number
