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

# Configuração das Intents (necessário para ver membros e conteúdo de mensagens)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

import datetime

class ZarathosBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=None # Vamos criar um help personalizado depois
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
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'Módulo {filename} carregado com sucesso.')
                except Exception as e:
                    print(f'Falha ao carregar módulo {filename}: {e}')

        # Adiciona verificação global para que apenas o dono do bot consiga usar os comandos
        @self.check
        async def globally_block_non_owner(ctx):
            return await self.is_owner(ctx.author)

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("**[Erro]** Você não tem permissão para usar meus comandos. Apenas meu mestre, Yago, pode fazer isso.")
        else:
            # Continua para os tratamentos normais de erros dos Cogs se não for erro de dono
            pass

    async def on_ready(self):
        print("-------")
        print(f'Bot conectado como: {self.user.name}')
        print(f'ID do Bot: {self.user.id}')
        print(f'Prefixo: {PREFIX}')
        print("-------")
        
        # Define o status do bot
        await self.change_presence(activity=discord.Game(name=f"Protegendo o servidor | {PREFIX}help"))

async def main():
    bot = ZarathosBot()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    if not TOKEN or TOKEN == "seu_token_aqui_nao_compartilhe":
        print("ERRO: O Token do Discord não foi configurado no arquivo .env!")
    else:
        try:
            keep_alive() # NOVO: Inicia o servidor web ANTES de iniciar o bot
            asyncio.run(main())
        except KeyboardInterrupt:
            pass
