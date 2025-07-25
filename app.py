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

# ==================== ROTAS DE VERIFICAÇÃO DISCORD ====================

@app.route('/api/check-discord-verification', methods=['GET'])
def check_discord_verification():
    wallet_address = request.args.get('wallet')
    if not wallet_address:
        return jsonify({"error": "Wallet address is required"}), 400

    try:
        # Verifica na tabela de verificação
        verification_response = supabase_client.table('discord_verifications') \
            .select('verified_at, discord_id') \
            .eq('wallet_address', wallet_address) \
            .execute()
        
        verified = len(verification_response.data) > 0
        
        # Verifica se está vinculado ao usuário principal
        user_response = supabase_client.table('users') \
            .select('discord_id') \
            .eq('wallet_address', wallet_address) \
            .execute()
        
        user_linked = len(user_response.data) > 0 and user_response.data[0]['discord_id']

        return jsonify({
            "verified": verified,
            "user_linked": user_linked,
            "verified_at": verification_response.data[0].get('verified_at') if verified else None,
            "discord_id": verification_response.data[0].get('discord_id') if verified else None
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/verify-user', methods=['POST'])
def verify_user():
    data = request.get_json()
    wallet_address = data.get('wallet')
    discord_id = data.get('discord_id')
    
    if not wallet_address or not discord_id:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        # Verifica se a verificação existe
        verification_response = supabase_client.table('discord_verifications') \
            .select('*') \
            .eq('wallet_address', wallet_address) \
            .eq('discord_id', discord_id) \
            .execute()
        
        if not verification_response.data:
            return jsonify({
                "verified": False,
                "message": "Discord verification not found"
            }), 404

        # Atualiza o usuário principal
        update_response = supabase_client.table('users') \
            .update({'discord_id': discord_id}) \
            .eq('wallet_address', wallet_address) \
            .execute()
        
        if update_response.data:
            return jsonify({
                "verified": True,
                "message": "Discord account linked successfully"
            }), 200
        else:
            return jsonify({
                "verified": False,
                "message": "Failed to update user record"
            }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== ROTA PARA MISSÕES ====================

@app.route('/api/update-mission-progress', methods=['POST'])
def update_mission_progress():
    data = request.get_json()
    user_id = data.get('user_id')
    mission_id = data.get('mission_id')
    progress = data.get('progress')
    
    if not all([user_id, mission_id, progress is not None]):
        return jsonify({"error": "Missing parameters"}), 400

    try:
        # Busca a missão do usuário
        mission_response = supabase_client.table('user_missions') \
            .select('id, progress') \
            .eq('user_id', user_id) \
            .eq('mission_id', mission_id) \
            .single() \
            .execute()
        
        current_progress = mission_response.data.get('progress', 0)
        new_progress = max(current_progress, progress)  # Não diminui o progresso
        
        # Atualiza o progresso
        update_response = supabase_client.table('user_missions') \
            .update({
                'progress': new_progress,
                'last_updated': 'now()'
            }) \
            .eq('id', mission_response.data['id']) \
            .execute()
        
        return jsonify({
            "success": True,
            "new_progress": new_progress
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Inicia o servidor Flask
    app.run(host='0.0.0.0', port=5000, debug=True)
