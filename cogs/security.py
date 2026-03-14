import discord
from discord.ext import commands
import datetime
import json
import os
import re

class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_track = {}  # {user_id: [(timestamp, message)]}
        self.join_track = {}     # {guild_id: [timestamps]}
        self.config_file = 'anti_spam_config.json'
        # Regex super agressiva para identificar sites adultos, termos NSFW e hentai, mesmo escondidos em links de redirecionamento (ex: Google)
        self.adult_link_regex = re.compile(r"(https?://[^\s]*(pornhub|xvideos|xnxx|redtube|xhamster|rule34|onlyfans|privacy|nude|hentai|yaoi|yuri|e621|r34|nsfw)[^\s]*)", re.IGNORECASE)
        
        self.ignored_channels = self.load_ignored_channels()
        # Mesma lógica, salva canais que podem enviar links
        self.link_bypass_channels = self.load_link_bypass_channels()
        
        # Sistema Anti-Nuke
        self.nuke_bypassers = self.load_nuke_bypassers()
        self.nuke_track = {} # {guild_id: {user_id: [timestamps]}}
        
        # Palavras proibidas (Filtro Anti-Ofensas / Scams)
        self.blacklisted_words = ["freenitro", "free nitro", "discord.gift/", "nude", "hackear", "trava_zap"]

    def load_ignored_channels(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_ignored_channels(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.ignored_channels, f)

    def load_link_bypass_channels(self):
        link_file = 'anti_link_config.json'
        if os.path.exists(link_file):
            try:
                with open(link_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_link_bypass_channels(self):
        with open('anti_link_config.json', 'w') as f:
            json.dump(self.link_bypass_channels, f)

    def load_nuke_bypassers(self):
        file = 'anti_nuke_config.json'
        if os.path.exists(file):
            try:
                with open(file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_nuke_bypassers(self):
        with open('anti_nuke_config.json', 'w') as f:
            json.dump(self.nuke_bypassers, f)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Ignora se o canal estiver na lista de exceções
        if message.channel.id in self.ignored_channels:
            return

        # Permissões de administrador ignoram os filtros
        if message.author.guild_permissions.manage_messages:
            return

        # --- SISTEMA: FILTRO DE PALAVRAS PROIBIDAS ---
        # Converte a mensagem para minúscula para a verificação
        msg_lower = message.content.lower()
        if any(bad_word in msg_lower for bad_word in self.blacklisted_words):
            try:
                await message.delete()
                warning = await message.channel.send(f"**[FILTRO AUTOMÁTICO]** {message.author.mention}, sua mensagem continha um termo proibido e foi interceptada.", delete_after=6)
                return
            except:
                pass
        # ---------------------------------------------

        # --- SISTEMA: ANTI-LINK (APENAS CONTEÚDO ADULTO) ---
        if self.adult_link_regex.search(message.content):
            if message.channel.id not in self.link_bypass_channels:
                try:
                    await message.delete()
                    await message.channel.send(f"**[BLOQUEIO DE NSFW]** {message.author.mention}, o compartilhamento de links de conteúdo adulto é estritamente proibido.", delete_after=5)
                    return
                except:
                    pass
        # --------------------------

        user_id = message.author.id
        now = datetime.datetime.now()

        if user_id not in self.message_track:
            self.message_track[user_id] = []

        # Adiciona a mensagem atual (timestamp e objeto) e remove os antigos (mais de 5 segundos)
        self.message_track[user_id].append((now, message))
        self.message_track[user_id] = [(t, m) for t, m in self.message_track[user_id] if (now - t).total_seconds() < 5]

        # Se o usuário enviou mais de 5 mensagens em 5 segundos
        if len(self.message_track[user_id]) > 5:
            if len(self.message_track[user_id]) == 6:
                await message.channel.send(f"{message.author.mention}, não exeda a taxa permitida de envio de mensagens.", delete_after=5)
                
                # Apaga todas as mensagens que formaram o ciclo de spam de uma só vez (Bulk Delete)
                messages_to_delete = [m for t, m in self.message_track[user_id]]
                if messages_to_delete:
                    try:
                        await message.channel.delete_messages(messages_to_delete)
                    except discord.HTTPException:
                        # Fallback se as mensagens tiverem mais de 14 dias ou der algum erro
                        for m in messages_to_delete:
                            try:
                                await m.delete()
                            except:
                                pass
            else:
                # Se continuar floodando após o 6º aviso (ainda nos 5 segs), apaga também
                try:
                    await message.delete()
                except:
                    pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        now = datetime.datetime.now()

        if guild_id not in self.join_track:
            self.join_track[guild_id] = []

        # Adiciona o timestamp atual de entrada
        self.join_track[guild_id].append(now)
        
        # Mantém apenas os registros dos últimos 10 segundos
        self.join_track[guild_id] = [t for t in self.join_track[guild_id] if (now - t).total_seconds() < 10]

        # Se mais de 5 pessoas entrarem em 10 segundos, é considerado RAID
        if len(self.join_track[guild_id]) > 5:
            try:
                # Expulsa o membro suspeito
                await member.kick(reason="Anti-Raid: Possível ataque de bots/raid detectado.")
                
                # Procura um canal de logs ou envia no sistema
                log_channel = discord.utils.get(member.guild.text_channels, name="logs")
                if log_channel:
                    await log_channel.send(f"**[ALERTA DE SEGURANÇA]**\nO usuário {member.mention} foi expulso automaticamente devido à entrada massiva de contas (Anti-Raid).")
            except:
                pass
                
        # --- SISTEMA: ANTI-ALT (VERIFICADOR DE IDADE DE CONTA) ---
        # Contas criadas a menos de 7 dias serão colocadas em quarentena (Time Out automático de 1 hora)
        account_age = now.replace(tzinfo=datetime.timezone.utc) - member.created_at
        if account_age.days < 7:
            try:
                # Coloca de castigo por 1 hora
                duration = datetime.timedelta(hours=1)
                await member.timeout(duration, reason="Segurança: Conta criada a menos de 7 dias (Possível Fake/Bot).")
                
                log_channel = discord.utils.get(member.guild.text_channels, name="logs")
                if log_channel:
                    embed = discord.Embed(
                        title="[ALERTA] Conta Suspeita Detectada (ANTI-FAKE)",
                        description=f"{member.mention} entrou no servidor, mas a conta foi criada há apenas **{account_age.days} dias**.",
                        color=discord.Color.gold(),
                        timestamp=datetime.datetime.now()
                    )
                    embed.set_footer(text="Ação: Membro silenciado preventivamente por 1 hora.")
                    await log_channel.send(embed=embed)
            except discord.Forbidden:
                pass
        # ---------------------------------------------------------

    @commands.command(name='antispam_bypass', help='Define um canal para ser ignorado pelo anti-spam.')
    @commands.has_permissions(administrator=True)
    async def antispam_bypass(self, ctx, channel: discord.TextChannel = None):
        """Define ou remove um canal da lista de exceções do anti-spam."""
        channel = channel or ctx.channel
        
        if channel.id in self.ignored_channels:
            self.ignored_channels.remove(channel.id)
            self.save_ignored_channels()
            await ctx.send(f"**[CONFIGURAÇÃO]** O canal {channel.mention} não é mais ignorado pelo módulo anti-spam.")
        else:
            self.ignored_channels.append(channel.id)
            self.save_ignored_channels()
            await ctx.send(f"**[CONFIGURAÇÃO]** O canal {channel.mention} agora será ignorado pelo módulo anti-spam.")

    @commands.command(name='list_bypass', help='Lista os canais ignorados pelo anti-spam.')
    @commands.has_permissions(administrator=True)
    async def list_bypass(self, ctx):
        """Lista todos os canais que estão na lista branca do anti-spam."""
        if not self.ignored_channels:
            return await ctx.send("**[INFORMAÇÃO]** Não há canais configurados como ignorados pelo módulo anti-spam no momento.")
        
        channels_mentions = [f"<#{cid}>" for cid in self.ignored_channels]
        embed = discord.Embed(
            title="[REGISTRO] - CANAIS ISENTOS DE ANTI-SPAM",
            description="\n".join(channels_mentions),
            color=discord.Color.from_rgb(0, 0, 0)
        )
        await ctx.send(embed=embed)

    @commands.command(name='antilink_bypass', help='Define um canal para o anti-link ignorar.')
    @commands.has_permissions(administrator=True)
    async def antilink_bypass(self, ctx, channel: discord.TextChannel = None):
        """Define ou remove um canal da lista de exceções do anti-link."""
        channel = channel or ctx.channel
        
        if channel.id in self.link_bypass_channels:
            self.link_bypass_channels.remove(channel.id)
            self.save_link_bypass_channels()
            await ctx.send(f"**[CONFIGURAÇÃO]** O canal {channel.mention} não está mais isento do módulo anti-link.")
        else:
            self.link_bypass_channels.append(channel.id)
            self.save_link_bypass_channels()
            await ctx.send(f"**[CONFIGURAÇÃO]** O canal {channel.mention} agora está isento do módulo anti-link.")

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        if not entry.guild:
            return
            
        guild = entry.guild
        user = entry.user
        
        # Ignora ações caso não se refira a um usuário, seja o próprio bot ou o dono do servidor
        if not user or user == self.bot.user or user.id == guild.owner_id:
            return
            
        # Ignora se o usuário for confiável e estiver na whitelist de Anti-Nuke
        if user.id in self.nuke_bypassers:
            return
            
        dangerous_actions = [
            discord.AuditLogAction.channel_delete,
            discord.AuditLogAction.channel_create,
            discord.AuditLogAction.role_delete,
            discord.AuditLogAction.role_create,
            discord.AuditLogAction.ban,
            discord.AuditLogAction.kick,
            discord.AuditLogAction.webhook_create,
            discord.AuditLogAction.webhook_delete,
            discord.AuditLogAction.guild_update
        ]
        
        if entry.action not in dangerous_actions:
            return
            
        guild_id = guild.id
        user_id = user.id
        now = datetime.datetime.now()
        
        if guild_id not in self.nuke_track:
            self.nuke_track[guild_id] = {}
            
        if user_id not in self.nuke_track[guild_id]:
            self.nuke_track[guild_id][user_id] = []
            
        self.nuke_track[guild_id][user_id].append(now)
        
        # Limpa registros antigos (mais de 15 segundos)
        self.nuke_track[guild_id][user_id] = [t for t in self.nuke_track[guild_id][user_id] if (now - t).total_seconds() < 15]
        
        # Acima de 4 ações destrutivas em 15 segundos => NUKE detectado
        if len(self.nuke_track[guild_id][user_id]) > 4:
            try:
                await guild.ban(user, reason="Sistema Anti-Nuke Automático: Tentativa detectada de destruir o servidor.")
                
                log_channel = discord.utils.get(guild.text_channels, name="logs")
                if log_channel:
                    embed = discord.Embed(
                        title="[ALERTA DE SEGURANÇA MÁXIMA] - ANTI-NUKE",
                        description=f"O membro **{user.mention}** ({user.id}) foi banido em caráter de emergência do servidor.",
                        color=discord.Color.brand_red(),
                        timestamp=datetime.datetime.now()
                    )
                    embed.add_field(name="Motivo do Bloqueio", value="Atividades como deletar canais, criar cargos perigosos ou banir muitas pessoas simultaneamente foram detectadas.", inline=False)
                    await log_channel.send(f"@everyone **[URGENTE] INVASÃO CONTIDA**", embed=embed)
                    
                # Limpa a contagem para não inundar o log com várias tentativas de banir
                self.nuke_track[guild_id][user_id] = []
            except discord.Forbidden:
                pass

    @commands.command(name='nuke_bypass', help='Libera um usuário das restrições do Anti-Nuke.')
    @commands.has_permissions(administrator=True)
    async def nuke_bypass(self, ctx, membro: discord.Member):
        """Define ou remove um usuário da lista de confiança (ignora o anti-nuke)."""
        if membro.id in self.nuke_bypassers:
            self.nuke_bypassers.remove(membro.id)
            self.save_nuke_bypassers()
            await ctx.send(f"**[SEGURANÇA]** O membro {membro.mention} não possui mais o bypass do Anti-Nuke e será monitorado.")
        else:
            self.nuke_bypassers.append(membro.id)
            self.save_nuke_bypassers()
            await ctx.send(f"**[SEGURANÇA PRIVILEGIADA]** O membro {membro.mention} recebeu o bypass. Suas ações agora serão ignoradas pelo Anti-Nuke.")


    @commands.command(name='list_nuke_bypass', help='Lista usuários livres do Anti-Nuke.')
    @commands.has_permissions(administrator=True)
    async def list_nuke_bypass(self, ctx):
        """Mostra os usuários na whitelist do anti-nuke."""
        if not self.nuke_bypassers:
            return await ctx.send("**[INFORMAÇÃO]** Ninguém está na lista de exceções do Anti-Nuke.")
            
        users_mentions = [f"<@{uid}>" for uid in self.nuke_bypassers]
        embed = discord.Embed(
            title="[REGISTRO] - WHITELIST DO ANTI-NUKE",
            description="\n".join(users_mentions),
            color=discord.Color.from_rgb(0, 0, 0)
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # --- SISTEMA: DETECTOR DE GHOST PING ---
        if message.author.bot or not message.guild:
            return
            
        # Se a mensagem tinha menções a usuários ou cargos e foi deletada
        if message.mentions or message.role_mentions:
            # Não avisamos se ele mencionou a si próprio
            if len(message.mentions) == 1 and message.mentions[0] == message.author:
                return

            embed = discord.Embed(
                title="[DETECTOR] Ghost Ping",
                description=f"O membro **{message.author.mention}** mencionou alguém e apagou a mensagem rapidamente para tentar se esconder.",
                color=discord.Color.dark_magenta(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Mensagem Ocultada:", value=message.content[:1024] or "Conteúdo não encontrado/anexo.", inline=False)
            
            try:
                await message.channel.send(embed=embed)
            except:
                pass

    @commands.command(name='lockdown', help='[CUIDADO] Tranca TODOS os canais do servidor.')
    @commands.has_permissions(administrator=True)
    async def global_lockdown(self, ctx):
        """Bloqueia todos os canais de texto contra membros normais (Protocolo de Pânico)."""
        await ctx.send("**[INICIANDO PROTOCOLO GLOBAL DE LOCKDOWN]**\nSilenciando o servidor, aguarde...")
        locked = 0
        for channel in ctx.guild.text_channels:
            try:
                # Pega a permissão atual de @everyone e define send_messages como False
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                if overwrite.send_messages is not False:
                    overwrite.send_messages = False
                    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
                    locked += 1
            except discord.Forbidden:
                pass

        embed = discord.Embed(
            title="[LOCKDOWN] - GLOBAL ATIVADO",
            description=f"O protocolo de emergência foi ativado. **{locked} canais** foram bloqueados.\nNinguém sem cargo de administração poderá enviar mensagens até o aviso prévio.",
            color=discord.Color.brand_red()
        )
        await ctx.send(embed=embed)

    @commands.command(name='unlockdown', help='Acaba com o lockdown global e destranca tudo.')
    @commands.has_permissions(administrator=True)
    async def global_unlockdown(self, ctx):
        """Desfaz o protocolo de pânico (Restaura os canais globais)."""
        await ctx.send("**[DESATIVANDO PROTOCOLO DE LOCKDOWN]**...\nRestaurando acessos.")
        unlocked = 0
        for channel in ctx.guild.text_channels:
            try:
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                if overwrite.send_messages is False:
                    overwrite.send_messages = None
                    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
                    unlocked += 1
            except discord.Forbidden:
                pass

        embed = discord.Embed(
            title="[LOCKDOWN] - GLOBAL ENCERRADO",
            description=f"O servidor está seguro. **{unlocked} canais** foram destrancados e os membros votaram a ter permissão de fala.",
            color=discord.Color.brand_green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Security(bot))
