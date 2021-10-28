#let's start creating a cryptocurrency

import datetime
import hashlib
import json
from flask import Flask,jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

#part 1-building blockchain
class Blockchain:
    def __init__(self):   #init is constructor in python
        self.chain = [];
        self.transactions=[]
        self.create_block(proof=1,previous_hash='0')
        self.nodes=set()                  #contains a list of all the nodes in the network
        
    def create_block(self,proof,previous_hash):
        block={'index':len(self.chain)+1,
               'timestamp':str(datetime.datetime.now()),
               'proof':proof,
               'previous_hash':previous_hash,
               'transactions' :self.transactions}
        self.transactions=[]
        self.chain.append(block)
        return block
    
    def get_last_block(self):
        return self.chain[-1]
    
    def proof_of_work(self,previous_proof):
        new_proof=1
        check_proof=False
        while check_proof is False:
            hash_function=hashlib.sha256(str(new_proof**2-previous_proof**2).encode()).hexdigest()
            if hash_function[:4]=='0000':
                check_proof=True
            else:
                new_proof+=1
        return new_proof
            
    def hash(self,block):
        encoded_block=json.dumps(block,sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self):
        previous_block=self.chain[0]
        block_idx=1
        while block_idx < len(self.chain):
            block=self.chain[block_idx]
            if block['previous_hash']!=self.hash(previous_block):
                return False
            previous_proof=previous_block['proof']
            current_proof=block['proof']
            hash_function=hashlib.sha256(str(current_proof**2-previous_proof**2).encode()).hexdigest()
            if hash_function[:4]!='0000':
                return False
            previous_block=block
            block_idx+=1
        return True
    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender':sender,
                                  'receiver':receiver,
                                  'amount':amount})
        return self.get_last_block()['index']+1
    
    def add_node(self,address):            #adds node containing that address to the set of nodes
        parsed_url = urlparse(address)      #returns parsed address
        self.nodes.add(parsed_url.netloc)   #netloc cuts out only the url part of the address
        
    def replace_chain(self):             #replaces the chain of current node after comparing
        network=self.nodes               #with the chains of all the nodes in the network
        longest_chain=None
        max_length=len(self.chain)
        for node in network:
            response=requests.get(f'http://{node}/get_chain')   #gets the address of every node in the network
            if response.status_code == 200:
                length=response.json()['length']
                chain= response.json()['chain']
                if length>max_length and self.is_chain_valid(chain):
                    max_length=length
                    longest_chain=chain                 #for loop ends
        if longest_chain:
            self.chain=longest_chain
            return True
        return False
    
#part2-mining a block
#creating a webapp
app = Flask(__name__)

#creating a node address on port 5000
node_address=str(uuid4()).replace('-','')       #randomly generates an add since after mining a coin will be transferred from this add to the miner

#creating a blockchain
blockchain=Blockchain()
    
#mining a new block
@app.route("/mine_block",methods=['GET'])          #equivalent of app.get in webdev
def mine_block():                                   #FUNCTION TO TRIGGER WHEN GET REQUEST IS MADE
    previous_block = blockchain.get_last_block()
    previous_proof = previous_block['proof']
    curr_proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender=node_address, receiver='Samrat', amount=1)
    block = blockchain.create_block(curr_proof,previous_hash)
    response = {'message':'mined successfully',
                'index':block['index'],
                'timestamp':block['timestamp'],
                'proof':block['proof'],
                'previous_hash':block['previous_hash'],
                'transactons': block['transactions']}
    return jsonify(response), 200                  #200 is for success code
    
#getting the full blockchain
@app.route("/get_chain",methods=['GET'])
def get_chain():
    response={'block':blockchain.chain,
              'length':len(blockchain.chain)}
    return jsonify(response), 200

#checking if the blockchain is valid
@app.route("/is_valid",methods=['GET'])
def is_valid():
    is_valid=blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response={'Message':'All good. The chain is valid'}
    else:
        response={'Message':'The chain is not valid'}
    return jsonify(response),200

#posting transaction to the blockchain
@app.route("/add_transaction",methods=['POST'])
def add_transaction():
    json=request.get_json()                 #gets parsed json input
    transaction_keys=['sender','receiver','amount']     #checking if all the keys of transaction keys
    if not all(key in json for key in transaction_keys): #are present in the parsed json file
        return 'some elements are missing', 400
    index=blockchain.add_transaction(json['sender'],json['receiver'], json['amount'])
    response={'message':f'This transaction will be added to block {index}'}
    return jsonify(response),201

#part 3-decentralizing a blockchain
#connecting new nodes
@app.route("/connect_nodes",methods=['POST'])
def connect_nodes():
    json=request.get_json()
    nodes=json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response={'message':'all the nodes are now connected',
              'total_nodes':list(blockchain.nodes)} #nodes is the set initialised in init method
    return jsonify(response),201

#replacing the chain at a node with the longest one in the network
@app.route("/replace_chain",methods=['GET'])
def replace_chain():
    is_chain_replaced=blockchain.replace_chain()
    if is_chain_replaced:
        response={'Message':'The chain was replaced with the longest one',
                  'new_chain': blockchain.chain}
    else:
        response={'Message':'All good!',
                  'actual_chain':blockchain.chain}
    return jsonify(response),200

#running the app
#app.debug=True
app.run(host='0.0.0.0', port=5002)