import discord
from discord.ext import commands
from discord import app_commands
import random
import os
import logging
from dotenv import load_dotenv

# Configurar logging para Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ... resto do código permanece igual ...
# (VampireDiceResult, format_dice_results, etc.)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} está conectado e pronto!')
    logger.info(f'Comandos disponíveis: /vamp, /dados, !vamp, !ajuda_vamp')
    
    # Sincronizar comandos slash
    try:
        synced = await bot.tree.sync()
        logger.info(f"Sincronizados {len(synced)} comandos slash")
    except Exception as e:
        logger.error(f"Falha ao sincronizar comandos: {e}")

# ... resto do código dos comandos ...

if __name__ == "__main__":
    logger.info("🧛 Iniciando bot de Vampiro: A Máscara...")
    logger.info("🎛️ Novos recursos: Interface interativa com /dados")
    logger.info("📖 Use !ajuda_vamp para ver todos os comandos")
    
    # Obter token da variável de ambiente
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        logger.error("❌ ERRO: Token não encontrado!")
        logger.error("💡 Certifique-se de definir a variável DISCORD_TOKEN")
        exit(1)
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("❌ ERRO: Token inválido!")
    except Exception as e:
        logger.error(f"❌ ERRO inesperado: {e}")
