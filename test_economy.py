import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()

async def test():
    try:
    from cogs.economy import Economy
    # Mock simple bot
    bot = commands.Bot(command_prefix='z.', intents=discord.Intents.default())
    cog = Economy(bot)
    if cog.collection is not None:
    print("TEST: Economy loaded and connected to DB")
    else:
    print(f"TEST: Economy loaded but DB failed: {cog.error_msg}")
    except Exception as e:
    print(f"TEST ERROR: {e}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
