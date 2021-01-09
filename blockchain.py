from hashlib import sha256
import json
import time
import requests
from flask import Flask, jsonify, request
import shelve
from block import Block
from store import StoreController
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()


class Blockchain(StoreController):
    difficulty = 2

    def __init__(self):
        self.unconfirmedTransaction = self.getTransactionsStored()
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
        for element in self.chain:
            for transaction in element.transactions:
                if not transaction['uid'] is None:
                    if auth['uid'] == transaction['uid']:
                        return {"continue": True, "message": element.hash + ":" + auth['uid']}
        return {"continue": False}

    def validateCredentials(self, transaction, auth):
        checkPass = bcrypt.check_password_hash(
            transaction['password'], auth['password'])
        if (checkPass and auth['username'] == transaction['username']):
            return True
        return False

    '''
    Validar la necesidad de actualizar un registro antes de ser minado 
    def validatePendingTransaction(self, auth):
        for pending in self.getTransactionsStored():
            if pending['uid'] == auth['uid']:
                pending['username'] = auth['username']
                pending['email'] = auth['email']
                pending['password'] = bcrypt.generate_password_hash(
                    auth["password"])
                pending['timestamp'] = time.time()
                return True
        return False'''

    @property
    def lastBlock(self):
        return self.chain[-1]

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
