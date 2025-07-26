from mnemonic import Mnemonic
from ecdsa import SigningKey, SECP256k1, VerifyingKey
import hashlib
import hmac
import binascii

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
