import discord
from discord.ext import commands
import os

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='reload', aliases=['rc', 'recarregar'], help='Recarrega um módulo do bot sem desligá-lo.')
    @commands.is_owner()
    async def reload(self, ctx, extension: str):
        """Recarrega um módulo específico (ex: security, admin, utility)."""
        try:
            await self.bot.reload_extension(f'cogs.{extension}')
            await ctx.send(f"**[Sistema]** O módulo `{extension}.py` foi atualizado com sucesso! As novas funções já estão online.")
        except Exception as e:
            await ctx.send(f"**[Erro]** Falha ao recarregar o módulo `{extension}`:\n```py\n{e}\n```")

    @commands.command(name='load', help='Carrega um arquivo novo.')
    @commands.is_owner()
    async def load(self, ctx, extension: str):
        """Carrega um módulo que foi criado depois que o bot iniciou."""
        try:
            await self.bot.load_extension(f'cogs.{extension}')
            await ctx.send(f"**[Sistema]** O novo módulo `{extension}.py` foi detectado e inserido no sistema com sucesso!")
        except Exception as e:
            await ctx.send(f"**[Erro]** Falha ao carregar o módulo `{extension}`:\n```py\n{e}\n```")

    @commands.command(name='unload', help='Desativa um módulo inteiro.')
    @commands.is_owner()
    async def unload(self, ctx, extension: str):
        """Desliga temporiamente um módulo."""
        try:
            await self.bot.unload_extension(f'cogs.{extension}')
            await ctx.send(f"**[Sistema]** O módulo `{extension}.py` foi completamente desativado.")
        except Exception as e:
            await ctx.send(f"**[Erro]** Falha ao desativar o módulo `{extension}`:\n```py\n{e}\n```")

    @commands.command(name='reloadall', aliases=['rcall'], help='Recarrega TODOS os arquivos da pasta cogs.')
    @commands.is_owner()
    async def reloadall(self, ctx):
        """Atualiza todo o sistema do bot pegando todas as edições feitas de uma vez."""
        reloaded = []
        failed = []
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                ext = filename[:-3]
                try:
                    await self.bot.reload_extension(f'cogs.{ext}')
                    reloaded.append(ext)
                except Exception as e:
                    failed.append(f"{ext}: {type(e).__name__} - {e}")
        
        msg = f"**[Reinicialização Quente (Hot-Reload)]**\n"
        if reloaded:
            msg += f"**Carregados com sucesso:** `{', '.join(reloaded)}`\n"
        if failed:
            msg += f"**Falhas Críticas:**\n```py\n{chr(10).join(failed)}\n```"
            
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(Owner(bot))
