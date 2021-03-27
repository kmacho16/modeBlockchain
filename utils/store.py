import shelve
from model.block import Block


class StoreController(object):

    def __init__(self, transactionFile, chainFile, peersFile, peersTransactionsFile):
        self.transactionFile = ("data/%s" % transactionFile)
        self.chainFile = ("data/%s" % chainFile)
        self.peersFile = ("data/%s" % peersFile)
        self.peersTransactionsFile = ("data/%s" % peersTransactionsFile)

    def getTransactionsStored(self):
        transactions = shelve.open(self.transactionFile)
        pendingTransactions = []
        try:
            if 'pending' in transactions:
                pendingTransactions = transactions['pending']
            else:
                pendingTransactions = []
        finally:
            transactions.close()
        return pendingTransactions

    def addTransactionsStored(self, transaction):
        transactions = shelve.open(self.transactionFile)
        try:
            if 'pending' in transactions:
                pendingTransactions = transactions['pending']
            else:
                pendingTransactions = []

            pendingTransactions.append(transaction)
            transactions['pending'] = pendingTransactions
        finally:
            transactions.close()
        return pendingTransactions

    def delTransactionsStored(self):
        transactions = shelve.open(self.transactionFile)
        try:
            if 'pending' in transactions:
                del transactions['pending']
        finally:
            transactions.close()
        return []

    def getBlockChain(self):
        blocks = shelve.open(self.chainFile)
        blockchain = None
        try:
            if 'blocks' in blocks:
                blockchain = blocks['blocks']
            else:
                blockchain = []
        finally:
            blocks.close()
        return blockchain

    def setBlockStored(self, mChain):
        blocks = shelve.open(self.chainFile)
        try:
            blocks['blocks'] = mChain
        finally:
            blocks.close()

    def isBlockSet(self):
        blocks = shelve.open(self.chainFile)
        result = False
        try:
            if 'blocks' in blocks:
                result = True
        finally:
            blocks.close()
        return result

    def getPeersStored(self):
        peers = shelve.open(self.peersFile)
        storedPeers = []
        try:
            if 'peers' in peers:
                storedPeers = peers['peers']
            else:
                storedPeers = []
        finally:
            peers.close()
        return storedPeers

    def addPeersStored(self, mPeer):
        peers = shelve.open(self.peersFile)
        storedPeers = []
        exist = False
        try:
            if 'peers' in peers:
                storedPeers = peers['peers']
            else:
                storedPeers = []
            for element in storedPeers:
                if(element['node_address'] == mPeer['node_address']):
                    exist = True
            if not exist:
                storedPeers.append(mPeer)
                peers['peers'] = storedPeers
        finally:
            peers.close()
        return storedPeers

    def delPeersStored(self):
        peers = shelve.open(self.peersFile)
        try:
            if 'peers' in peers:
                del peers['pending']
        finally:
            peers.close()
        return []

    def getPeersTransactionStored(self):
        peersTransaction = shelve.open(self.peersTransactionsFile)
        storedPeersTransaction = []
        try:
            if 'peersTransaction' in peersTransaction:
                storedPeersTransaction = peersTransaction['peersTransaction']
            else:
                storedPeersTransaction = []
        finally:
            peersTransaction.close()
        return storedPeersTransaction

    def addPeersTransactionStored(self, mPeer):
        peersTransaction = shelve.open(self.peersTransactionsFile)
        storedPeersTransaction = []
        exist = False
        try:
            if 'peersTransaction' in peersTransaction:
                storedPeersTransaction = peersTransaction['peersTransaction']
            else:
                storedPeersTransaction = []
            for element in storedPeersTransaction:
                if(element['node_address'] == mPeer['node_address']):
                    exist = True
            if not exist:
                storedPeersTransaction.append(mPeer)
                peersTransaction['peersTransaction'] = storedPeersTransaction
        finally:
            peersTransaction.close()
        return storedPeersTransaction

    def delPeersTransactionStored(self):
        peersTransaction = shelve.open(self.peersTransactionsFile)
        try:
            if 'peersTransaction' in peersTransaction:
                del peersTransaction['peersTransaction']
        finally:
            peersTransaction.close()
        return []
