from hashlib import sha256
import json
import time
import requests
from flask import Flask, jsonify, request
import shelve
from model.block import Block
from utils.store import StoreController
import random
import math
from requests.exceptions import ConnectionError


class Blockchain(StoreController):
    difficulty = 2

    def __init__(self, transactionFile='transactions.ud', chainFile='blocks.ud', peersFile='peers.ud', peersTransactionsFile='peersTransaction.ud'):
        super(Blockchain, self).__init__(
            transactionFile, chainFile, peersFile, peersTransactionsFile)
        self.unconfirmedTransaction = self.getTransactionsStored()
        self.peers = self.getPeersStored()
        self.chain = []
        self.createGenesisBlock()

    def createGenesisBlock(self):
        genesisBlock = Block(0, [], time.time(), "")
        genesisBlock.hash = genesisBlock.computedHash()
        self.chain.append(genesisBlock)
        if (not self.isBlockSet()):
            self.setBlockStored(self.chain)
        else:
            self.chain = self.getBlockChain()

    def proofOfWork(self, block):
        block.nonce = 0
        computedHash = block.computedHash()
        while not computedHash.startswith('0'*Blockchain.difficulty):
            block.nonce += 1
            computedHash = block.computedHash()
        return computedHash

    def addNewTransaction(self, transaction):
        self.sendTransactionToPeers(transaction)
        self.addTransactionsStored(transaction)
        self.unconfirmedTransaction = self.getTransactionsStored()

    def mine(self):
        if not self.unconfirmedTransaction:
            return False
        lastBlock = self.lastBlock

        newBlock = Block(lastBlock.index + 1,
                         self.unconfirmedTransaction,
                         time.time(),
                         lastBlock.hash)
        proof = self.proofOfWork(newBlock)
        self.addBlock(newBlock, proof)
        self.unconfirmedTransaction = self.delTransactionsStored()
        return newBlock.index

    def sendTransactionToPeers(self, transaction):
        self.validatePeersTransactions()
        try:
            for peer in self.getPeersTransactionStored():
                nodeAddress = peer['node_address']
                headers = {'Content-Type': "application/json"}
                requests.post(nodeAddress + "/new_transaction/peer",
                              data=json.dumps(transaction), headers=headers)
        except ConnectionError as e:
            print("ERROR CONECTANDO %s ", e)

    def validatePeersTransactions(self):
        necessaryPeers = int(math.ceil(len(self.getPeersStored()) * 0.51))
        if(necessaryPeers > len(self.getPeersTransactionStored())):
            mContinue = True
            while(mContinue):
                randomPeer = random.choice(self.getPeersStored())
                mContinue = False
                for item in self.getPeersTransactionStored():
                    if(item['node_address'] == randomPeer['node_address']):
                        mContinue = True
            self.addPeersTransactionStored(randomPeer)

    def addBlock(self, block, proof):
        previousHash = self.lastBlock.hash
        if previousHash != block.previousHash:
            return False

        if not self.isValidProof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        self.setBlockStored(self.chain)
        return True

    def isValidProof(self, block, proof):
        return (proof.startswith('0' * Blockchain.difficulty) and
                proof == block.computedHash())

    def uidExist(self, auth):
        record = {'exist': False}
        for element in self.getBlockChain():
            for transaction in element.transactions:
                if not transaction['uid'] is None and 'active' in transaction:
                    if auth['uid'] == transaction['uid']:
                        record = {
                            'exist': True,
                            'active': transaction['active'],
                            'node': element.hash,
                            'transaction': transaction}
        return record

    def validatePendingTransaction(self, auth):
        response = {'exist': False}
        for pending in self.getTransactionsStored():
            if pending['uid'] == auth['uid'] and pending['active']:
                response = {'exist': True, "transaction": pending}
        return response

    @property
    def lastBlock(self):
        return self.chain[-1]

    @property
    def firstBlock(self):
        return self.chain[0]

    def checkChainValidity(self, chain):
        result = True
        previousHash = "0"
        for block in chain:
            blockHash = block.hash
            delattr(block, "hash")
            if not self.isValidProof(block, block.hash) or previousHash != block.previousHash:
                result = False
                break

            block.hash, previousHash = blockHash, blockHash

        return result

        # Initialize flask application
