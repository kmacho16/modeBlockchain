from hashlib import sha256
import json
import time
import requests
import shelve
import jwt
from flask import Flask, jsonify, request
from model.block import Block
from model.blockchain import Blockchain
from model.peer import Peer
from flask_cors import CORS
import datetime
from functools import wraps
from utils.utils import stringToHash, create_chain_from_dump, activatePin, deactivatePin, addPeers, updatePeers, token_required, validateRecords, validateCredentials, validatePendingTransactionsPeers
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
devicesBlockchain = Blockchain("devices.ud", "tdevices.ud")


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


@app.route('/new_transaction/peer', methods=['POST'])
def newTransactionPeer():
    tx_data = request.get_json()
    required_fields = ["username"]
    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404
    blockchain.addNewTransaction(tx_data)
    response = jsonify({'continue': True})
    return response, 200


@app.route('/devices/new_transaction', methods=['POST'])
def devices_new_transactions():
    data = request.get_json()
    data['timestamp'] = time.time()
    devicesBlockchain.addNewTransaction(data)
    response = jsonify(status="continue")
    return response, 200


@app.route('/login', methods=['POST'])
def login():
    authData = request.get_json()
    required_fields = ['username', 'password', 'uid']
    for field in required_fields:
        if not authData.get(field):
            return "Invalid transaction data", 404
    lastTransaction = blockchain.uidExist(authData)
    response = validateRecords(lastTransaction)
    if(response['continue'] and validateCredentials(lastTransaction['transaction'], authData)):
        token = jwt.encode({'public_id': response['message'], 'exp': datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=180)}, app.config['SECRET_KEY'])
        return jsonify({'continue': True, 'token': token.decode('UTF-8')})
    else:
        return jsonify({'continue': False, 'message': 'Credenciales incorrectas o dispositivo no registrado'})


'''@app.route('/mine/peers', methods=['POST'])
    def minePeers():
        authData = request.get_json()[""]'''


@app.route('/get-data', methods=['GET'])
@token_required
def getData(current_user):
    return jsonify({'message': current_user})


@app.route('/change_led_status/<int:pin>/<int:status>', methods=['POST'])
@token_required
def changeLedStatus(current_user, pin, status):
    node, uid, username = current_user.split(":")
    if(status == 1):
        action = activatePin(pin)
    else:
        action = deactivatePin(pin)
    data = {"uid": uid, "username": username, "action": action}
    data["timestamp"] = time.time()
    blockchain.addNewTransaction(data)
    return jsonify({"continue": True, "message": "Interaccion registrada"})


@app.route('/register/user', methods=['POST'])
def new_user_register():
    authData = request.get_json()
    required_fields = ["username", "email", "password", "uid"]
    for field in required_fields:
        if not authData.get(field):
            return "Invalid transaction data", 404
    authData["timestamp"] = time.time()
    authData["password"] = bcrypt.generate_password_hash(authData["password"])
    authData['active'] = True
    pending = blockchain.validatePendingTransaction(authData)
    previousTransaction = blockchain.uidExist(authData)
    if(pending['exist']):
        pending['transaction']['active'] = False
        blockchain.addNewTransaction(pending['transaction'])
    elif(previousTransaction['exist']):
        previousTransaction['transaction']['active'] = False
        blockchain.addNewTransaction(previousTransaction['transaction'])

    blockchain.addNewTransaction(authData)
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
    validatePendingTransactionsPeers()
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    return "Block #{} is mined.".format(result)


@app.route('/base/hash', methods=['GET'])
def getBasehash():
    blockchain = Blockchain()
    auxString = "%s:%s" % (blockchain.firstBlock.hash,
                           blockchain.lastBlock.hash)
    return jsonify({"hash": stringToHash(auxString)})


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


@app.route('/devices/pending_tx')
def get_dev_pending_tx():
    return jsonify(devicesBlockchain.unconfirmedTransaction), 200


@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node = request.get_json()
    if not node:
        return "Invalid data", 400
    blockchain.addPeersStored(node)
    chain_data = []
    chain = blockchain.getBlockChain()
    for block in chain:
        chain_data.append(block.__dict__)
    return jsonify({"peers": blockchain.getPeersStored(), "chain": chain_data}), 200


@app.route("/peers", methods=['GET'])
def getPeers():
    return jsonify(blockchain.getPeersStored()), 200


@app.route('/devices', methods=['get'])
def getDevices():
    devices = [{"id": "8f019343-15ee-4530-9e32-6f5cfd0665c0", "name": "Led Principal"},
               {"id": "7c39379a-1421-43f8-a341-0a5150138cc6", "name": "Led Secundario"}]
    return jsonify({"continue": True, "devices": devices})


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    nodeAddress = request.get_json()["node_address"]
    if not nodeAddress:
        return "invalid data", 400
    #print("************* register_with_existing_node *****************")
    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}
    # print(json.dumps(data))
    #print("************* end register_with_existing_node *****************")
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
