import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

async def test():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='z.', intents=intents)
    print("Starting bot test connection...")
    try:
    # We don't want to actually start the loop forever, just see if it connects
    # await bot.start(TOKEN)
    # But bot.start is what connects.
    print(f"Token length: {len(TOKEN) if TOKEN else 0}")
    # Let's just try to login
    await bot.login(TOKEN)
    print("Login successful!")
    await bot.close()
    except Exception as e:
    print(f"BOT ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test())
