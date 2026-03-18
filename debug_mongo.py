import pymongo
import certifi
import os
from dotenv import load_dotenv
import ssl

load_dotenv()
url = os.getenv("MONGO_URL")

def test_connection(name, **kwargs):
    print(f"\n--- Testando: {name} ---")
    try:
        client = pymongo.MongoClient(url, serverSelectionTimeoutMS=5000, **kwargs)
        client.admin.command("ping")
        print(f"SUCESSO: {name}")
        return True
    except Exception as e:
        print(f"FALHA: {name}\nErro: {e}")
        return False

if __name__ == "__main__":
    if not url:
        print("ERRO: MONGO_URL não encontrada no .env")
    else:
        # Teste 1: Com certifi (o que já tentamos)
        test_connection("Certifi (Padrao)", tlsCAFile=certifi.where())

        # Teste 2: Permitindo certificados inválidos (Diagnóstico)
        test_connection("Allow Invalid Certs", tlsAllowInvalidCertificates=True)

        # Teste 3: Sem SSL (O Atlas exige SSL, então deve falhar)
        # test_connection("Sem SSL", tls=False)

        # Teste 4: Usando o contexto padrão do SSL
        test_connection("Contexto Padrao SSL", tls=True)
