from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "O servidor web do Zarathos está online e pronto para manter o bot vivo 24/7!"

def run():
    # Roda o servidor web na porta 8080 (padrão de nuvem)
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Inicia a thread separada para o servidor Web"""
    t = Thread(target=run)
    t.start()
