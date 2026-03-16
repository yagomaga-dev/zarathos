import discord
from discord.ext import commands
import random
import datetime
from dotenv import load_dotenv
import os
import pymongo
from discord import ui

# Tentativa de carregar o .env para ambientes locais
load_dotenv()

class ShopSelect(ui.Select):
    def __init__(self, economy_cog):
        self.economy_cog = economy_cog
        options = [
            discord.SelectOption(label="VIP Surface", description="25.000 ZE | 30 dias de vantagens", value="1"),
            discord.SelectOption(label="VIP Kraken", description="45.000 ZE | 40 dias de vantagens", value="2"),
            discord.SelectOption(label="VIP Leviathan", description="80.000 ZE | 50 dias de vantagens", value="3"),
        ]
        super().__init__(
            placeholder="Selecione um VIP para ver detalhes...",
            min_values=1,
            max_values=1,
            options=options,
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        vips = {
            "1": {"nome": "Vip Surface", "preco": 25000, "duracao": "30 dias", "desc": "Cargo exclusivo, nick livre, imagens em canais restritos."},
            "2": {"nome": "Vip Kraken", "preco": 45000, "duracao": "40 dias", "desc": "Tudo anterior + Cargo destaque, cargo personalizado, áudios/sons."},
            "3": {"nome": "Vip Leviathan", "preco": 80000, "duracao": "50 dias", "desc": "Tudo anterior + Área VIP, mini VIP, privilégios máximos."}
        }
        
        vip = vips[self.values[0]]
        embed = discord.Embed(
            title=f"Detalhes: {vip['nome']}",
            description=(
                f"**Preço:** `{vip['preco']:,} ZE`\n"
                f"**Duração:** `{vip['duracao']}`\n\n"
                f"**Benefícios:**\n{vip['desc']}\n\n"
                "Para comprar, use o comando: `z.comprar " + self.values[0] + "`"
            ),
            color=discord.Color.dark_purple()
        )
        embed.set_footer(text="Confirme se possui saldo suficiente antes de comprar.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ShopView(ui.View):
    def __init__(self, economy_cog):
        super().__init__(timeout=None)
        self.economy_cog = economy_cog
        self.add_item(ShopSelect(economy_cog))

    @ui.button(label="Comprar", style=discord.ButtonStyle.grey)
    async def buy_something(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("Use o seletor abaixo para escolher o que deseja comprar!", ephemeral=True)

    @ui.button(label="Converter", style=discord.ButtonStyle.grey)
    async def convert(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        user_data = self.economy_cog.get_user_data(user_id)
        
        if not user_data:
            return await interaction.response.send_message("Não encontrei seus dados no sistema.", ephemeral=True)
            
        msgs = user_data.get("msg_count", 0)
        
        if msgs < 1:
            return await interaction.response.send_message("Você não tem mensagens acumuladas para converter ainda. Converse mais no chat!", ephemeral=True)
            
        # 1000 msgs = 3500 ZE -> Taxa de 3.5 ZE por mensagem
        reward = int(msgs * 3.5)
        
        if reward > 0:
            # Adiciona o saldo e reseta o contador de mensagens
            self.economy_cog.update_balance(user_id, reward, "wallet")
            self.economy_cog.collection.update_one({"_id": user_id}, {"$set": {"msg_count": 0}})
            
            await interaction.response.send_message(
                f"| **Conversão Concluída!**\n"
                f"Você converteu **{msgs:,} mensagens** em **{reward:,} ZE**.\n"
                f"Seu saldo foi atualizado!", ephemeral=True
            )
        else:
            await interaction.response.send_message("Você precisa de pelo menos uma mensagem para converter.", ephemeral=True)

    @ui.button(label="Meu Saldo", style=discord.ButtonStyle.grey)
    async def my_balance(self, interaction: discord.Interaction, button: ui.Button):
        user_data = self.economy_cog.get_user_data(interaction.user.id)
        if user_data:
            wallet = user_data.get("balance", 0)
            bank = user_data.get("bank", 0)
            await interaction.response.send_message(
                f"| **Seu Saldo:**\n"
                f"Carteira: `{wallet:,} ZE`\n"
                f"Banco: `{bank:,} ZE`\n"
                f"Total: `{wallet + bank:,} ZE`", ephemeral=True
            )
        else:
            await interaction.response.send_message("Não consegui encontrar seus dados financeiros.", ephemeral=True)

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.collection = None
        self.error_msg = None
        self.connect_db()
        
        # Rastreamento de voz na memória
        self.voice_tracking = {}

    def connect_db(self):
        """Tenta estabelecer conexão com o MongoDB."""
        url = os.getenv("MONGO_URL")
        if not url:
            self.error_msg = "A variável 'MONGO_URL' não foi encontrada nas configurações (Environment Variables)."
            self.collection = None
            return

        try:
            cluster = pymongo.MongoClient(url, serverSelectionTimeoutMS=5000)
            # Testa a conexão
            cluster.admin.command('ping')
            db = cluster["zarathos_db"]
            self.collection = db["economy"]
            self.error_msg = None
            print("[SISTEMA] Conectado ao MongoDB Atlas com sucesso.")
        except Exception as e:
            self.error_msg = f"Falha ao conectar ao banco de dados: {str(e)}"
            self.collection = None
            print(f"[ERRO] {self.error_msg}")

    def get_user_data(self, user_id):
        """Retorna os dados do usuário ou cria se não existir."""
        if self.collection is None:
            # Tenta reconectar uma vez se estiver nulo
            self.connect_db()
            if self.collection is None:
                return None
            
        user_id = str(user_id)
        data = self.collection.find_one({"_id": user_id})
        
        if not data:
            data = {
                "_id": user_id,
                "balance": 0,
                "bank": 0,
                "msg_count": 0,
                "xp": 0,
                "level": 1
            }
            self.collection.insert_one(data)
        return data

    def add_xp(self, user_id, amount, guild=None, member=None):
        """Adiciona XP ao usuário e verifica se subiu de nível."""
        user_data = self.get_user_data(user_id)
        if not user_data: return
        
        current_xp = user_data.get("xp", 0)
        current_level = user_data.get("level", 1)
        
        new_xp = current_xp + amount
        # Fórmula simples: cada nível precisa de (level * 500) de XP
        xp_needed = current_level * 500
        
        if new_xp >= xp_needed:
            new_level = current_level + 1
            new_xp -= xp_needed
            self.collection.update_one(
                {"_id": str(user_id)},
                {"$set": {"xp": new_xp, "level": new_level}}
            )
            return True, new_level
        else:
            self.collection.update_one(
                {"_id": str(user_id)},
                {"$set": {"xp": new_xp}}
            )
            return False, current_level

    def get_xp_multiplier(self, member):
        """Retorna o multiplicador de XP baseado no cargo VIP."""
        if not member or isinstance(member, discord.User):
            return 1.0
            
        roles_names = [r.name for r in member.roles]
        if "Vip Leviathan" in roles_names:
            return 2.0
        elif "Vip Kraken" in roles_names:
            return 1.5
        elif "Vip Surface" in roles_names:
            return 1.2
        return 1.0

    def update_balance(self, user_id, amount, mode="wallet"):
        """Atualiza o saldo do usuário (carteira ou banco)."""
        if self.collection is None: return
        
        user_id = str(user_id)
        field = "balance" if mode == "wallet" else "bank"
        self.collection.update_one({"_id": user_id}, {"$inc": {field: amount}})


    @commands.command(name="money", aliases=["saldo", "bal", "atm", "wallet", "carteira"])
    async def balance(self, ctx, member: discord.Member = None):
        """Verifica o saldo de um membro."""
        if self.collection is None:
            return await ctx.send(f"**[Erro]** O sistema de economia está offline. Motivo: `{self.error_msg or 'Conexão indisponível'}`")
        
        member = member or ctx.author
        user_data = self.get_user_data(member.id)
        
        wallet = user_data["balance"]
        bank = user_data["bank"]
        total = wallet + bank

        embed = discord.Embed(
            title=f"Finanças de {member.display_name}",
            color=discord.Color.dark_purple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="Carteira", value=f"`{wallet:,} ZE`", inline=True)
        embed.add_field(name="Banco", value=f"`{bank:,} ZE`", inline=True)
        embed.add_field(name="Total", value=f"`{total:,} ZE`", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)


    @commands.command(name="depositar", aliases=["dep", "deposito"])
    async def deposit(self, ctx, amount):
        """Guarda moedas no banco para segurança."""
        if self.collection is None:
            return await ctx.send("**[Erro]** Sistema offline. Tente novamente em instantes.")

        user_data = self.get_user_data(ctx.author.id)
        wallet = user_data["balance"]

        if amount.lower() == "all":
            amount = wallet
        else:
            try:
                amount = int(amount)
            except ValueError:
                return await ctx.send("**[Erro]** Informe um valor numérico válido ou `all`.")

        if amount <= 0:
            return await ctx.send("**[Erro]** Você não pode depositar valores negativos ou zero.")
        
        if amount > wallet:
            return await ctx.send("**[Erro]** Você não tem essa quantia na carteira.")

        self.update_balance(ctx.author.id, -amount, "wallet")
        self.update_balance(ctx.author.id, amount, "bank")

        await ctx.send(f"| Você guardou **{amount:,} ZE** no cofre do Banco!")

    @commands.command(name="sacar", aliases=["withdraw", "with"])
    async def withdraw(self, ctx, amount):
        """Saca moedas do banco para a carteira."""
        if self.collection is None:
            return await ctx.send("**[Erro]** Sistema offline. Tente novamente em instantes.")

        user_data = self.get_user_data(ctx.author.id)
        bank = user_data["bank"]

        if amount.lower() == "all":
            amount = bank
        else:
            try:
                amount = int(amount)
            except ValueError:
                return await ctx.send("**[Erro]** Valor inválido.")

        if amount <= 0:
            return await ctx.send("**[Erro]** Valor inválido.")
        
        if amount > bank:
            return await ctx.send("**[Erro]** Seu saldo bancário é insuficiente.")

        self.update_balance(ctx.author.id, amount, "wallet")
        self.update_balance(ctx.author.id, -amount, "bank")

        await ctx.send(f"| Você sacou **{amount:,} ZE** e agora está na sua carteira!")

    @commands.command(name="economy", aliases=["economia", "ajuda_economia"])
    async def economy_help(self, ctx):
        """Lista todos os comandos da economia."""
        prefix = ctx.prefix
        embed = discord.Embed(
            title="Guia de Economia - Deep Sea",
            description=(
                f"Aqui estão os comandos para gerenciar suas conquistas:\n\n"
                f"• `{prefix}money` - Veja seu saldo na carteira e banco.\n"
                f"• `{prefix}dep [valor/all]` - Guarda moedas no banco.\n"
                f"• `{prefix}with [valor/all]` - Saca moedas do banco.\n"
                f"• `{prefix}loja` - Abre o mercado de VIPs.\n"
                f"• `{prefix}comprar [id]` - Adquire um cargo VIP."
            ),
            color=discord.Color.from_rgb(0, 0, 0)
        )
        embed.set_footer(text="Use os comandos com sabedoria, explorador.")
        await ctx.send(embed=embed)

    @commands.command(name="loja", aliases=["shop", "store"])
    async def shop(self, ctx):
        """Exibe os itens e cargos disponíveis para compra com interface interativa."""
        if self.collection is None:
            return await ctx.send("**[Erro]** A loja está fechada temporariamente por problemas técnicos.")
        embed = discord.Embed(
            title="Mercado das Profundezas - Zarathos",
            description=(
                "Selecione uma opção no seletor para continuar! Você poderá visualizar os benefícios antes de confirmar a compra."
            ),
            color=discord.Color.from_rgb(20, 20, 20)
        )
        
        # Thumbnail fictícia ou do bot
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Powered by Zarathos | Economia • Atividade • Call • Brasil • Hoje às {datetime.datetime.now().strftime('%H:%M')}")
        
        view = ShopView(self)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="comprar", aliases=["buy"])
    async def buy(self, ctx, item_id: str):
        """Compra um cargo VIP da loja."""
        if self.collection is None:
            return await ctx.send("**[Erro]** Vendas suspensas por instabilidade no banco de dados.")

        # A lista precisa estar aqui dentro para o reload funcionar
        vips = {
            "1": {"nome": "Vip Surface", "preco": 25000},
            "2": {"nome": "Vip Kraken", "preco": 45000},
            "3": {"nome": "Vip Leviathan", "preco": 80000}
        }

        if item_id not in vips:
            return await ctx.send("**[Erro]** ID inválido. Use `z.loja` para ver os códigos.")

        item = vips[item_id]
        user_data = self.get_user_data(ctx.author.id)
        saldo_total = user_data.get("balance", 0) + user_data.get("bank", 0)
        
        if saldo_total < item["preco"]:
            faltam = item["preco"] - saldo_total
            return await ctx.send(f"**[Saldo Insuficiente]** Você precisa de mais `{faltam:,} ZE` para este VIP.")

        # Processamento do pagamento
        current_wallet = user_data.get("balance", 0)
        if current_wallet >= item["preco"]:
            self.update_balance(ctx.author.id, -item["preco"], "wallet")
        else:
            sobra = item["preco"] - current_wallet
            self.update_balance(ctx.author.id, -current_wallet, "wallet")
            self.update_balance(ctx.author.id, -sobra, "bank")

        # Entrega do cargo
        role = discord.utils.get(ctx.guild.roles, name=item["nome"])
        
        if role:
            try:
                await ctx.author.add_roles(role)
                msg = f"| Sucesso! Você agora é um **{item['nome']}**. Bem-vindo às profundezas!"
            except discord.Forbidden:
                msg = f"| Pagamento aceito! Mas estou sem permissão para te dar o cargo `{item['nome']}`. Chame um staff."
        else:
            msg = f"| Pagamento aceito! O cargo `{item['nome']}` não foi encontrado no servidor. Chame um staff."

        await ctx.send(msg)
        print(f"[ECONOMIA] {ctx.author} adquiriu {item['nome']}")

    # --- Listeners de Atividade ---

    @commands.Cog.listener()
    async def on_message(self, message):
        """Recompensa por mensagens enviadas."""
        if message.author.bot or not message.guild or self.collection is None:
            return

        user_id = str(message.author.id)
        
        # Sistema de XP por Mensagem
        xp_gain = random.randint(15, 25)
        multiplier = self.get_xp_multiplier(message.author)
        total_xp = int(xp_gain * multiplier)
        
        leveled_up, level = self.add_xp(user_id, total_xp, message.guild, message.author)
        if leveled_up:
            try:
                await message.channel.send(f"| **LEVEL UP!** {message.author.mention}, você subiu para o **Nível {level}**! Continue explorando as profundezas.")
            except:
                pass

        # Incrementa APENAS o contador de mensagens (sem dar ZE automático)
        self.collection.update_one(
            {"_id": user_id}, 
            {
                "$inc": {"msg_count": 1},
                "$setOnInsert": {"balance": 0, "bank": 0}
            },
            upsert=True
        )

        # Bônus automático ao atingir 1.000 mensagens
        user_data = self.get_user_data(user_id)
        if user_data.get("msg_count", 0) >= 1000:
            bonus = 3500
            self.update_balance(user_id, bonus)
            self.collection.update_one({"_id": user_id}, {"$set": {"msg_count": 0}})
            
            try:
                await message.channel.send(f"| **Conversão Automática!** {message.author.mention}, você atingiu **1.000 mensagens** e elas foram convertidas em **{bonus:,} ZE**!")
            except:
                pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Recompensa por tempo em call."""
        if member.bot or self.collection is None:
            return

        user_id = member.id
        now = datetime.datetime.now(datetime.timezone.utc)

        # Entrou em uma call (ou mudou de canal)
        if after.channel is not None and before.channel is None:
            # Ignora canais AFK se houver
            if not after.afk:
                self.voice_tracking[user_id] = now

        # Saiu da call
        elif after.channel is None and before.channel is not None:
            if user_id in self.voice_tracking:
                join_time = self.voice_tracking.pop(user_id)
                duration = now - join_time
                total_seconds = duration.total_seconds()
                
                # Cálculo exato: 3500 ZE por 3600 segundos (1 hora)
                if total_seconds >= 60: # Mínimo de 1 minuto para ganhar algo
                    total_reward = int((total_seconds / 3600) * 3500)
                    minutes = int(total_seconds // 60)
                    
                    # XP por Voice (10 XP por minuto base)
                    xp_voice = int((minutes * 10) * self.get_xp_multiplier(member))
                    self.add_xp(user_id, xp_voice)
                    
                    if total_reward > 0:
                        self.update_balance(user_id, total_reward)
                        
                        try:
                            # Mensagem sem emojis e com valor exato
                            await member.send(f"| Atividade em Voice: Você passou `{minutes}` minutos em call e recebeu **{total_reward:,} ZE** e **{xp_voice} XP**!")
                        except:
                            pass

    @commands.command(name="rank", aliases=["level", "nivel", "xp"])
    async def rank(self, ctx, member: discord.Member = None):
        """Mostra o nível e XP de um explorador."""
        member = member or ctx.author
        member = member or ctx.author
        if self.collection is None:
            return await ctx.send(f"**[Erro]** Sistema de ranking offline. Motivo: `{self.error_msg or 'Conexão indisponível'}`")
            
        user_data = self.get_user_data(member.id)
        level = user_data.get("level", 1)
        xp = user_data.get("xp", 0)
        xp_needed = level * 500
        
        # Barra de progresso visual simples
        filled = int((xp / xp_needed) * 10)
        bar = "▰" * filled + "▱" * (10 - filled)
        
        embed = discord.Embed(
            title=f"Explorador: {member.display_name}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Nível Atual", value=f"**{level}**", inline=True)
        embed.add_field(name="Experiência (XP)", value=f"`{xp}/{xp_needed}`", inline=True)
        embed.add_field(name="Progresso", value=f"{bar} ({int((xp/xp_needed)*100)}%)", inline=False)
        
        # Mostra o status VIP se tiver
        multiplier = self.get_xp_multiplier(member)
        if multiplier > 1.0:
            embed.add_field(name="Bônus Ativo", value=f"💎 Multiplicador de XP: **{multiplier}x**", inline=False)
            
        embed.set_footer(text="Zarathos • A cada mensagem o conhecimento aumenta.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
