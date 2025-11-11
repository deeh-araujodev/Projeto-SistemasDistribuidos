import zmq
import json
import os
from datetime import datetime
import random 

# --- CONFIGURAÇÃO DE DADOS ---
POSSIBLE_USERS = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Mateus", "Felipe", "Thiago", "Vanessa", "Maura", "Nilza", "Laura"]
POSSIBLE_CHANNELS = ["Geral", "DevOps", "Python", "ZeroMQ", "SD-Projeto", "Doramas", "Aventuras", "Trilhas", "Viagens", "Jogos"]

# Configuração de Caminho (Correto)
DATA_DIR = "data" 
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")

# Garante que o diretório de dados exista
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- FUNÇÕES DE PERSISTÊNCIA ---
def load_json(filename):
    # ... (mantido inalterado) ...
    if not os.path.exists(filename):
        return []
    with open(filename, "r") as fp:
        try:
            return json.load(fp)
        except json.JSONDecodeError:
            return [] 

def save_json(filename, data):
    # ... (mantido inalterado) ...
    with open(filename, "w") as fp:
        json.dump(data, fp, indent=2)

# --- NOVO: FUNÇÃO DE GERAÇÃO DE DADOS ALEATÓRIOS ---
def generate_initial_data():
    """
    Carrega os dados existentes e adiciona novos usuários e canais aleatórios 
    a cada execução do programa, garantindo a atualização do arquivo JSON.
    """
    
    # 1. Usuários
    current_users = load_json(USERS_FILE)
    
    # Filtra os usuários que JÁ FORAM adicionados para não duplicar
    available_users = [user for user in POSSIBLE_USERS if user not in current_users]
    
    if available_users:
        # Escolhe um número aleatório para adicionar (entre 1 e no máximo o que estiver disponível)
        max_to_add = min(len(available_users), 3) 
        num_new_users = random.randint(1, max_to_add) 
        
        new_users = random.sample(available_users, num_new_users) 
        current_users.extend(new_users)
        
        save_json(USERS_FILE, current_users)
        print(f"   -> ADICIONADOS {num_new_users} novos usuários: {new_users}")
    else:
        print("   -> Não há novos usuários na lista para adicionar.")
    
    # 2. Canais
    current_channels = load_json(CHANNELS_FILE)
    
    # Filtra os canais que JÁ FORAM adicionados
    available_channels = [ch for ch in POSSIBLE_CHANNELS if ch not in current_channels]
    
    if available_channels:
        # Escolhe um número aleatório para adicionar
        max_to_add = min(len(available_channels), 3) 
        num_new_channels = random.randint(1, max_to_add) 
        
        new_channels = random.sample(available_channels, num_new_channels)
        current_channels.extend(new_channels)
        
        save_json(CHANNELS_FILE, current_channels)
        print(f"   -> ADICIONADOS {num_new_channels} novos canais: {new_channels}")
    else:
        print("   -> Não há novos canais na lista para adicionar.")
    
    # Retorna os dados atualizados
    return current_users, current_channels

# --- EXECUÇÃO INICIAL (Agora esta linha SEMPRE ATUALIZA) ---
print("--- Verificando e Atualizando dados de persistência ---")
USERS_IN_MEMORY, CHANNELS_IN_MEMORY = generate_initial_data()
# -------------------------

ctx = zmq.Context()
rep = ctx.socket(zmq.REP)
rep.bind("tcp://*:5556")

print("🧠 Servidor (Parte 1 - JSON) rodando em tcp://*:5556")

# O loop principal (while True) permanece inalterado pois a lógica de requisição/resposta 
# e salvamento para 'login' e 'channel' já estava correta, usando as variáveis em memória.
while True:
    try:
        raw = rep.recv()
        msg = json.loads(raw.decode("utf-8"))
        service = msg.get("service")
        data = msg.get("data", {})
        timestamp = datetime.now().isoformat()

        # Serviço: LOGIN -------------------------------------------------------
        if service == "login":
            user = data.get("user")
            if user in USERS_IN_MEMORY: 
                reply = { "service": "login", "data": { "status": "erro", "timestamp": timestamp, "description": "Usuário já logado" }}
            else:
                USERS_IN_MEMORY.append(user)
                save_json(USERS_FILE, USERS_IN_MEMORY) 
                reply = { "service": "login", "data": { "status": "sucesso", "timestamp": timestamp }}

        # Serviço: USERS -------------------------------------------------------
        elif service == "users":
            reply = { "service": "users", "data": { "timestamp": timestamp, "users": USERS_IN_MEMORY }}

        # Serviço: CHANNEL -----------------------------------------------------
        elif service == "channel":
            channel = data.get("channel")
            if channel in CHANNELS_IN_MEMORY:
                reply = { "service": "channel", "data": { "status": "erro", "timestamp": timestamp, "description": "Canal já existe" }}
            else:
                CHANNELS_IN_MEMORY.append(channel)
                save_json(CHANNELS_FILE, CHANNELS_IN_MEMORY) 
                reply = { "service": "channel", "data": { "status": "sucesso", "timestamp": timestamp }}

        # Serviço: CHANNELS ----------------------------------------------------
        elif service == "channels":
            reply = { "service": "channels", "data": { "timestamp": timestamp, "channels": CHANNELS_IN_MEMORY }}

        # Serviço inválido -----------------------------------------------------
        else:
            reply = { "service": "erro", "data": { "timestamp": timestamp, "description": "Serviço inválido" }}

        rep.send_string(json.dumps(reply))
    except KeyboardInterrupt:
        print("\nServidor encerrado por KeyboardInterrupt.")
        break
    except Exception as e:
        print(f"\nErro inesperado no servidor: {e}")
        break