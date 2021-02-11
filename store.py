import shelve
from block import Block


class StoreController(object):

    def __init__(self, transactionFile, chainFile, peersFile):
        self.transactionFile = transactionFile
        self.chainFile = chainFile
        self.peersFile = peersFile

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
