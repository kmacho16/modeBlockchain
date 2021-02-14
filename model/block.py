import json
from hashlib import sha256


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previousHash = previous_hash

    def computedHash(self):
        blockString = json.dumps(self.__dict__, sort_keys=True)
        return sha256(blockString.encode()).hexdigest()
