import asyncio
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

async def test_load():
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix='!', intents=intents)
    try:
    await bot.load_extension('cogs.economy')
    print("Módulo economy carregado com sucesso no teste.")
    except Exception as e:
    print(f"ERRO ao carregar modulo economy: {e}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_load())
