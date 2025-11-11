import zmq
import json
import os
import time
from datetime import datetime

# === CORES ANSI ===
RESET = "\033[0m"
BOLD = "\033[1m"
GRAY = "\033[90m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"

CHANNEL_COLORS = {
    "geral": CYAN,
    "dev": BLUE,
    "games": GREEN,
    "random": YELLOW,
    "suporte": MAGENTA,
    "offtopic": WHITE,
}

def color_channel(name):
    color = CHANNEL_COLORS.get(name, GRAY)
    return f"{color}#{name}{RESET}"

# === PERSISTÊNCIA ===
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
MESSAGES_FILE = os.path.join(DATA_DIR, "messages.json")

os.makedirs(DATA_DIR, exist_ok=True)

def load_data(file):
    if not os.path.exists(file):
        return []
    with open(file, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Arquivo corrompido: {file}")
            return []

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

for f in [USERS_FILE, CHANNELS_FILE, MESSAGES_FILE]:
    if not os.path.exists(f):
        save_data(f, [])

# === ZMQ ===
context = zmq.Context()
rep_socket = context.socket(zmq.REP)
rep_socket.bind("tcp://*:5556")

pub_socket = context.socket(zmq.PUB)
pub_socket.connect("tcp://proxy:5557")

print(f"{BOLD}{CYAN}🧠 Servidor parte 2 iniciado (REQ/REP + PUB/SUB){RESET}\n")

while True:
    try:
        msg = rep_socket.recv_json()
    except Exception as e:
        print(f"{RED}❌ Erro ao receber mensagem: {e}{RESET}")
        break

    service = msg.get("service")
    data = msg.get("data", {})
    response = {"service": service, "data": {}}

    users = load_data(USERS_FILE)
    channels = load_data(CHANNELS_FILE)
    messages = load_data(MESSAGES_FILE)

    timestamp = datetime.now().isoformat(timespec='seconds')
    print(f"\n{GRAY}[{time.strftime('%H:%M:%S')}] 🔧 Requisição:{RESET} {service}")

    # === LOGIN ===
    if service == "login":
        user = data.get("user")
        if user not in users:
            users.append(user)
            save_data(USERS_FILE, users)
            print(f"{GREEN}👤 Novo usuário registrado:{RESET} {user}")
        response["data"] = {"status": "sucesso", "timestamp": timestamp}

    # === USERS ===
    elif service == "users":
        response["data"] = {"users": users, "timestamp": timestamp}

    # === CHANNEL ===
    elif service == "channel":
        channel = data.get("channel")
        if channel not in channels:
            channels.append(channel)
            save_data(CHANNELS_FILE, channels)
            print(f"{GREEN}📡 Canal criado:{RESET} {color_channel(channel)}")
        response["data"] = {"status": "OK", "timestamp": timestamp}

    # === PUBLICAR ===
    elif service == "publish":
        user = data.get("user")
        channel = data.get("channel")
        message = data.get("message")
        if channel not in channels:
            response["data"] = {"status": "erro", "message": "Canal inexistente"}
        else:
            formatted = f"{channel} [{user}]: {message}"
            pub_socket.send_string(formatted)
            messages.append({"type": "channel", "from": user, "to": channel, "message": message, "timestamp": timestamp})
            save_data(MESSAGES_FILE, messages)
            print(f"{YELLOW}💬 {user} publicou em {color_channel(channel)}:{RESET} {message}")
            response["data"] = {"status": "OK", "timestamp": timestamp}

    # === PRIVADO ===
    elif service == "message":
        src = data.get("src")
        dst = data.get("dst")
        message = data.get("message")
        if dst not in users:
            response["data"] = {"status": "erro", "message": "Usuário inexistente"}
        else:
            formatted = f"{dst} [Privado de {src}]: {message}"
            pub_socket.send_string(formatted)
            messages.append({"type": "private", "from": src, "to": dst, "message": message, "timestamp": timestamp})
            save_data(MESSAGES_FILE, messages)
            print(f"{MAGENTA}✉️ {src} → {dst}:{RESET} {message}")
            response["data"] = {"status": "OK", "timestamp": timestamp}

    try:
        rep_socket.send_json(response)
    except Exception as e:
        print(f"{RED}❌ Erro ao responder: {e}{RESET}")
