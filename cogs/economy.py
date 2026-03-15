import discord
from discord.ext import commands
import random
import datetime
from dotenv import load_dotenv
import os
import pymongo

# Tentativa de carregar o .env para ambientes locais
load_dotenv()

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
                "last_daily": None,
                "last_work": None
            }
            self.collection.insert_one(data)
        return data

    def update_balance(self, user_id, amount, mode="wallet"):
        """Atualiza o saldo do usuário (carteira ou banco)."""
        if self.collection is None: return
        
        user_id = str(user_id)
        field = "balance" if mode == "wallet" else "bank"
        self.collection.update_one({"_id": user_id}, {"$inc": {field: amount}})

    @commands.command(name="daily", aliases=["diario"])
    async def daily(self, ctx):
        """Recompensa diária de Essência."""
        if self.collection is None:
            self.connect_db()
            if self.collection is None:
                return await ctx.send(f"**[Falha no Sistema]**\nO sistema de economia está offline.\nMotivo: `{self.error_msg}`")

        user_id = str(ctx.author.id)
        user_data = self.get_user_data(user_id)
        now = datetime.datetime.now(datetime.timezone.utc)

        last_daily = user_data.get("last_daily")
        if last_daily:
            # MongoDB pode retornar datetime diretamente ou string
            if isinstance(last_daily, str):
                try:
                    last_daily = datetime.datetime.fromisoformat(last_daily.replace('Z', '+00:00'))
                except ValueError:
                    last_daily = None
            
            # Se for datetime mas sem timezone (naive), adiciona UTC
            if isinstance(last_daily, datetime.datetime) and last_daily.tzinfo is None:
                last_daily = last_daily.replace(tzinfo=datetime.timezone.utc)
            
            # 24 horas de cooldown
            if isinstance(last_daily, datetime.datetime) and (now - last_daily).total_seconds() < 86400:
                restante = 86400 - (now - last_daily).total_seconds()
                horas = int(restante // 3600)
                minutos = int((restante % 3600) // 60)
                return await ctx.send(f"**[Calma]** Você já coletou sua essência hoje! Volte em `{horas}h {minutos}m`.")

        reward = random.randint(500, 1500)
        self.update_balance(user_id, reward)
        self.collection.update_one({"_id": user_id}, {"$set": {"last_daily": now}})

        embed = discord.Embed(
            title="Colheita de Essência",
            description=f"Você colheu **{reward} ZE** das sombras de Zarathos!",
            color=discord.Color.purple(),
            timestamp=now
        )
        embed.set_footer(text=f"Saldo atual: {user_data['balance'] + reward} ZE")
        await ctx.send(embed=embed)

    @commands.command(name="money", aliases=["saldo", "bal", "atm", "wallet", "carteira"])
    async def balance(self, ctx, member: discord.Member = None):
        """Verifica o saldo de um membro."""
        if self.collection is None: return
        
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


    @commands.command(name="depositar", aliases=["dep"])
    async def deposit(self, ctx, amount):
        """Deposita moedas no banco para segurança."""
        if self.collection is None: return

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
        if self.collection is None: return

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
                f"• `{prefix}daily` - Coleta sua recompensa diária.\n"
                f"• `{prefix}money (@user)` - Veja seu saldo atual.\n"
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
        """Exibe os itens e cargos disponíveis para compra."""
        embed = discord.Embed(
            title="Mercado das Profundezas - Deep Sea",
            description=(
                "Quer se destacar no servidor com um cargo exclusivo e vantagens especiais? "
                "Você pode se tornar VIP utilizando sua **Essência de Zarathos (ZE)**.\n\n"
                "*Lembre-se: não realizamos reembolso e, caso saia do servidor, será necessário adquirir o VIP novamente.*\n"
                "Use `z.comprar <ID>` para adquirir."
            ),
            color=discord.Color.from_rgb(0, 0, 0),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        # VIP 1 - SURFACE
        embed.add_field(
            name="1 - VIP Surface",
            value=(
                "Preço: `25,000 ZE`\n"
                "Duração: `30 dias`\n"
                "**Benefícios:**\n"
                "└ Cargo exclusivo @Vip Surface\n"
                "└ Alterar o próprio nick\n"
                "└ Enviar imagens em canais restritos\n"
                "└ Emojis externos e sorteios VIP\n"
                "*Representa aqueles que começam a explorar o oceano.*"
            ),
            inline=False
        )

        # VIP 2 - KRAKEN
        embed.add_field(
            name="2 - VIP Kraken",
            value=(
                "Preço: `45,000 ZE`\n"
                "Duração: `40 dias`\n"
                "**Benefícios:**\n"
                "└ Tudo do nível anterior\n"
                "└ Cargo @Vip Kraken com destaque\n"
                "└ Criar 1 cargo personalizado\n"
                "└ Enviar áudios e efeitos sonoros\n"
                "└ Prioridade no atendimento\n"
                "*Membros poderosos que dominam as profundezas.*"
            ),
            inline=False
        )

        # VIP 3 - LEVIATHAN
        embed.add_field(
            name="3 - VIP Leviathan",
            value=(
                "Preço: `80,000 ZE`\n"
                "Duração: `50 dias`\n"
                "**Benefícios:**\n"
                "└ Tudo dos níveis anteriores\n"
                "└ Cargo @Vip Leviathan (Máximo Destaque)\n"
                "└ Acesso à Área VIP Exclusiva\n"
                "└ Adicionar 2 emojis/figurinhas\n"
                "└ Direito a 1 Mini VIP / Primeira Dama\n"
                "└ Acesso antecipado a eventos\n"
                "*Os membros mais lendários das profundezas.*"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="comprar", aliases=["buy"])
    async def buy(self, ctx, item_id: str):
        """Compra um cargo VIP da loja."""
        if self.collection is None: return

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
        # Ganho base: 5 ZE por mensagem
        reward = 5
        
        # Incrementa o contador e saldo
        self.collection.update_one(
            {"_id": user_id}, 
            {
                "$inc": {"balance": reward, "msg_count": 1},
                "$setOnInsert": {"bank": 0, "last_daily": None, "last_work": None}
            },
            upsert=True
        )

        # Checa meta de 1.000 mensagens
        user_data = self.get_user_data(user_id)
        if user_data.get("msg_count", 0) >= 1000:
            bonus = 3500
            self.update_balance(user_id, bonus)
            self.collection.update_one({"_id": user_id}, {"$set": {"msg_count": 0}})
            
            try:
                await message.channel.send(f"| PARABÉNS {message.author.mention}! Você atingiu **1.000 mensagens** e recebeu um bônus de **{bonus:,} ZE**!")
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
                    
                    if total_reward > 0:
                        self.update_balance(user_id, total_reward)
                        
                        try:
                            # Mensagem sem emojis e com valor exato
                            await member.send(f"| Atividade em Voice: Você passou `{minutes}` minutos em call e recebeu **{total_reward:,} ZE**!")
                        except:
                            pass

async def setup(bot):
    await bot.add_cog(Economy(bot))
