import os
import re
import discord
from discord.ext import commands
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
VERIFY_CHANNEL_ID = int(os.getenv('DISCORD_VERIFY_CHANNEL_ID'))
VERIFIED_ROLE_ID = int(os.getenv('DISCORD_VERIFIED_ROLE_ID'))

# Log inicial
print(f"🟡 Iniciando bot...")
print(f"🟡 SUPABASE_URL: {SUPABASE_URL}")
print(f"🟡 SUPABASE_KEY: {SUPABASE_KEY[:5]}...")
print(f"🟡 VERIFY_CHANNEL_ID: {VERIFY_CHANNEL_ID}")
print(f"🟡 VERIFIED_ROLE_ID: {VERIFIED_ROLE_ID}")

# Inicializa o Supabase
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Conexão com Supabase estabelecida")
except Exception as e:
    print(f"❌ Erro ao conectar ao Supabase: {str(e)}")
    exit(1)

# Inicializa o bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name}')
    print(f'⚙️ Canal de verificação: {VERIFY_CHANNEL_ID}')
    print(f'🎯 Cargo verificado: {VERIFIED_ROLE_ID}')

@bot.event
async def on_message(message):
    # Ignora mensagens de bots e de outros canais
    if message.author.bot:
        return

    print(f"\n--- Nova mensagem de {message.author} no canal {message.channel.id} ---")
    print(f"Conteúdo: '{message.content}'")
    
    if message.channel.id != VERIFY_CHANNEL_ID:
        print(f"❌ Mensagem fora do canal de verificação (esperado: {VERIFY_CHANNEL_ID})")
        return

    # ============== BLOCO QUE ESTAVA FALTANDO ==============
    # Expressão regular para wallets
    wallet_pattern = r'(0x[a-fA-F0-9]{40}|[1-9A-HJ-NP-Za-km-z]{32,44})'
    match = re.search(wallet_pattern, message.content)
    
    if not match:
        print("❌ Nenhuma carteira válida encontrada na mensagem")
        await message.reply(
            "🚫 **Formato inválido!**\n"
            "Por favor, envie apenas seu endereço de carteira.\n"
            "Exemplos:\n"
            "- Ethereum: `0x742d35Cc6634C0532925a3b844Bc454e4438f44e`\n"
            "- Solana: `4F3e6d7A8B9c0d1E2f3A4B5C6d7E8F9a0B1C2D3E`"
        )
        return

    wallet_address = match.group(0)
    # ============== FIM DO BLOCO FALTANTE ==============
    
    discord_id = str(message.author.id)
    discord_name = message.author.name

    print(f"✅ Carteira detectada: {wallet_address}")
    print(f"🆔 Discord ID: {discord_id}")
    print(f"👤 Discord Name: {discord_name}")

    try:
        # Verifica se a wallet já foi usada
        print("🔍 Verificando se carteira já existe...")
        response = supabase.table('discord_verifications') \
            .select('*') \
            .eq('wallet_address', wallet_address) \
            .execute()
        
        if response.data and len(response.data) > 0:
            existing = response.data[0]
            print(f"⚠️ Carteira já verificada por: {existing['discord_name']} (ID: {existing['discord_id']})")
            await message.reply(
                f"⚠️ **Carteira já verificada!**\n"
                f"Esta carteira `{wallet_address}` já está associada a outro usuário."
            )
            return

        # Registra a verificação no banco de dados
        print("📝 Registrando nova verificação...")
        response = supabase.table('discord_verifications').insert({
            'wallet_address': wallet_address,
            'discord_id': discord_id,
            'discord_name': discord_name
        }).execute()
        
        if response.error:
            print(f"❌ Erro ao inserir: {response.error}")
        else:
            print(f"✅ Registro inserido com sucesso: {response.data}")

        # Atribui o cargo de verificado
        guild = message.guild
        role = guild.get_role(VERIFIED_ROLE_ID)
        
        if not role:
            print(f"❌ Cargo de verificado não encontrado! ID: {VERIFIED_ROLE_ID}")
            await message.reply("❌ Cargo de verificado não configurado corretamente!")
            return
            
        await message.author.add_roles(role)
        print(f"🎯 Cargo atribuído: {role.name}")
        
        # Resposta com confirmação
        await message.reply(
            f"✅ **Verificação bem-sucedida!**\n"
            f"Carteira `{wallet_address}` registrada.\n"
            f"Bem-vindo(a) ao servidor, {message.author.mention}!"
        )

    except Exception as e:
        print(f"🔥 ERRO: {str(e)}")
        await message.reply(
            "❌ **Erro durante a verificação!**\n"
            "Tente novamente ou contate um administrador.\n"
            f"Detalhes: `{str(e)}`"
        )

if __name__ == '__main__':
    print("\n🚀 Iniciando bot...")
    bot.run(DISCORD_TOKEN)
