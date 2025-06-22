# app.py
from flask import Flask
from flask_cors import CORS
from wallet_api import wallet_bp

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Registra apenas o blueprint da carteira
    app.register_blueprint(wallet_bp(), url_prefix='/api/wallet')
    
    return app

if __name__ == '__main__': 
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)