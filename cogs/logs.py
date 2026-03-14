import discord
from discord.ext import commands
import datetime

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Canal de logs por servidor (Em uma versão futura, usar DB)
        self.log_channels = {}

    @commands.group(name='logs', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def logs(self, ctx):
        """Comando raiz do sistema de logs."""
        await ctx.send(f"Sintaxe operacional: `{ctx.prefix}logs set #canal` para definir diretriz de registro.")

    @logs.command(name='set', help='Define qual canal vai receber os logs importantes.')
    @commands.has_permissions(administrator=True)
    async def set_logs(self, ctx, channel: discord.TextChannel):
        """Define o canal de logs do servidor."""
        self.log_channels[ctx.guild.id] = channel.id
        await ctx.send(f"**[Configuração]** Diretório de registros apontado para {channel.mention}.")

    async def send_log(self, guild, embed):
        """Função auxiliar para enviar logs para o canal configurado."""
        channel_id = self.log_channels.get(guild.id)
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)

    # Evento: Membro Banido
    @commands.Cog.listener()
    async def on_member_banner(self, guild, user): # Erro comum, o evento correto é on_member_ban
        pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(
            title="[Registro] - Membro Banido",
            description=f"O membro **{user.name}** ({user.id}) teve o acesso revogado globalmente neste servidor.",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Tenta buscar o motivo no audit log
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                embed.add_field(name="Responsável", value=entry.user.name)
                embed.add_field(name="Motivo", value=entry.reason or "Não informado")
                break
        
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = discord.Embed(
            title="[Registro] - Membro Desbanido",
            description=f"O membro **{user.name}** ({user.id}) teve seu acesso restaurado.",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url if user.display_avatar else None)
        
        # Tenta buscar o responsável no audit log
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
            if entry.target.id == user.id:
                embed.add_field(name="Responsável", value=entry.user.name)
                embed.add_field(name="Motivo", value=entry.reason or "Não informado")
                break
        
        await self.send_log(guild, embed)


    # Evento: Membro Expulso
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        # Verifica se foi kick via audit log (kick dispara remove)
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id:
                embed = discord.Embed(
                    title="[Registro] - Membro Expulso",
                    description=f"O membro **{member.name}** ({member.id}) foi removido compulsoriamente.",
                    color=discord.Color.from_rgb(0, 0, 0),
                    timestamp=datetime.datetime.utcnow()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.add_field(name="Responsável", value=entry.user.name)
                embed.add_field(name="Motivo", value=entry.reason or "Não informado")
                await self.send_log(guild, embed)
                break

    # Evento: Mensagem Deletada (Útil para o clear)
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
            
        embed = discord.Embed(
            title="[Registro] - Mensagem Deletada",
            description=f"Registro obliterado. Autor originário: {message.author.mention}. Foco: {message.channel.mention}.",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Conteúdo", value=message.content or "*(Mensagem sem texto ou apenas imagem)*")
        await self.send_log(message.guild, embed)

    # Evento: Mensagem Editada
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
            
        embed = discord.Embed(
            title="[Registro] - Mensagem Alterada",
            description=f"Registro modificado. Autor originário: {before.author.mention}. Foco: {before.channel.mention}.",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="De", value=before.content or "*(Sem conteúdo textual)*", inline=False)
        embed.add_field(name="Para", value=after.content or "*(Sem conteúdo textual)*", inline=False)
        embed.add_field(name="Link Direto", value=f"[Acessar]({after.jump_url})", inline=False)
        await self.send_log(before.guild, embed)

    # Evento: Canal Criado
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(
            title="Novo Diretório Detectado",
            description=f"Um novo canal foi criado no servidor.",
            color=discord.Color.brand_green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Tipo de Diretório", value=str(channel.type).capitalize())
        embed.add_field(name="ID do Diretório", value=channel.id)
        
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
            if entry.target.id == channel.id:
                embed.add_field(name="Arquiteto", value=entry.user.mention, inline=False)
                break
                
        await self.send_log(channel.guild, embed)

    # Evento: Canal Deletado
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(
            title="Diretório Obliterado",
            description=f"Um canal foi permanentemente apagado.",
            color=discord.Color.brand_red(),
            timestamp=datetime.datetime.utcnow()
        )
        
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if entry.target.id == channel.id:
                embed.add_field(name="Destruidor", value=entry.user.mention, inline=False)
                break
                
        await self.send_log(channel.guild, embed)

    # Evento: Cargo Criado
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = discord.Embed(
            title="[Hierarquia] - Nova Patente Registrada",
            description=f"A patente {role.mention} foi instanciada.",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.datetime.utcnow()
        )
        
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
            if entry.target.id == role.id:
                embed.add_field(name="Autoridade", value=entry.user.mention, inline=False)
                break
                
        await self.send_log(role.guild, embed)

    # Evento: Cargo Deletado
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        embed = discord.Embed(
            title="[Hierarquia] - Patente Revogada",
            description=f"A patente **{role.name}** foi destruída.",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.datetime.utcnow()
        )
        
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if entry.target.id == role.id:
                embed.add_field(name="Autoridade", value=entry.user.mention, inline=False)
                break
                
        await self.send_log(role.guild, embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
