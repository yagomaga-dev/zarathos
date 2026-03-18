import discord
from discord.ext import commands
from discord import ui
import random
import datetime
import os
import pymongo
import certifi
from dotenv import load_dotenv
from typing import Optional

# Carrega variáveis de ambiente locais
load_dotenv()


class ShopSelect(ui.Select):
    def __init__(self, economy_cog: "Economy"):
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
        preco: int = int(vip["preco"])
        embed = discord.Embed(
            title=f"Detalhes: {vip['nome']}",
            description=(
                f"**Preço:** `{preco:,} ZE`\n"
                f"**Duração:** `{vip['duracao']}`\n\n"
                f"**Benefícios:**\n{vip['desc']}\n\n"
                f"Para comprar, use o comando: `z.comprar {self.values[0]}`"
            ),
            color=discord.Color.dark_purple()
        )
        embed.set_footer(text="Confirme se possui saldo suficiente antes de comprar.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ShopView(ui.View):
    def __init__(self, economy_cog: "Economy"):
        super().__init__(timeout=None)
        self.economy_cog = economy_cog
        self.add_item(ShopSelect(economy_cog))

    @ui.button(label="Converter", style=discord.ButtonStyle.grey)
    async def convert(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        user_data = self.economy_cog.get_user_data(user_id)

        if not user_data:
            return await interaction.response.send_message("Nao encontrei seus dados no sistema.", ephemeral=True)

        msgs: int = int(user_data.get("msg_count", 0))

        if msgs < 1:
            return await interaction.response.send_message("Voce nao tem mensagens acumuladas para converter ainda.", ephemeral=True)

        # Taxa: 3.5 ZE por mensagem
        reward: int = int(msgs * 3.5)

        if reward > 0:
            self.economy_cog.update_balance(user_id, reward, "wallet")
            col = self.economy_cog.collection
            if col is not None:
                col.update_one({"_id": user_id}, {"$set": {"msg_count": 0}})

            await interaction.response.send_message(
                f"**Conversão Concluída!**\n"
                f"Você converteu **{msgs:,} mensagens** em **{reward:,} ZE**.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("Você precisa de pelo menos uma mensagem para converter.", ephemeral=True)

    @ui.button(label="Meu Saldo", style=discord.ButtonStyle.grey)
    async def my_balance(self, interaction: discord.Interaction, button: ui.Button):
        user_data = self.economy_cog.get_user_data(interaction.user.id)
        if user_data:
            wallet: int = int(user_data.get("balance", 0))
            bank: int = int(user_data.get("bank", 0))
            await interaction.response.send_message(
                f"**Seu Saldo:**\n"
                f"Carteira: `{wallet:,} ZE`\n"
                f"Banco: `{bank:,} ZE`\n"
                f"Total: `{wallet + bank:,} ZE`",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("Não consegui encontrar seus dados financeiros.", ephemeral=True)


class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.collection: Optional[pymongo.collection.Collection] = None
        self.error_msg: str = ""
        self.voice_tracking: dict = {}
        self.target_channel_id: Optional[str] = os.getenv("CHAT_ECONOMIA")
        self.connect_db()

    def connect_db(self):
        """Tenta estabelecer conexão com o MongoDB."""
        url = os.getenv("MONGO_URL")
        if not url:
            self.error_msg = "A variável 'MONGO_URL' não foi encontrada nas configurações."
            self.collection = None
            return

        try:
            ca = certifi.where()
            cluster = pymongo.MongoClient(url, serverSelectionTimeoutMS=5000, tlsCAFile=ca)
            cluster.admin.command("ping")
            db = cluster["zarathos_db"]
            self.collection = db["economy"]
            self.error_msg = ""
            print("[SISTEMA] Conectado ao MongoDB Atlas com sucesso.")
        except Exception as e:
            self.error_msg = str(e)
            self.collection = None
            print(f"[ERRO] Falha ao conectar ao banco de dados: {self.error_msg}")

    def get_user_data(self, user_id) -> Optional[dict]:
        """Retorna os dados do usuário ou cria se não existir."""
        if self.collection is None:
            self.connect_db()
        col = self.collection
        if col is None:
            return None

        uid = str(user_id)
        data = col.find_one({"_id": uid})

        if not data:
            data = {
                "_id": uid,
                "balance": 0,
                "bank": 0,
                "msg_count": 0,
                "total_msgs": 0,
                "msgs_spent": 0,
            }
            col.insert_one(data)

        return data

    def update_balance(self, user_id, amount: int, mode: str = "wallet"):
        """Atualiza o saldo do usuário (carteira ou banco)."""
        col = self.collection
        if col is None:
            return

        uid = str(user_id)
        field = "balance" if mode == "wallet" else "bank"
        try:
            col.update_one({"_id": uid}, {"$inc": {field: amount}})
        except Exception as e:
            print(f"[ERRO] Falha ao atualizar saldo: {e}")

    # ------------------------------------------------------------------ #
    #  Comandos                                                            #
    # ------------------------------------------------------------------ #

    @commands.command(name="money", aliases=["saldo", "bal", "atm", "wallet", "carteira"])
    async def balance(self, ctx, member: discord.Member = None):
        """Verifica o saldo de um membro."""
        if self.collection is None:
            return await ctx.send(f"**[Erro]** Sistema offline. Motivo: `{self.error_msg or 'Conexao indisponivel'}`")

        member = member or ctx.author
        user_data = self.get_user_data(member.id)

        if not user_data:
            return await ctx.send("**[Erro]** Falha ao carregar dados do usuário.")

        wallet: int = int(user_data.get("balance", 0))
        bank: int = int(user_data.get("bank", 0))
        total: int = wallet + bank

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

    @commands.command(name="profile", aliases=["p", "perfil"])
    async def profile(self, ctx, member: discord.Member = None):
        """Exibe o perfil completo do usuário no sistema Zarathos."""
        member = member or ctx.author
        user_data = self.get_user_data(member.id)
        
        if not user_data:
            return await ctx.send("**[Erro]** Não foi possível carregar os dados do perfil.")

        wallet: int = int(user_data.get("balance", 0))
        bank: int = int(user_data.get("bank", 0))
        total_msgs: int = int(user_data.get("total_msgs", 0))
        msgs_spent: int = int(user_data.get("msgs_spent", 0))
        current_msgs: int = int(user_data.get("msg_count", 0))
        
        # Identifica se possui algum dos cargos VIP definidos na loja
        vips = ["Vip Surface", "Vip Kraken", "Vip Leviathan"]
        user_vips = [role.name for role in member.roles if role.name in vips]
        vip_status = " | ".join(user_vips) if user_vips else "Nenhum"

        embed = discord.Embed(
            title=f"Perfil - {member.name}",
            color=discord.Color.dark_purple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        # Busca o banner do usuário
        user_fetch = await self.bot.fetch_user(member.id)
        if user_fetch.banner:
            embed.set_image(url=user_fetch.banner.url)
            
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="Economia", value=f"Carteira: `{wallet:,} ZE`\nBanco: `{bank:,} ZE`", inline=True)
        embed.add_field(name="Atividade", value=f"Atuais: `{current_msgs:,}`\nGastas: `{msgs_spent:,}`\nTotal: `{total_msgs:,}`", inline=True)
        embed.add_field(name="Status VIP", value=f"`{vip_status}`", inline=False)
        
        # Data de entrada formatada
        entrada = member.joined_at.strftime("%d/%m/%Y")
        embed.set_footer(text=f"Explorador desde {entrada} • Zarathos Bot")
        
        await ctx.send(embed=embed)

    @commands.command(name="rank", aliases=["leaderboard"])
    async def rank_leaderboard(self, ctx):
        """Mostra o ranking dos usuarios mais ricos do servidor."""
        col = self.collection
        if col is None:
            return await ctx.send("**[Erro]** Sistema offline.")

        # Pipeline de agregacao para somar saldo e banco com tratamento de nulos
        pipeline = [
            {
                "$project": {
                    "_id": 1,
                    "total": {
                        "$add": [
                            {"$ifNull": ["$balance", 0]},
                            {"$ifNull": ["$bank", 0]}
                        ]
                    }
                }
            },
            {"$sort": {"total": -1}},
            {"$limit": 10}
        ]

        try:
            results = list(col.aggregate(pipeline))
            if not results:
                return await ctx.send("Nenhum dado financeiro registrado no momento.")

            embed = discord.Embed(
                title="Ranking de Economia - Zarathos",
                description="Os 10 exploradores mais ricos das profundezas.\n\n",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )

            description = ""
            for i, user in enumerate(results, 1):
                uid = user["_id"]
                # Tenta pegar do cache do bot, se nao conseguir mostra o ID
                user_obj = self.bot.get_user(int(uid))
                name = user_obj.name if user_obj else f"ID: {uid}"
                total = int(user["total"])
                
                medal = f"`{i}.` "
                
                description += f"{medal}**{name}** — `{total:,} ZE`\n"

            embed.description += description
            embed.set_footer(text="A riqueza aqui é medida em Essência.")
            await ctx.send(embed=embed)
        except Exception as e:
            print(f"[ERRO] Falha ao gerar rank: {e}")
            await ctx.send("**[Erro]** Nao foi possivel carregar o ranking no momento.")

    @commands.command(name="messages", aliases=["msgs", "msg", "mensagens"])
    async def messages_count(self, ctx, member: discord.Member = None):
        """Mostra a quantidade de mensagens acumuladas para conversão."""
        if self.collection is None:
            return await ctx.send("**[Erro]** Sistema offline.")

        member = member or ctx.author
        user_data = self.get_user_data(member.id)

        if not user_data:
            return await ctx.send("**[Erro]** Falha ao carregar dados.")

        msgs: int = int(user_data.get("msg_count", 0))
        estimativa: int = int(msgs * 3.5)

        embed = discord.Embed(
            title=f"Atividade de {member.display_name}",
            description=(
                f"Protocolo de monitoramento de chat ativo.\n\n"
                f"Mensagens Acumuladas: `{msgs:,}`\n"
                f"Valor estimado: `~{estimativa:,}` ZE"
            ),
            color=discord.Color.blue()
        )

        if self.target_channel_id:
            embed.set_footer(text="Apenas mensagens em um canal específico são contabilizadas.")
        else:
            embed.set_footer(text="Todas as mensagens do servidor estão sendo contabilizadas.")

        await ctx.send(embed=embed)

    @commands.command(name="depositar", aliases=["dep", "deposito"])
    async def deposit(self, ctx, amount: str):
        """Guarda moedas no banco para seguranca."""
        if self.collection is None:
            return await ctx.send("**[Erro]** Sistema offline. Tente novamente em instantes.")

        user_data = self.get_user_data(ctx.author.id)
        if not user_data:
            return await ctx.send("**[Erro]** Falha ao carregar seus dados.")

        wallet: int = int(user_data.get("balance", 0))
        qty: int

        if amount.lower() == "all":
            qty = wallet
        else:
            try:
                qty = int(amount)
            except ValueError:
                return await ctx.send("**[Erro]** Informe um valor numérico válido ou `all`.")

        if qty <= 0:
            return await ctx.send("**[Erro]** Você não pode depositar valores negativos ou zero.")

        if qty > wallet:
            return await ctx.send("**[Erro]** Você não tem essa quantia na carteira.")

        self.update_balance(ctx.author.id, -qty, "wallet")
        self.update_balance(ctx.author.id, qty, "bank")
        await ctx.send(f"Você guardou **{qty:,} ZE** no cofre do Banco!")

    @commands.command(name="sacar", aliases=["withdraw", "with"])
    async def withdraw(self, ctx, amount: str):
        """Saca moedas do banco para a carteira."""
        if self.collection is None:
            return await ctx.send("**[Erro]** Sistema offline. Tente novamente em instantes.")

        user_data = self.get_user_data(ctx.author.id)
        if not user_data:
            return await ctx.send("**[Erro]** Falha ao carregar seus dados.")

        bank: int = int(user_data.get("bank", 0))
        qty: int

        if amount.lower() == "all":
            qty = bank
        else:
            try:
                qty = int(amount)
            except ValueError:
                return await ctx.send("**[Erro]** Valor inválido.")

        if qty <= 0:
            return await ctx.send("**[Erro]** Valor inválido.")

        if qty > bank:
            return await ctx.send("**[Erro]** Seu saldo bancário é insuficiente.")

        self.update_balance(ctx.author.id, qty, "wallet")
        self.update_balance(ctx.author.id, -qty, "bank")
        await ctx.send(f"Você sacou **{qty:,} ZE** e agora está na sua carteira!")

    @commands.command(name="convert", aliases=["converter", "trocar"])
    async def manual_convert(self, ctx):
        """Converte as mensagens acumuladas em ZE."""
        if self.collection is None:
            return await ctx.send("**[Erro]** Sistema offline.")

        user_id = str(ctx.author.id)
        user_data = self.get_user_data(user_id)

        if not user_data:
            return await ctx.send("**[Erro]** Falha ao acessar banco de dados.")

        msgs: int = int(user_data.get("msg_count", 0))

        if msgs < 1:
            return await ctx.send("**[Aviso]** Você não possui mensagens acumuladas para converter.")

        reward: int = int(msgs * 3.5)

        if reward > 0:
            self.update_balance(user_id, reward)
            col = self.collection
            if col is not None:
                col.update_one(
                    {"_id": user_id}, 
                    {
                        "$set": {"msg_count": 0},
                        "$inc": {"msgs_spent": msgs}
                    }
                )

            embed = discord.Embed(
                title="Conversão Direta",
                description=(
                    f"O sistema processou sua atividade recente.\n\n"
                    f"Atividade: `{msgs:,} mensagens`\n"
                    f"Rendimento: `+{reward:,} ZE`"
                ),
                color=discord.Color.dark_purple()
            )
            embed.set_footer(text="Zarathos Economy System")
            await ctx.send(embed=embed)
        else:
            await ctx.send("**[Aviso]** Atividade insuficiente para gerar rendimento.")

    @commands.command(name="loja", aliases=["shop", "store"])
    async def shop(self, ctx):
        """Exibe os itens e cargos disponíveis para compra."""
        if self.collection is None:
            return await ctx.send("**[Erro]** A loja está fechada temporariamente.")

        embed = discord.Embed(
            title="Mercado das Profundezas - Zarathos",
            description="Selecione uma opção no seletor para continuar!",
            color=discord.Color.from_rgb(20, 20, 20)
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Hoje as {datetime.datetime.now().strftime('%H:%M')}")
        view = ShopView(self)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="comprar", aliases=["buy"])
    async def buy(self, ctx, item_id: str):
        """Compra um cargo VIP da loja."""
        if self.collection is None:
            return await ctx.send("**[Erro]** Vendas suspensas por instabilidade no banco de dados.")

        vips = {
            "1": {"nome": "Vip Surface", "preco": 25000},
            "2": {"nome": "Vip Kraken", "preco": 45000},
            "3": {"nome": "Vip Leviathan", "preco": 80000}
        }

        if item_id not in vips:
            return await ctx.send("**[Erro]** ID invalido. Use `z.loja` para ver os codigos.")

        item = vips[item_id]
        preco: int = int(item["preco"])

        user_data = self.get_user_data(ctx.author.id)
        if not user_data:
            return await ctx.send("**[Erro]** Falha ao carregar seus dados.")

        wallet: int = int(user_data.get("balance", 0))
        bank: int = int(user_data.get("bank", 0))
        saldo_total: int = wallet + bank

        if saldo_total < preco:
            faltam: int = preco - saldo_total
            return await ctx.send(f"**[Saldo Insuficiente]** Voce precisa de mais `{faltam:,} ZE` para este VIP.")

        # Processa o pagamento
        if wallet >= preco:
            self.update_balance(ctx.author.id, -preco, "wallet")
        else:
            sobra: int = preco - wallet
            self.update_balance(ctx.author.id, -wallet, "wallet")
            self.update_balance(ctx.author.id, -sobra, "bank")

        # Entrega o cargo
        role = discord.utils.get(ctx.guild.roles, name=item["nome"])
        if role:
            try:
                await ctx.author.add_roles(role)
                msg = f"Sucesso! Voce agora e um **{item['nome']}**. Bem-vindo!"
            except discord.Forbidden:
                msg = f"Pagamento aceito! Sem permissao para dar o cargo `{item['nome']}`. Chame um staff."
        else:
            msg = f"Pagamento aceito! O cargo `{item['nome']}` nao foi encontrado. Chame um staff."

        await ctx.send(msg)
        print(f"[ECONOMIA] {ctx.author} adquiriu {item['nome']}")

    @commands.command(name="diaria", aliases=["daily"])
    async def daily(self, ctx):
        """Coleta a recompensa diaria de Essencia."""
        if self.collection is None:
            return await ctx.send("**[Erro]** Sistema offline.")

        user_id = str(ctx.author.id)
        user_data = self.get_user_data(user_id)

        if not user_data:
            return await ctx.send("**[Erro]** Falha ao carregar seus dados.")

        now = datetime.datetime.now(datetime.timezone.utc)
        last_daily_str = user_data.get("last_daily")

        if last_daily_str and isinstance(last_daily_str, str):
            try:
                last_daily = datetime.datetime.fromisoformat(last_daily_str)
                delta = now - last_daily
                if delta.total_seconds() < 86400:
                    remaining = 86400 - delta.total_seconds()
                    hours: int = int(remaining // 3600)
                    minutes: int = int((remaining % 3600) // 60)
                    return await ctx.send(f"**[Calma]** Voce ja coletou seu daily hoje! Volte em **{hours}h {minutes}m**.")
            except (ValueError, TypeError):
                pass

        reward: int = random.randint(1500, 3000)
        self.update_balance(user_id, reward)

        col = self.collection
        if col is not None:
            col.update_one({"_id": user_id}, {"$set": {"last_daily": now.isoformat()}})

        await ctx.send(f"**Recompensa Diaria!** Voce recebeu **{reward:,} ZE**.")

    # ------------------------------------------------------------------ #
    #  Listeners                                                           #
    # ------------------------------------------------------------------ #

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Conta mensagens e recompensa a cada 1.000."""
        if message.author.bot or not message.guild:
            return

        col = self.collection
        if col is None:
            return

        # Restricao por canal
        if self.target_channel_id:
            if str(message.channel.id) != str(self.target_channel_id):
                return

        user_id = str(message.author.id)

        # Incrementa o contador de mensagens
        col.update_one(
            {"_id": user_id},
            {
                "$inc": {"msg_count": 1, "total_msgs": 1},
                "$setOnInsert": {"balance": 0, "bank": 0}
            },
            upsert=True
        )

        # Bonus automatico a cada 1.000 mensagens
        user_data = self.get_user_data(user_id)
        if user_data and int(user_data.get("msg_count", 0)) >= 1000:
            bonus: int = 3500
            self.update_balance(user_id, bonus)
            col2 = self.collection
            if col2 is not None:
                col2.update_one(
                    {"_id": user_id}, 
                    {
                        "$set": {"msg_count": 0},
                        "$inc": {"msgs_spent": 1000}
                    }
                )

            embed = discord.Embed(
                title="Ciclo De Atividade Concluido",
                description=(
                    f"{message.author.mention}, voce atingiu o marco de **1.000 mensagens**!\n\n"
                    f"Recompensa Automatica: `+3.500 ZE`"
                ),
                color=discord.Color.gold()
            )
            embed.set_footer(text="A atividade gera poder nas profundezas.")
            try:
                await message.channel.send(embed=embed)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Recompensa por tempo em call."""
        if member.bot or self.collection is None:
            return

        user_id = member.id
        now = datetime.datetime.now(datetime.timezone.utc)

        # Entrou em uma call
        if after.channel is not None and before.channel is None:
            if not after.afk:
                self.voice_tracking[user_id] = now

        # Saiu da call
        elif after.channel is None and before.channel is not None:
            if user_id in self.voice_tracking:
                join_time = self.voice_tracking.pop(user_id)
                total_seconds: float = (now - join_time).total_seconds()

                if total_seconds >= 60:
                    total_reward: int = int((total_seconds / 3600) * 3500)
                    minutes_in_call: int = int(total_seconds // 60)

                    if total_reward > 0:
                        self.update_balance(user_id, total_reward)
                        try:
                            await member.send(
                                f"Atividade em Voice: Voce passou `{minutes_in_call}` minutos em call "
                                f"e recebeu **{total_reward:,} ZE**!"
                            )
                        except Exception:
                            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
