import requests
from flask import jsonify, request
from block import Block
from blockchain import Blockchain
import json
from functools import wraps
import jwt
SECRET_KEY = '3st03sS3cr3t0'
peers = set()
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"
blockchain = Blockchain()


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


def announce_new_block(block):
    for peer in peers:
        url = "{}add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))


def create_chain_from_dump(chain_dump):
    blockchain = BlockChain()
    for idx, block_data in enumerate(chain_dump):
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"])
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


def validateRecords(records):
    response = {'continue': False}
    for record in records:
        if record['transaction']['active']:
            response = {"continue": True,
                        "message": record['node'] + ":" + record['transaction']['uid']}
        else:
            response = {'continue': False}
    return response


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
