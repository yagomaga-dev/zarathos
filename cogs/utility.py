import discord
from discord.ext import commands
from discord.ui import Select, View
import datetime
import time


class HelpSelect(Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(
                label="Administração", 
                description="Comandos de controle e moderação", 
                value="admin"
            ),
            discord.SelectOption(
                label="Utilidades", 
                description="Comandos gerais e informações", 
                value="util"
            ),
            discord.SelectOption(
                label="Segurança", 
                description="Proteção contra spam e ataques", 
                value="security"
            ),
        ]
        super().__init__(placeholder="Selecione uma categoria...", options=options)

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(color=discord.Color.from_rgb(0, 0, 0))
        prefix = self.bot.command_prefix

        if self.values[0] == "admin":
            embed.title = "[Manual] - Comandos De Administração"
            
            admin_list = (
                "• `[]` = Obrigatório / `()` = Opcional\n\n"
                f"➥ **{prefix}logs set [#canal]**:\n"
                "  ◦ Configura onde os logs serão enviados.\n"
                f"➥ **{prefix}clear [n]**:\n"
                "  ◦ Apaga uma quantidade específica de mensagens.\n"
                f"➥ **{prefix}kick [@user] (motivo)**:\n"
                "  ◦ Expulsa um membro infrator do servidor.\n"
                f"➥ **{prefix}ban [@user] (motivo)**:\n"
                "  ◦ Bane permanentemente um membro do servidor.\n"
                f"➥ **{prefix}ipban [@user] (motivo)**:\n"
                "  ◦ Bane o membro e seu IP (limpa 7 dias de chat).\n"
                f"➥ **{prefix}mute [@user] (motivo)**:\n"
                "  ◦ Silencia um usuário (timeout de 28 dias).\n"
                f"➥ **{prefix}unmute [@user]**:\n"
                "  ◦ Remove o silêncio de um usuário.\n"
                f"➥ **{prefix}timeout [@user] [min] (motivo)**:\n"
                "  ◦ Aplica um castigo temporário em minutos.\n"
                f"➥ **{prefix}warn [@user] (motivo)**:\n"
                "  ◦ Aplica um aviso formal a um membro.\n"
                f"➥ **{prefix}unwarn [@user]**:\n"
                "  ◦ Remove o último aviso de um usuário.\n"
                f"➥ **{prefix}warnings [@user]**:\n"
                "  ◦ Mostra o histórico de avisos de um membro.\n"
                f"➥ **{prefix}unban [Id] (motivo)**:\n"
                "  ◦ Desbane um usuário do servidor pelo ID.\n"
                f"➥ **{prefix}slowmode [segundos]**:\n"
                "  ◦ Define o tempo de espera no canal atual.\n"
                f"➥ **{prefix}lock**:\n"
                "  ◦ Tranca o canal para que ninguém envie mensagens.\n"
                f"➥ **{prefix}unlock**:\n"
                "  ◦ Destranca o canal para o público.\n"
                f"➥ **{prefix}massban [@user1] [@user2]...**:\n"
                "  ◦ Bane múltiplos usuários de uma só vez.\n"
                f"➥ **{prefix}nuke**:\n"
                "  ◦ Apaga e clona o canal atual limpando as mensagens.\n"
                f"➥ **{prefix}muteall**:\n"
                "  ◦ Muta todos os usuários no seu canal de voz atual.\n"
                f"➥ **{prefix}unmuteall**:\n"
                "  ◦ Desmuta todos que estão na sua call atual.\n"
                f"➥ **{prefix}roleall [@cargo]**:\n"
                "  ◦ Dá um cargo para Todos Os Membros (demorado).\n"
                f"➥ **{prefix}dc_all [ID_do_canal]**:\n"
                "  ◦ Derruba à força todos de um canal de voz pelo ID dele."
            )
            embed.description = admin_list

        elif self.values[0] == "util":
            embed.title = "[Manual] - Comandos De Utilidade"
            
            util_list = (
                "• `[]` = Obrigatório / `()` = Opcional\n\n"
                f"➥ **{prefix}ping**:\n"
                "  ◦ Mostra a minha latência atual com o servidor.\n"
                f"➥ **{prefix}avatar (@user)**:\n"
                "  ◦ Mostra a foto de perfil de um usuário.\n"
                f"➥ **{prefix}banner (@user)**:\n"
                "  ◦ Mostra o banner de perfil de um usuário.\n"
                f"➥ **{prefix}userinfo (@user)**:\n"
                "  ◦ Exibe informações detalhadas de um membro.\n"
                f"➥ **{prefix}serverinfo**:\n"
                "  ◦ Exibe informações detalhadas do servidor.\n"
                f"➥ **{prefix}servericon**:\n"
                "  ◦ Mostra o ícone deste servidor.\n"
                f"➥ **{prefix}membercount**:\n"
                "  ◦ Mostra a quantidade de membros no servidor.\n"
                f"➥ **{prefix}uptime**:\n"
                "  ◦ Mostra há quanto tempo estou online.\n"
                f"➥ **{prefix}poll [pergunta]**:\n"
                "  ◦ Cria uma votação simples com Sim/Não.\n"
                f"➥ **{prefix}invite**:\n"
                "  ◦ Envia o meu link de convite.\n"
                f"➥ **{prefix}botinfo**:\n"
                "  ◦ Exibe informações técnicas sobre mim.\n"
                f"➥ **{prefix}roles**:\n"
                "  ◦ Lista todos os cargos do servidor.\n"
                f"➥ **{prefix}say [mensagem]**:\n"
                "  ◦ Faz o bot repetir a mensagem digitada.\n"
                f"➥ **{prefix}help**:\n"
                "  ◦ Mostra este menu interativo de ajuda."
            )
            embed.description = util_list

        elif self.values[0] == "security":
            embed.title = "[Manual] - Comandos De Segurança"
            
            security_list = (
                "• `[]` = Obrigatório / `()` = Opcional\n\n"
                f"➥ **{prefix}antispam_bypass (#canal)**:\n"
                "  ◦ Adiciona ou remove um canal da exceção do anti-spam.\n"
                f"➥ **{prefix}list_bypass**:\n"
                "  ◦ Lista todos os canais que ignoram o anti-spam.\n"
                f"➥ **{prefix}antilink_bypass (#canal)**:\n"
                "  ◦ Adiciona ou remove um canal da exceção do bloqueio de links."
            )
            embed.description = security_list

        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text=f"Comando executado por: {interaction.user}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(View):
    def __init__(self, bot):
        super().__init__(timeout=120)  # O menu expira após 2 minutos
        self.add_item(HelpSelect(bot))

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    async def help(self, ctx):
        """Mostra o menu interativo de ajuda."""
        embed = discord.Embed(
            title="Central De Comandos Zarathos",
            description=(
                "Assistente de moderação e controle estabelecido.\n"
                "Selecione uma das categorias no menu abaixo para acessar os comandos correspondentes."
            ),
            color=discord.Color.from_rgb(0, 0, 0)
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text=f"Prefixo configurado: {ctx.prefix}")
        
        view = HelpView(self.bot)
        await ctx.send(embed=embed, view=view)

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Verifica a latência do bot."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"**[Status]** Conexão estável. Latência: {latency}ms")

    @commands.command(name='avatar')
    async def avatar(self, ctx, member: discord.Member = None):
        """Mostra o avatar de um membro."""
        member = member or ctx.author
        embed = discord.Embed(title=f"[Imagem] - AVATAR: {member.name}", color=discord.Color.from_rgb(0, 0, 0))
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='userinfo', aliases=['ui', 'user'])
    async def userinfo(self, ctx, member: discord.Member = None):
        """Mostra informações de um membro."""
        member = member or ctx.author
        roles = [role.mention for role in member.roles[1:]] # Exclui o @everyone
        
        embed = discord.Embed(title=f"[Arquivo] - PERFIL: {member.name}", color=discord.Color.from_rgb(0, 0, 0))
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Tag", value=f"`{member}`", inline=True)
        embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="Conta Criada", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="Entrou no Servidor", value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name=f"Cargos ({len(roles)})", value=" ".join(roles) if roles else "Nenhum", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='serverinfo', aliases=['si', 'server'])
    async def serverinfo(self, ctx):
        """Mostra informações do servidor."""
        guild = ctx.guild
        embed = discord.Embed(title=f"[Arquivo] - Dados Do Servidor: {guild.name}", color=discord.Color.from_rgb(0, 0, 0))
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="Dono", value=f"{guild.owner.mention}", inline=True)
        embed.add_field(name="ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="Membros", value=f"{guild.member_count}", inline=True)
        embed.add_field(name="Canais", value=f"Total: {len(guild.channels)}", inline=True)
        embed.add_field(name="Cargos", value=f"{len(guild.roles)}", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='say')
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, message):
        """O bot repete a mensagem enviada."""
        await ctx.message.delete()
        await ctx.send(message)

    @commands.command(name='banner')
    async def banner(self, ctx, member: discord.Member = None):
        """Mostra o banner de um membro."""
        member = member or ctx.author
        
        # É necessário buscar o usuário para obter o banner
        user = await self.bot.fetch_user(member.id)
        
        if not user.banner:
            return await ctx.send(f"**[Aviso]** O membro {member.name} não possui um banner configurado.")
            
        embed = discord.Embed(title=f"[Imagem] - BANNER: {member.name}", color=discord.Color.from_rgb(0, 0, 0))
        embed.set_image(url=user.banner.url)
        await ctx.send(embed=embed)

    @commands.command(name='uptime')
    async def uptime(self, ctx):
        """Mostra há quanto tempo o bot está online."""
        now = datetime.datetime.now(datetime.timezone.utc)
        uptime_delta = now - self.bot.start_time
        
        hours, remainder = divmod(int(uptime_delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        embed = discord.Embed(
            title="[Status] - Uptime Do Sistema",
            description=f"O sistema está operando continuamente por:\n**{uptime_str}**",
            color=discord.Color.from_rgb(0, 0, 0)
        )
        await ctx.send(embed=embed)

    @commands.command(name='servericon', aliases=['icon', 'si_icon'])
    async def servericon(self, ctx):
        """Mostra o ícone do servidor."""
        if not ctx.guild.icon:
            return await ctx.send("**[Aviso]** Este servidor não possui um ícone configurado.")
            
        embed = discord.Embed(title=f"[Imagem] - Ícone Do Servidor", color=discord.Color.from_rgb(0, 0, 0))
        embed.set_image(url=ctx.guild.icon.url)
        await ctx.send(embed=embed)

    @commands.command(name='membercount', aliases=['mc'])
    async def membercount(self, ctx):
        """Mostra a contagem de membros do servidor."""
        guild = ctx.guild
        total = guild.member_count
        # Contagem simplificada de bots vs humanos (requer intents de membros)
        bots = sum(1 for member in guild.members if member.bot)
        humans = total - bots
        
        embed = discord.Embed(title=f"[Estatísticas] - POPULAÇÃO", color=discord.Color.from_rgb(0, 0, 0))
        embed.add_field(name="Total", value=f"`{total}`", inline=True)
        embed.add_field(name="Humanos", value=f"`{humans}`", inline=True)
        embed.add_field(name="Bots", value=f"`{bots}`", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='poll')
    async def poll(self, ctx, *, question):
        """Cria uma votação simples."""
        embed = discord.Embed(
            title="[Votação] - Avaliação De Conselho",
            description=question,
            color=discord.Color.from_rgb(0, 0, 0)
        )
        embed.set_footer(text=f"Proposto por: {ctx.author.name}")
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("V")
        await msg.add_reaction("X")

    @commands.command(name='invite')
    async def invite(self, ctx):
        """Envia o link de convite do bot."""
        invite_link = discord.utils.oauth_url(self.bot.user.id, permissions=discord.Permissions(8))
        
        embed = discord.Embed(
            title="[Conectividade] - Link De Convite",
            description=f"Acesso ao protocolo de inclusão do sistema em novos diretórios:\n\n[Iniciar Conexão]({invite_link})",
            color=discord.Color.from_rgb(0, 0, 0)
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='botinfo', aliases=['bi', 'info'])
    async def botinfo(self, ctx):
        """Exibe informações sobre o bot."""
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        total_guilds = len(self.bot.guilds)
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(title="Informações Técnicas", color=discord.Color.from_rgb(0, 0, 0))
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        embed.add_field(name="Proprietário", value="`Yago`", inline=True) # Você pode ajustar conforme desejar
        embed.add_field(name="Linguagem", value="`Python (discord.py)`", inline=True)
        embed.add_field(name="Servidores", value=f"`{total_guilds}`", inline=True)
        embed.add_field(name="Usuários", value=f"`{total_members}`", inline=True)
        embed.add_field(name="Latência", value=f"`{latency}ms`", inline=True)
        embed.add_field(name="Prefixo", value=f"`{self.bot.command_prefix}`", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='roles')
    async def roles(self, ctx):
        """Lista todos os cargos do servidor."""
        roles = [role.mention for role in reversed(ctx.guild.roles) if role != ctx.guild.default_role]
        
        if not roles:
            return await ctx.send("Este servidor não possui cargos criados.")
            
        # Divide em chunks caso haja muitos cargos (limite de 1024 caracteres em campos de embed)
        roles_str = ", ".join(roles)
        if len(roles_str) > 1000:
            roles_str = roles_str[:997] + "..."
            
        embed = discord.Embed(
            title=f"[Dados] - Relação De Cargos",
            description=roles_str,
            color=discord.Color.from_rgb(0, 0, 0)
        )
        embed.set_footer(text=f"Total: {len(roles)} cargos")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignora se for o próprio bot ou se não houver menção ao bot
        if message.author.bot:
            return

        if self.bot.user in message.mentions:
            # Verifica se quem mencionou é o dono do bot
            if await self.bot.is_owner(message.author):
                embed = discord.Embed(
                    title="Central De Comandos Zarathos",
                    description=(
                        "Assistente de moderação e controle estabelecido.\n"
                        "Selecione uma das categorias no menu abaixo para acessar os comandos correspondentes."
                    ),
                    color=discord.Color.from_rgb(0, 0, 0)
                )
                
                embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user.avatar else None)
                embed.set_footer(text=f"Prefixo configurado: {self.bot.command_prefix}")
                
                view = HelpView(self.bot)
                await message.reply(embed=embed, view=view)

    @commands.command(name='remover_emoji', aliases=['del', 'delemoji', 'del_emoji'])
    @commands.has_permissions(manage_emojis=True)
    async def remover_emoji(self, ctx, emoji: discord.Emoji):
        """Remove um emoji do servidor enviando o próprio emoji no chat."""
        try:
            await emoji.delete(reason=f"Comando executado por {ctx.author.name}")
            await ctx.send(f"O emoji `:{emoji.name}:` foi deletado com sucesso do servidor.")
        except discord.Forbidden:
            await ctx.send("**[Erro]** O bot não possui permissão para gerenciar/deletar emojis.")
        except discord.HTTPException:
            await ctx.send("**[Falha Interna]** Ocorreu um erro ao tentar deletar o emoji.")

async def setup(bot):
    await bot.add_cog(Utility(bot))
