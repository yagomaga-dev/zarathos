import discord
from discord.ext import commands
import random
import datetime
from dotenv import load_dotenv
import os
import pymongo

# Tenta carregar o .env do diretório raiz
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, '.env')
load_dotenv(dotenv_path=env_path)

# Configuração do MongoDB
MONGO_URL = os.getenv("MONGO_URL")

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Conexão com o banco de dados
        if MONGO_URL:
            try:
                self.cluster = pymongo.MongoClient(MONGO_URL)
                self.db = self.cluster["zarathos_db"]
                self.collection = self.db["economy"]
                print("[SISTEMA] Conectado ao MongoDB com sucesso.")
            except Exception as e:
                print(f"[ERRO] Falha ao conectar ao MongoDB: {e}")
                self.collection = None
        else:
            print("[AVISO] MONGO_URL não encontrada no .env. Economia desativada.")
            self.collection = None

    def get_user_data(self, user_id):
        """Retorna os dados do usuário ou cria se não existir."""
        if self.collection is None:
            return None
            
        user_id = str(user_id)
        data = self.collection.find_one({"_id": user_id})
        
        if not data:
            data = {
                "_id": user_id,
                "balance": 0,
                "bank": 0,
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
            return await ctx.send("**[Erro]** O sistema de economia não está configurado corretamente (falta MONGO_URL).")

        user_id = str(ctx.author.id)
        user_data = self.get_user_data(user_id)
        now = datetime.datetime.now(datetime.timezone.utc)

        last_daily = user_data.get("last_daily")
        if last_daily:
            # MongoDB salva como datetime, então não precisamos converter se já for
            if isinstance(last_daily, str):
                last_daily = datetime.datetime.fromisoformat(last_daily)
            
            # 24 horas de cooldown
            if (now - last_daily).total_seconds() < 86400:
                restante = 86400 - (now - last_daily).total_seconds()
                horas = int(restante // 3600)
                minutos = int((restante % 3600) // 60)
                return await ctx.send(f"**[Calma]** Você já coletou sua essência hoje! Volte em `{horas}h {minutos}m`.")

        reward = random.randint(500, 1500)
        self.update_balance(user_id, reward)
        self.collection.update_one({"_id": user_id}, {"$set": {"last_daily": now}})

        embed = discord.Embed(
            title="✨ | Colheita de Essência",
            description=f"Você colheu **{reward} ZE** das sombras de Zarathos!",
            color=discord.Color.purple(),
            timestamp=now
        )
        embed.set_footer(text=f"Saldo atual: {user_data['balance'] + reward} ZE")
        await ctx.send(embed=embed)

    @commands.command(name="money", aliases=["saldo", "bal", "atm"])
    async def balance(self, ctx, member: discord.Member = None):
        """Verifica o saldo de um membro."""
        if self.collection is None: return
        
        member = member or ctx.author
        user_data = self.get_user_data(member.id)
        
        wallet = user_data["balance"]
        bank = user_data["bank"]
        total = wallet + bank

        embed = discord.Embed(
            title=f"💰 | Finanças de {member.display_name}",
            color=discord.Color.dark_purple(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.add_field(name="👛 Carteira", value=f"`{wallet:,} ZE`", inline=True)
        embed.add_field(name="🏦 Banco", value=f"`{bank:,} ZE`", inline=True)
        embed.add_field(name="📊 Total", value=f"`{total:,} ZE`", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.command(name="trabalhar", aliases=["work"])
    async def work(self, ctx):
        """Trabalhe para ganhar Essência."""
        if self.collection is None: return

        user_id = str(ctx.author.id)
        user_data = self.get_user_data(user_id)
        now = datetime.datetime.now(datetime.timezone.utc)

        last_work = user_data.get("last_work")
        if last_work:
            if isinstance(last_work, str):
                last_work = datetime.datetime.fromisoformat(last_work)
            
            # 1 hora de cooldown
            if (now - last_work).total_seconds() < 3600:
                restante = 3600 - (now - last_work).total_seconds()
                minutos = int(restante // 60)
                segundos = int(restante % 60)
                return await ctx.send(f"**[Cansaço]** Seus braços estão pesados. Descanse mais `{minutos}m {segundos}s`.")

        trabalhos = [
            "Limpou as masmorras de Zarathos",
            "Polindo os chifres do Guardião",
            "Organizando pergaminhos proibidos",
            "Caçando almas perdidas nos arredores",
            "Escoltando um novo membro pelo abismo"
        ]
        
        ganho = random.randint(100, 450)
        trabalho_feito = random.choice(trabalhos)
        
        self.update_balance(user_id, ganho)
        self.collection.update_one({"_id": user_id}, {"$set": {"last_work": now}})

        await ctx.send(f"⚒️ **| {ctx.author.display_name}**, você {trabalho_feito} e recebeu **{ganho} ZE**!")

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

        await ctx.send(f"🏦 **|** Você guardou **{amount:,} ZE** no cofre do Banco!")

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

        await ctx.send(f"👛 **|** Você sacou **{amount:,} ZE** e agora está na sua carteira!")

    @commands.command(name="loja", aliases=["shop", "store"])
    async def shop(self, ctx):
        """Exibe os itens e cargos disponíveis para compra."""
        embed = discord.Embed(
            title="🛒 | Mercado das Sombras - Zarathos",
            description="Use `!comprar <ID>` para adquirir um item.",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        # Aqui você define seus VIPs
        vips = [
            {"id": "1", "nome": "VIP Místico", "preco": 50000, "desc": "Tag exclusiva + Cor no nome"},
            {"id": "2", "nome": "VIP Soberano", "preco": 150000, "desc": "Permissão para mudar nick + Chat privado"},
            {"id": "3", "nome": "Lenda de Zarathos", "preco": 500000, "desc": "Cargo no topo + Canal de voz próprio"}
        ]

        for vip in vips:
            embed.add_field(
                name=f"ID: {vip['id']} - {vip['nome']}",
                value=f"💰 Preço: `{vip['preco']:,} ZE`\n📜 {vip['desc']}",
                inline=False
            )
        
        embed.set_footer(text="Economia Zarathos - Render & MongoDB")
        await ctx.send(embed=embed)

    @commands.command(name="comprar", aliases=["buy"])
    async def buy(self, ctx, item_id: str):
        """Compra um cargo VIP da loja."""
        if self.collection is None: return

        # Lista de itens (deve ser a mesma da loja)
        vips = {
            "1": {"nome": "VIP Místico", "preco": 50000},
            "2": {"nome": "VIP Soberano", "preco": 150000},
            "3": {"nome": "Lenda de Zarathos", "preco": 500000}
        }

        if item_id not in vips:
            return await ctx.send("**[Erro]** ID de item inválido. Use `!loja` para ver os códigos.")

        item = vips[item_id]
        user_data = self.get_user_data(ctx.author.id)
        
        # Verifica se tem dinheiro na carteira ou banco
        saldo_total = user_data["balance"] + user_data["bank"]
        
        if saldo_total < item["preco"]:
            faltam = item["preco"] - saldo_total
            return await ctx.send(f"**[Pobreza]** Você não tem Essência suficiente. Faltam `{faltam:,} ZE`.")

        # Tenta tirar da carteira primeiro, depois do banco
        if user_data["balance"] >= item["preco"]:
            self.update_balance(ctx.author.id, -item["preco"], "wallet")
        else:
            sobra = item["preco"] - user_data["balance"]
            self.update_balance(ctx.author.id, -user_data["balance"], "wallet")
            self.update_balance(ctx.author.id, -sobra, "bank")

        # Entrega do cargo
        role = discord.utils.get(ctx.guild.roles, name=item["nome"])
        
        if role:
            try:
                await ctx.author.add_roles(role)
                msg_sucesso = f"🎉 **| Sucesso!** Você adquiriu o cargo **{item['nome']}**."
            except discord.Forbidden:
                msg_sucesso = f"✅ **| Compra realizada!** Mas eu não tenho permissão para te dar o cargo `{item['nome']}`. Fale com um admin."
        else:
            msg_sucesso = f"✅ **| Compra realizada!** Porém, o cargo `{item['nome']}` não existe neste servidor. Contate os administradores."

        await ctx.send(msg_sucesso)
        print(f"[ECONOMIA] {ctx.author} comprou {item['nome']}")

async def setup(bot):
    await bot.add_cog(Economy(bot))
