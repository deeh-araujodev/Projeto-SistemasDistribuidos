import zmq
import json
import os
import time
from datetime import datetime

# === CONFIGURAÇÕES ===
DATA_DIR = "data"
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
MESSAGES_FILE = os.path.join(DATA_DIR, "messages.json")

# Garante que as pastas existam no sistema de arquivos do contêiner (e no host via volume)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# === CORES ===
RESET = "\033[0m"
BOLD = "\033[1m"
GRAY = "\033[90m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"

def log_time():
    return f"[{time.strftime('%H:%M:%S')}]"

def load_data(file):
    if not os.path.exists(file):
        return []
    try:
        with open(file, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# === Função para gerar o resumo global ===
def update_summary():
    """Gera resumo global com base nos relatórios JSON dos bots."""
    summary_path = os.path.join(REPORTS_DIR, "summary.json")
    # Nota: A lista reports é gerada dinamicamente lendo o diretório, 
    # o que garante que o servidor verá todos os reports salvos no volume pelos bots.
    reports = [f for f in os.listdir(REPORTS_DIR) if f.startswith("report_") and f.endswith(".json")]

    total_public = 0
    total_private = 0
    users = set()
    channels = {}
    user_stats = {}

    for fname in reports:
        try:
            with open(os.path.join(REPORTS_DIR, fname), "r") as f:
                data = json.load(f)
        except Exception as e:
            # Captura exceções para relatórios incompletos ou corrompidos.
            print(f"{RED}❌ Erro ao processar relatório {fname}: {e}{RESET}")
            continue

        users.add(data.get("user"))

        # Processa mensagens enviadas (se o bot foi corrigido para salvar objetos, esta lógica precisa ser adaptada)
        for msg in data.get("sent_messages", []):
            # Se for string (lógica antiga)
            if isinstance(msg, str):
                 if "(privada)" in msg:
                    total_private += 1
                 else:
                    total_public += 1
            # Se for objeto (lógica nova com timestamp)
            elif isinstance(msg, dict):
                 if msg.get("type") == "privada":
                    total_private += 1
                 else:
                    total_public += 1

        for msg in data.get("received_messages", []):
            mtype = msg.get("type")
            if mtype == "privada":
                total_private += 1
            elif (mtype == "pública" or mtype == "publica") and msg.get("channel"):
                total_public += 1
                ch = msg["channel"]
                channels[ch] = channels.get(ch, 0) + 1

            sender = msg.get("from")
            if sender:
                user_stats[sender] = user_stats.get(sender, 0) + 1

    summary = {
        "total_users": len(users),
        "total_reports": len(reports),
        "total_messages_public": total_public,
        "total_messages_private": total_private,
        "top_channels": dict(sorted(channels.items(), key=lambda x: x[1], reverse=True)[:5]),
        "top_users": dict(sorted(user_stats.items(), key=lambda x: x[1], reverse=True)[:5]),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"{CYAN}📊 Resumo global atualizado em {summary_path} ({len(reports)} relatórios agregados){RESET}")

# === GARANTIR ARQUIVOS BÁSICOS ===
for f in [USERS_FILE, CHANNELS_FILE, MESSAGES_FILE]:
    if not os.path.exists(f):
        save_data(f, [])

# === INICIAR ZMQ ===
ctx = zmq.Context()
rep = ctx.socket(zmq.REP)
rep.bind("tcp://*:5556")

pub = ctx.socket(zmq.PUB)
pub.connect("tcp://proxy:5557")

print(f"{BOLD}{CYAN}🧠 Servidor iniciado com suporte a canais, mensagens privadas e geração automática de summary.json{RESET}\n")

# ---------------------------------------------------------------------------------------
# ALTERAÇÃO CRUCIAL: ATUALIZA O SUMÁRIO NO INÍCIO (QUANDO O SERVIDOR LOGA NO DOCKER)
# ---------------------------------------------------------------------------------------
print(f"{YELLOW}⏳ Verificando e atualizando resumo global na inicialização...{RESET}")
update_summary()
print(f"{GREEN}✅ Inicialização do sumário concluída.{RESET}")
# ---------------------------------------------------------------------------------------

# === LOOP PRINCIPAL ===
while True:
    msg = rep.recv_json()
    service = msg.get("service")
    data = msg.get("data", {})
    timestamp = datetime.now().isoformat(timespec="seconds")

    users = load_data(USERS_FILE)
    channels = load_data(CHANNELS_FILE)
    messages = load_data(MESSAGES_FILE)

    print(f"{GRAY}{log_time()} {MAGENTA}Requisição:{RESET} {service}")

    if service == "login":
        user = data["user"]
        if user not in users:
            users.append(user)
            save_data(USERS_FILE, users)
            print(f"{GREEN}👤 Novo usuário registrado:{RESET} {user}")
        rep.send_json({"data": {"status": "OK"}})

    elif service == "channel":
        ch = data["channel"]
        user = data["user"]
        if ch not in channels:
            channels.append(ch)
            save_data(CHANNELS_FILE, channels)
            print(f"{GREEN}📡 Canal criado:{RESET} {ch}")
        rep.send_json({"data": {"status": "OK"}})

    elif service == "publish":
        user = data["user"]
        channel = data["channel"]
        message = data["message"]

        pub.send_string(f"{channel} [{user}]: {message}")

        messages.append({
            "type": "public",
            "from": user,
            "to": channel,
            "message": message,
            "timestamp": timestamp
        })
        save_data(MESSAGES_FILE, messages)

        print(f"{YELLOW}💬 {user} publicou em {channel}:{RESET} \"{message}\"")

        # Atualiza summary global
        update_summary()

        rep.send_json({"data": {"status": "OK"}})

    elif service == "message":
        src = data["src"]
        dst = data["dst"]
        message = data["message"]

        pub.send_string(f"{dst} [Privado de {src}]: {message}")

        messages.append({
            "type": "private",
            "from": src,
            "to": dst,
            "message": message,
            "timestamp": timestamp
        })
        save_data(MESSAGES_FILE, messages)

        print(f"{MAGENTA}✉️  {src} enviou mensagem privada para {dst}:{RESET} \"{message}\"")

        # Atualiza summary global
        update_summary()

        rep.send_json({"data": {"status": "OK"}})

    elif service == "report":
        # Envia o conteúdo do summary.json
        summary_path = os.path.join(REPORTS_DIR, "summary.json")
        if os.path.exists(summary_path):
            with open(summary_path, "r") as f:
                summary_data = json.load(f)
            rep.send_json({"data": summary_data})
        else:
            rep.send_json({"data": {"error": "summary.json não encontrado"}})

    else:
        rep.send_json({"data": {"status": "desconhecido"}})