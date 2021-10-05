import requests
from flask import jsonify, request
from model.block import Block
from model.blockchain import Blockchain
from model.concensus import Concensus
import json
from functools import wraps
from raspi import Raspi
import jwt
from flask_bcrypt import Bcrypt
import base64
import hashlib
from requests.exceptions import ConnectionError

bcrypt = Bcrypt()

SECRET_KEY = '3st03sS3cr3t0'
peers = set()
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"
blockchain = Blockchain()


yellowLed = Raspi(12, "LedPrincipal")
otroLed = Raspi(4, "LedPrincipal")


def consensus():
    global blockchain
    longestChain = None
    currentLength = len(blockchain.chain)

    for node in peers:
        response = request.get('{i}/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > currentLength and blockchain.checkChainValidity(chain):
            currentLength = length
            longestChain = chain
        if longestChain:
            blockchain = longestChain
            return True

        return False


def fetch_posts():
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content,
                       key=lambda k: k['timestamp'],
                       reverse=True)


def activatePin():
    yellowLed.changeOutPin(True)
    otroLed.changeOutPin(True)
    return ({"uuid": yellowLed.uuid,
             "name": yellowLed.name,
             "state": "activate"})


def deactivatePin():
    yellowLed.changeOutPin(False)
    otroLed.changeOutPin(False)

    return ({"uuid": yellowLed.uuid,
             "name": yellowLed.name,
             "state": "deactivate"})


def announce_new_block(block):
    for peer in peers:
        url = "{}add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))


def create_chain_from_dump(chain_dump):
    # blockchain = BlockChain()
    for idx, block_data in enumerate(chain_dump):
        print("*************** BLOCK  *****************")
        print(json.dumps(block_data))
        print("*************** BLOCK END  *****************")
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previousHash"])
        proof = block_data['hash']
        if idx > 0:
            added = blockchain.addBlock(block, proof)
            if not added:
                raise Exception("The chain dump is tampered!!")
        else:  # the block is a genesis block, no verification needed
            blockchain.chain.append(block)
    return blockchain


def addPeers(node_address):
    peers.add(node_address)


def updatePeers(address):
    global peers
    peers.update(address)


def validateRecords(record):
    response = {'continue': False}
    if 'active' in record and record['active']:
        response = {"continue": True,
                    "message": record['node'] + ":" + record['transaction']['uid'] + ":" + record['transaction']['username']}
    else:
        response = {'continue': False}
    return response


def validateCredentials(transaction, auth):
    checkPass = bcrypt.check_password_hash(
        transaction['password'], auth['password'])
    if (checkPass and auth['username'] == transaction['username']):
        return True
    return False


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
        if not token:
            return jsonify({'message': 'a valid token is missing'})
        try:
            data = jwt.decode(token, SECRET_KEY)
            current_user = data['public_id']
        except:
            return jsonify({'message': 'token is invalid'})
        return f(current_user, *args, **kwargs)
    return decorator


def stringToHash(jsonString):
    jsonString = jsonString.replace(" ", "").replace("\n", "")
    return hashlib.md5(jsonString).hexdigest()


def addVote(nodesList, pendinHash, nodeAddress=""):
    voted = False
    for node in nodesList:
        if node.baseHash == pendinHash:
            node.addVote()
            voted = True
    if(not voted):
        nodesList.append(Concensus(pendinHash, 1, nodeAddress))
    return nodesList


def findBestNode(nodesList):
    maxValue = 0
    for index, node in enumerate(nodesList):
        if(index == 0):
            maxValue = node.votes
        elif(node.votes > maxValue):
            maxValue = node.votes
            nodesList.remove(nodesList[index-1])
        elif(node.votes < maxValue):
            nodesList.remove(node)
    return nodesList


def getTransactionFromMainServer(nodeAddress):
    print("*************** getTransactionFromMainServer ***************")
    print(blockchain.unconfirmedTransaction)
    response = consumePendingTransaction(nodeAddress)
    print(response.json)


def consumePendingTransaction(nodeAddress):
    headers = {'Content-Type': "application/json"}
    response = requests.get(
        nodeAddress + "/pending_tx", headers=headers)
    return response


def validatePendingTransactionsPeers():
    optionsList = []
    jsonString = json.dumps(
        blockchain.unconfirmedTransaction, sort_keys=True).encode()
    mainTransactions = stringToHash(jsonString)
    initNode = Concensus(mainTransactions, 1)
    optionsList.append(initNode)
    optionsList.append(Concensus("XXXXX", 0, "test"))
    try:
        for peer in blockchain.getPeersTransactionStored():
            nodeAddress = peer['node_address']
            response = consumePendingTransaction(nodeAddress)
            peerTransaction = stringToHash(response.text)
            optionsList = addVote(optionsList, peerTransaction, nodeAddress)
    except ConnectionError as e:
        print("ERROR CONECTANDO %s " % e)
    optionsList = findBestNode(optionsList)
    if not optionsList[0].validateMain():
        getTransactionFromMainServer(optionsList[0].nodeAddress)


def encodeBase64(data):
    return base64.b64encode(data)


def decodeBase64(stringBase64):
    return base64.b64decode(stringBase64)
