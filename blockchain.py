import hashlib
import json
from textwrap import dedent
from time import time
from urllib import response
from uuid import uuid4
from flask import Flask, jsonify, request

# La clase Blockchain es la encargada de almacenar y validar los datos de la blockchain.
class Blockchain(object):
    # Constructor de la clase Blockchain. Crea una lista vacía para almacenar la cadena y las transacciones
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Crea un bloque genesis y lo añade a la cadena
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        # Crea un nuevo bloque y lo añade a la cadena 
        """
        Crea un nuevo bloque en la Blockchain.
        :param proof: <int> la prueba de trabajo
        :param previous_hash: (Optional) <str> el hash del bloque anterior
        :return: <dict> nuevo bloque
        """
        
        block = {
            'index': len(self.chain) + 1,  # Toma la longitud de la cadena y le suma 1
            'timestamp': time(),           # Toma el tiempo actual
            'transactions': self.current_transactions,  # Toma las transacciones actuales
            'proof': proof,                               # Toma la prueba de trabajo
            'previous_hash': previous_hash or self.hash(self.chain[-1]) # Toma el hash del bloque anterior o el hash del último bloque
        }

        # Reinicia la lista de transacciones actuales
        self.current_transactions = []

        # Añade el bloque a la cadena
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):

        # Añade una nueva transaccion a la lista de transacciones
        """
        Crea una nueva transacción para agregar a la cadena.
        :param sender: <str> la dirección del remitente
        :param recipient: <str> la dirección del destinatario
        :param amount: <int> la cantidad
        :return: <int> el índice del bloque que contiene la transacción
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }) 

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        # Retorna el último bloque de la cadena
        return self.chain[-1]

    @staticmethod
    def hash(block):
        # Crea un hash del bloque
        """
        Crea un hash SHA-256 del bloque
        :param block: <dict> Block
        :return: <str>
        """

        # Serializa el bloque en JSON
        block_string = json.dumps(block, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()

    
    def proof_of_work(self, last_proof):
        # Crea una prueba de trabajo
        """
        Algoritmo de prueba de trabajo:
        - Encuentra un número p tal que hash(pp') contiene 4 ceros como el primero, donde p es el p' anterior.
        - p es la prueba previa y p' es la prueba actual.
        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        # Verifica que el hash contenga 4 ceros
        """
        Valida que la prueba: ¿El hash(last_proof, proof) contiene 4 ceros al principio?
        :param last_proof: <int> Prueba anterior
        :param proof: <int> Prueba actual
        :return: <bool> True si la prueba es válida, False si no lo es.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"




### PARTE DEL SERVIDOR ###

# Instanciar nuestro nodo
app = Flask(__name__)

# Generar una dirección unica para este nodo
node_identifier = str(uuid4()).replace('-', '')

# Instanciar la blockchain a través de la clase Blockchain
blockchain = Blockchain()

# Crea un endpoint llamado /mine el cual es una petición GET
@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1
    )

    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "Nueva mina",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200

# Crea el endpoint /transactions/new el cual es una petición POST, ya que vamos a enviar datos
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Valida que los campos requeridos estén presentes en la petición
    required = ['sender', 'recipient', 'amount']
    if not all(i in values for i in required):
        return 'Missing values', 400

    # Crea una nueva transacción
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'La transacción será añadida a un bloque {index}'}

    return jsonify(response), 201

# Crea el endpoint /chain el cual retorna la Blockchain completa
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

# Corre el servidor en el puerto 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)