
import requests


class Peer:
    def __init__(self, name, address):
        self.name = name
        self.address = address

    def getPeers(self):
        response = requests.get(self.address + "/peers")
        if response.status_code == 200:
            peers = response.json()['peers']
            return peers
        else:
            return response.content, response.status_code
