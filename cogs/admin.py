import discord
from discord.ext import commands
import datetime
import asyncio
class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='clear', help='Limpa mensagens do chat.')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Apaga uma quantidade específica de mensagens."""
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f'Foram apagadas {amount} mensagens deste canal.', delete_after=5)

    @commands.command(name='kick', help='Expulsa um membro do servidor.')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Expulsa um membro informando o motivo."""
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="Membro Expulso",
            description=f"O usuário **{member.name}** foi expulso.",
            color=discord.Color.orange(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Motivo", value=reason or "Não informado")
        embed.set_footer(text=f"Executado por {ctx.author}")
        await ctx.send(embed=embed)

    @commands.command(name='ban', help='Bane um membro do servidor.')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Bane um membro informando o motivo."""
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="[Registro] - BANIMENTO",
            description=f"O membro **{member.name}** teve seu acesso revogado permanentemente.",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Motivo", value=reason or "Não informado")
        embed.set_footer(text=f"Executado por {ctx.author}")
        await ctx.send(embed=embed)

    @commands.command(name='ipban', aliases=['banip'], help='Bane um membro pelo IP (todos os IPs da conta).')
    @commands.has_permissions(ban_members=True)
    async def ipban(self, ctx, member: discord.Member, *, reason=None):
        """Bane um membro e todas as contas ligadas ao mesmo IP."""
        # delete_message_days=7 limpa as mensagens da última semana do usuário banido
        await member.ban(reason=f"IP BAN: {reason or 'Não informado'}", delete_message_days=7)
        
        embed = discord.Embed(
            title="[Registro] - Banimento Global (IP)",
            description=f"O membro **{member.mention}** teve sua conexão e acesso bloqueados.",
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Alvo", value=f"{member.name} (ID: {member.id})")
        embed.add_field(name="Motivo", value=reason or "Não informado")
        embed.add_field(name="Ação", value="Mensagens dos últimos 7 dias foram removidas.")
        embed.set_footer(text=f"Sentenciado por {ctx.author}")
        
        await ctx.send(embed=embed)

    @commands.command(name='unban', help='Desbane um membro do servidor pelo ID.')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, usuario_id: int, *, reason=None):
        """Desbane um membro informando o ID."""
        try:
            user = await self.bot.fetch_user(usuario_id)
            await ctx.guild.unban(user, reason=reason)
            
            embed = discord.Embed(
                title="Membro Desbanido",
                description=f"O usuário **{user.name}** foi desbanido e pode retornar ao servidor.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            embed.add_field(name="Motivo", value=reason or "Não informado")
            embed.set_footer(text=f"Executado por {ctx.author}")
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("Usuário não encontrado na lista de banidos.")
        except discord.Forbidden:
            await ctx.send("**[Erro]** Permissões insuficientes para remover o banimento deste usuário.")
        except Exception as e:
            await ctx.send(f"**[Erro Interno]** Falha na operação: {e}")


    @commands.command(name='timeout', help='Aplica castigo em um membro.')
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, minutes: int, *, reason=None):
        """Aplica um silenciamento temporário no usuário."""
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(f"O membro {member.name} teve sua comunicação restrita por {minutes} minutos. Motivo: {reason or 'Não informado'}")

    @commands.command(name='untimeout', help='Remove o castigo de um membro.')
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        """Remove o silenciamento de um usuário."""
        await member.timeout(None)
        await ctx.send(f"Restrição de comunicação removida para {member.name}.")

    # --- Novos comandos de Mute/Warn ---

    @commands.command(name='mute', help='Silencia um membro indefinidamente.')
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        """Silencia um membro usando o sistema de Time Out (28 dias)."""
        # O Discord não tem mais um 'Mute' nativo por cargo que funcione tão bem quanto o Timeout
        # Aplicamos o tempo máximo permitido (28 dias) para simular um mute "infinito"
        duration = datetime.timedelta(days=28)
        await member.timeout(duration, reason=reason)
        await ctx.send(f"**[Mute]** O membro {member.name} foi silenciado. Motivo: {reason or 'Não informado'}")

    @commands.command(name='unmute', help='Remove o silêncio de um membro.')
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """Remove o silenciamento de um usuário."""
        await member.timeout(None)
        await ctx.send(f"**[Unmute]** O membro {member.name} agora pode falar novamente.")

    # Sistema simples de warns em memória (Atenção: reinicia se o bot desligar)
    # Em uma versão futura, usaremos um banco de dados para isso.
    warns = {}

    @commands.command(name='warn', help='Dá um aviso a um membro.')
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """Dá um aviso ao membro e registra no histórico."""
        guild_id = ctx.guild.id
        member_id = member.id
        
        if guild_id not in self.warns:
            self.warns[guild_id] = {}
        if member_id not in self.warns[guild_id]:
            self.warns[guild_id][member_id] = []
            
        self.warns[guild_id][member_id].append({
            'reason': reason or "Não informado",
            'author': ctx.author.name,
            'date': datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        })
        
        count = len(self.warns[guild_id][member_id])
        await ctx.send(f"**[Advertência]** O membro {member.name} recebeu uma infração. (Total: {count})\nMotivo: {reason or 'Não informado'}")

    @commands.command(name='warnings', help='Mostra os avisos de um membro.')
    async def warnings(self, ctx, member: discord.Member):
        """Lista todos os avisos de um usuário."""
        guild_id = ctx.guild.id
        member_id = member.id
        
        if guild_id not in self.warns or member_id not in self.warns[guild_id] or not self.warns[guild_id][member_id]:
            return await ctx.send(f"O membro {member.name} possui histórico limpo.")
            
        embed = discord.Embed(title=f"[Registro] - INFRAÇÕES: {member.name}", color=discord.Color.from_rgb(0, 0, 0))
        for i, warn in enumerate(self.warns[guild_id][member_id], 1):
            embed.add_field(
                name=f"Infração {i}", 
                value=f"Motivo: {warn['reason']}\nResponsável: {warn['author']}\nData: {warn['date']}", 
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name='unwarn', help='Remove o último aviso de um membro.')
    @commands.has_permissions(moderate_members=True)
    async def unwarn(self, ctx, member: discord.Member):
        """Remove o último aviso registrado de um usuário."""
        guild_id = ctx.guild.id
        member_id = member.id
        
        if guild_id in self.warns and member_id in self.warns[guild_id] and self.warns[guild_id][member_id]:
            self.warns[guild_id][member_id].pop()
            await ctx.send(f"A última infração de {member.name} foi removida dos registros.")
        else:
            await ctx.send(f"**[Erro]** O membro {member.name} não possui infrações registradas.")

    @commands.command(name='slowmode', help='Define o modo lento do canal.')
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        """Altera o tempo de espera entre mensagens no canal."""
        await ctx.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send("**[Controle]** O restritor de velocidade foi desativado neste canal.")
        else:
            await ctx.send(f"**[Controle]** O restritor de velocidade foi ativado para {seconds} segundos.")

    @commands.command(name='lock', help='Tranca o canal para membros.')
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """Impede que membros enviem mensagens no canal."""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("**[Segurança]** O canal encontra-se sob bloqueio de comunicações (Trancado).")

    @commands.command(name='unlock', help='Destranca o canal para membros.')
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """Permite que membros enviem mensagens no canal novamente."""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("**[Segurança]** O bloqueio de comunicações foi encerrado (Destrancado).")

    # --- Comandos Avançados De Segurança E ADMINISTRAÇÃO ---
    
    @commands.command(name='massban', help='Bane várias pessoas de uma vez pelo ID.')
    @commands.has_permissions(administrator=True)
    async def massban(self, ctx, *members: discord.Member):
        """Bane múltiplos usuários simultaneamente (Requer permissão de Admin)."""
        if not members:
            return await ctx.send("**[Erro De Sintaxe]** Você precisa mencionar ou colocar a ID dos usuários que deseja banir em massa.")
            
        banned = 0
        failed = 0
        
        await ctx.send("**[Sistema]** Iniciando protocolo de banimento em massa. Aguarde...")
        for member in members:
            try:
                await member.ban(reason=f"Massban executado por {ctx.author}")
                banned += 1
            except:
                failed += 1
                
        await ctx.send(f"**[Relatório De Massban]**\nSucesso: {banned} banidos.\nFalhas: {failed} não puderam ser banidos.")

    @commands.command(name='nuke', help='Clona e apaga o canal atual, limpando-o por completo.')
    @commands.has_permissions(manage_channels=True)
    async def nuke(self, ctx):
        """Destrói o canal atual e cria uma cópia exata limpa."""
        channel = ctx.channel
        pos = channel.position
        
        novo_canal = await channel.clone(reason=f"Nuke solicitado por {ctx.author}")
        await novo_canal.edit(position=pos)
        await channel.delete()
        
        embed = discord.Embed(
            title="[Diretório Purificado]",
            description="Este canal foi recriado com sucesso. Todo o histórico anterior foi obliterado.",
            color=discord.Color.from_rgb(0, 0, 0)
        )
        embed.set_image(url="https://media.giphy.com/media/HhTXt43pk1I1W/giphy.gif")
        await novo_canal.send(embed=embed)

    @commands.command(name='muteall', help='Silencia todos os membros em um canal de voz.')
    @commands.has_permissions(mute_members=True)
    async def muteall(self, ctx):
        """Muta o microfone de todos os usuários que estão no mesmo canal de voz que você."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("**[Erro]** Você precisa estar em um canal de voz para usar isso.")
            
        channel = ctx.author.voice.channel
        muted = 0
        for member in channel.members:
            if not member.bot and member != ctx.author:
                try:
                    await member.edit(mute=True)
                    muted += 1
                except:
                    pass
        await ctx.send(f"**[Controle De Voz]** Foram silenciados {muted} membros no canal {channel.name}.")

    @commands.command(name='unmuteall', help='Desmuta todos os membros em um canal de voz.')
    @commands.has_permissions(mute_members=True)
    async def unmuteall(self, ctx):
        """Devolve a voz de todos os usuários que estão no mesmo canal de voz que você."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("**[Erro]** Você precisa estar em um canal de voz para usar isso.")
            
        channel = ctx.author.voice.channel
        unmuted = 0
        for member in channel.members:
            if not member.bot:
                try:
                    await member.edit(mute=False)
                    unmuted += 1
                except:
                    pass
        await ctx.send(f"**[Controle De Voz]** A voz foi devolvida para {unmuted} membros no canal {channel.name}.")

    @commands.command(name='roleall', help='Dá um cargo para todos do servidor ao mesmo tempo (CUIDADO!).')
    @commands.has_permissions(administrator=True)
    async def roleall(self, ctx, role: discord.Role):
        """Aplica o cargo especificado em todos os membros humanos do servidor."""
        await ctx.send(f"**[Sistema]** Iniciando distribuição em massa do cargo {role.name}. Isso pode demorar vários minutos.")
        
        success = 0
        for member in ctx.guild.members:
            if not member.bot and role not in member.roles:
                try:
                    await member.add_roles(role)
                    success += 1
                    # Atraso mínimo para evitar tomar bloqueio por Rate Limit do Discord
                    await asyncio.sleep(1) 
                except:
                    pass
                    
        await ctx.send(f"**[Relatório]** A distribuição foi concluída. O cargo foi entregue a {success} membros.")

    @commands.command(name='disconnectall', aliases=['dc_all', 'derrubar'], help='Desconecta todos os usuários de um canal de voz.')
    @commands.has_permissions(administrator=True)
    async def disconnectall(self, ctx, canal_voz: discord.VoiceChannel):
        """Desconecta à força todos os membros que estiverem em um canal de voz específico."""
            
        if not canal_voz.members:
            return await ctx.send(f"O canal `{canal_voz.name}` já está vazio.")
            
        await ctx.send(f"**[Controle De Voz]** Iniciando a desconexão forçada na sala `{canal_voz.name}`...")
        
        desconectados = 0
        for member in canal_voz.members:
            try:
                await member.move_to(None) # Enviar para "None" joga o usuário para fora da call
                desconectados += 1
            except:
                pass
                
        await ctx.send(f"**[Relatório De Voz]** Operação concluída. {desconectados} membros foram chutados da chamada.")

    # Tratamento de erros para comandos de administração
    @clear.error
    @kick.error
    @ban.error
    @timeout.error
    @mute.error
    @warn.error
    @unwarn.error
    @unban.error
    @slowmode.error
    @lock.error
    @unlock.error
    @massban.error
    @nuke.error
    @muteall.error
    @unmuteall.error
    @roleall.error
    @disconnectall.error
    async def admin_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("**[Acesso Negado]** Requisitos de permissão não atingidos.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("**[Erro De Sintaxe]** Parâmetros ausentes. Consulte as instruções operacionais adequadas.")
        elif isinstance(error, (commands.BotMissingPermissions, discord.Forbidden)):
            await ctx.send("**[Falha No Sistema]** Nível de permissão operacional insuficiente. Eleve a hierarquia do cargo.")
        elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.Forbidden):
            await ctx.send("**[Falha No Sistema]** Nível de permissão operacional insuficiente. Eleve a hierarquia do cargo.")
        else:
            await ctx.send(f"**[Relatório De Falha]** Anomalia detectada: {error}")

async def setup(bot):
    await bot.add_cog(Admin(bot))
