import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive # NOVO: Importa o servidor web 24/7

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('PREFIX', '!')

# Habilitar TODAS as intents para garantir que módulos de segurança (audit log, members, etc.) funcionem sem restrições
intents = discord.Intents.all()

import datetime

class ZarathosBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=None,
            status=discord.Status.dnd,
            activity=discord.Game(name=f"Protegendo o servidor | {PREFIX}help")
        )
        self.start_time = datetime.datetime.now(datetime.timezone.utc)

    async def setup_hook(self):
        # Aqui carregaremos os Cogs (módulos de comandos)
        print("-------")
        print(f"Iniciando {self.user}...")
        
        # Pasta para os Cogs
        if not os.path.exists('./cogs'):
            os.makedirs('./cogs')
            print("Diretório 'cogs' criado.")

        # Carrega extensões da pasta cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                try:
                    ext = filename.replace('.py', '')
                    await self.load_extension(f'cogs.{ext}')
                    print(f'Módulo {filename} carregado com sucesso.')
                except Exception as e:
                    print(f'Falha ao carregar módulo {filename}: {e}')

    async def on_ready(self):
        print("-------")
        print(f'Bot conectado como: {self.user.name}')
        print(f'ID do Bot: {self.user.id}')
        print(f'Prefixo: {PREFIX}')
        print("-------")

async def main():
    bot = ZarathosBot()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    if not TOKEN or TOKEN == "seu_token_aqui_nao_compartilhe":
        print("ERRO: O Token do Discord não foi configurado no arquivo .env!")
    else:
        try:
            # keep_alive() # Usado apenas no Replit. Na Square Cloud nao e necessario.
            asyncio.run(main())
        except KeyboardInterrupt:
            pass
