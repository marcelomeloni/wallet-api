import os
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

# Inicializa o Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    if message.author.bot or message.channel.id != VERIFY_CHANNEL_ID:
        return

    # Remove espaços e quebras de linha
    wallet_address = message.content.strip()
    
    # Verificação básica de comprimento
    if len(wallet_address) < 20 or len(wallet_address) > 50:
        await message.reply(
            "🚫 **Formato inválido!**\n"
            "Por favor, envie apenas seu endereço de carteira gerado pelo sistema Sunaryum."
        )
        return

    discord_id = str(message.author.id)
    discord_name = message.author.name

    try:
        # Verifica se a wallet já foi usada
        existing = supabase.table('discord_verifications') \
            .select('discord_id') \
            .eq('wallet_address', wallet_address) \
            .execute()
        
        if existing.data and len(existing.data) > 0:
            await message.reply(
                f"⚠️ **Carteira já verificada!**\n"
                f"Esta carteira `{wallet_address}` já está associada a outro usuário."
            )
            return

        # Registra a verificação no banco de dados
        supabase.table('discord_verifications').upsert({
            'wallet_address': wallet_address,
            'discord_id': discord_id,
            'discord_name': discord_name,
            'verified_at': 'now()'
        }).execute()

        # Atribui o cargo de verificado
        guild = message.guild
        role = guild.get_role(VERIFIED_ROLE_ID)
        await message.author.add_roles(role)
        
        # Resposta com confirmação
        await message.reply(
            f"✅ **Verificação bem-sucedida!**\n"
            f"Carteira `{wallet_address}` registrada.\n"
            f"Bem-vindo(a) ao servidor, {message.author.mention}!"
        )

    except Exception as e:
        print(f"Erro na verificação: {str(e)}")
        await message.reply(
            "❌ **Erro durante a verificação!**\n"
            "Tente novamente ou contate um administrador."
        )

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
