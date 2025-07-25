import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações do Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Inicializa o Flask
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Importa e registra o blueprint da carteira
from wallet_api import wallet_bp
app.register_blueprint(wallet_bp, url_prefix='/api/wallet')

# ==================== ROTA DE VERIFICAÇÃO DISCORD ====================

@app.route('/api/check-discord-verification', methods=['GET'])
def check_discord_verification():
    wallet_address = request.args.get('wallet')
    if not wallet_address:
        return jsonify({"error": "Wallet address is required"}), 400

    try:
        # Busca a verificação no banco de dados
        response = supabase_client.table('discord_verifications') \
            .select('verified_at') \
            .eq('wallet_address', wallet_address) \
            .execute()
        
        verified = len(response.data) > 0
        return jsonify({
            "verified": verified,
            "verified_at": response.data[0].get('verified_at') if verified else None
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=5000, debug=True)
