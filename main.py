from hashlib import sha256
import json
import time
import requests
from flask import Flask, jsonify, request
import shelve
from block import Block
from blockchain import Blockchain
from flask_cors import CORS
import datetime
from functools import wraps
from utils import create_chain_from_dump, addPeers, updatePeers, token_required
import jwt
from flask_bcrypt import Bcrypt

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

app = Flask(__name__)
app.config['SECRET_KEY'] = '3st03sS3cr3t0'
CORS(app)
bcrypt = Bcrypt(app)
blockchain = Blockchain()


@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["username"]
    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404
    tx_data["timestamp"] = time.time()
    blockchain.addNewTransaction(tx_data)
    response = jsonify(username=tx_data["username"])
    return response, 200


@app.route('/login', methods=['POST'])
def login():
    mRequest = request.get_json()
    required_fields = ['username', 'password', 'uid']
    for field in required_fields:
        if not mRequest.get(field):
            return "Invalid transaction data", 404
    response = blockchain.uidExist(mRequest)
    if(response['continue']):
        token = jwt.encode({'public_id': response['message'], 'exp': datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=180)}, app.config['SECRET_KEY'])
        return jsonify({'token': token.decode('UTF-8')})
    else:
        return jsonify({'continue': False, 'message': 'Credenciales incorrectas o dispositivo no registrado'})


@app.route('/get-data', methods=['GET'])
@token_required
def getData(current_user):
    return jsonify({'message': current_user})


@app.route('/register/user', methods=['POST'])
def new_user_register():
    tx_data = request.get_json()
    required_fields = ["username", "email", "password", "uid"]
    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404
    tx_data["timestamp"] = time.time()
    tx_data["password"] = bcrypt.generate_password_hash(tx_data["password"])
    tx_data['active'] = True
    blockchain.addNewTransaction(tx_data)
    response = jsonify(status="ok")
    return response, 200


@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    chain = blockchain.getBlockChain()
    for block in chain:
        chain_data.append(block.__dict__)
    return jsonify({"length": len(chain_data),
                    "chain": chain_data})


@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    return "Block #{} is mined.".format(result)


@app.route('/last/hash', methods=['GET'])
def getLastHash():
    exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    return jsonify({"message": blockchain.lastBlock.hash+":"+exp.strftime("%x")}), 200


@app.route('/validate/<mHash>', methods=['GET'])
def validateHash(mHash):
    if(blockchain.lastBlock.hash == mHash):
        return jsonify({"continue": True, "message": "Hash validado correctamente"})
    return jsonify({"continue": False, "message": "Hash no valido "})


@app.route('/pending_tx')
def get_pending_tx():
    return jsonify(blockchain.unconfirmedTransaction), 200


@app.route('/register_node', methods=['POST'])
def register_new_peers():
    # The host address to the peer node
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    addPeers(node_address)
    return get_chain()


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    nodeAddress = request.get_json()["node_address"]
    if not nodeAddress:
        return "invalid data", 400

    data = {"node_address", request.host_url}
    headers = {'Content-Type': "application/json"}
    response = requests.post(nodeAddress + "/register_node",
                             data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        global blockchain
        # update chain and the peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        updatePeers(response.json()['peers'])
        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)
    if not added:
        return "The block was discarded by the node", 400
    return "Block added to the chain", 201


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5001,
                        type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    app.run(host='0.0.0.0', port=port)
