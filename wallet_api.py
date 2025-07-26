# blockchain/wallet_api.py
from flask import Blueprint, jsonify, request
from mnemonic import Mnemonic
from ecdsa import SigningKey, SECP256k1, VerifyingKey
import hashlib
import hmac

# Cria o objeto Blueprint diretamente
wallet_bp = Blueprint('wallet', __name__)

@wallet_bp.route('/create', methods=['GET'])
def create_wallet():
    wallet = Wallet.create()
    return jsonify(wallet), 200
    
@wallet_bp.route('/ping', methods=['GET'])
def ping():
    return jsonify({'message': 'API Sunaryum online'}), 200
    
@wallet_bp.route('/import', methods=['POST'])
def import_wallet():
    data = request.get_json()
    if not data or 'mnemonic' not in data:
        return jsonify({
            "status": "error",
            "message": "Mnemonic phrase is required"
        }), 400
    
    try:
        wallet = Wallet.import_from_mnemonic(data['mnemonic'])
        
        # Retorna dados essenciais para o frontend
        return jsonify({
            "status": "success",
            "address": wallet["address"],
            "public_key": wallet["public_key"],
            "private_key": wallet["private_key"]
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

class Wallet:
    @staticmethod
    def create() -> dict:
        mnemo = Mnemonic('english')
        seed = mnemo.generate(strength=128)
        # Usa o mesmo método de derivação para criação e importação
        wallet = Wallet.derive_from_mnemonic(seed)
        wallet["mnemonic"] = seed
        return wallet

    @staticmethod
    def import_from_mnemonic(mnemonic: str) -> dict:
        return Wallet.derive_from_mnemonic(mnemonic)

    @staticmethod
    def derive_from_mnemonic(mnemonic: str) -> dict:
        # Deriva uma seed determinística do mnemônico
        seed_bytes = Mnemonic.to_seed(mnemonic, passphrase="")
        
        # Usa HMAC-SHA512 para derivar a chave privada
        # (Esta é uma abordagem simplificada, ideal seria usar BIP32)
        derived_key = hmac.new(b"SunaryumDerivation", seed_bytes, hashlib.sha512).digest()
        
        # Separa em chave privada (primeiros 32 bytes) e chain code
        private_key_bytes = derived_key[:32]
        
        priv = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
        pub = priv.get_verifying_key()
        
        return {
            "private_key": priv.to_string().hex(),
            "public_key": pub.to_string("compressed").hex(),
            "address": Wallet.generate_address(pub)
        }

    @staticmethod
    def generate_address(pub_key: VerifyingKey) -> str:
        return hashlib.sha256(pub_key.to_string()).hexdigest()[:40]
