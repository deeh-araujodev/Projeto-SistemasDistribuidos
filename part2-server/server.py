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

for f in [USERS_FILE, CHANNELS_FILE, MESSAGES_FILE]:
    if not os.path.exists(f):
        save_data(f, [])

# === INICIAR ZMQ ===
ctx = zmq.Context()
rep = ctx.socket(zmq.REP)
rep.bind("tcp://*:5556")

pub = ctx.socket(zmq.PUB)
pub.connect("tcp://proxy:5557")

print(f"{BOLD}{CYAN}🧠 Servidor iniciado com suporte a canais e mensagens privadas{RESET}\n")

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
        rep.send_json({"data": {"status": "OK"}})

    elif service == "message":
        src = data["src"]
        dst = data["dst"]
        message = data["message"]

        # Publica APENAS para o tópico do destinatário
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
        rep.send_json({"data": {"status": "OK"}})

    else:
        rep.send_json({"data": {"status": "desconhecido"}})
