# blockchain/wallet_api.py
from flask import Blueprint, jsonify, request
from wallet import Wallet

def wallet_bp():
    bp = Blueprint('wallet', __name__)

    @bp.route('/create', methods=['GET'])
    def create_wallet():
        wallet = Wallet.create()
        return jsonify(wallet), 200

    @bp.route('/import', methods=['POST'])
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

    return bp
