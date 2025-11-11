import zmq
import msgpack
import json
import os
import time
from datetime import datetime
# Adicionando um import ausente para Time Formatting
from time import strftime

# === CONFIGURAÇÕES ===
DATA_DIR = "data"
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
MESSAGES_FILE = os.path.join(DATA_DIR, "messages.json")

# A CRIAÇÃO DE PASTAS PODE VIR IMEDIATAMENTE DEPOIS (Linha 17 onde o erro ocorreu)
os.makedirs(DATA_DIR, exist_ok=True) 
os.makedirs(REPORTS_DIR, exist_ok=True)

# === CORES ===
# Nota: Removidas para foco no código, adicione de volta se precisar

# Garante que as pastas existam
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def load_data(file):
    if not os.path.exists(file):
        return []
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return []

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

# === Resumo global (Sem Alteração na Lógica de Leitura/Escrita de JSON) ===
def update_summary():
    summary_path = os.path.join(REPORTS_DIR, "summary.json")
    reports = [f for f in os.listdir(REPORTS_DIR) if f.startswith("report_") and f.endswith(".json")]
    total_public = total_private = 0
    users, channels, user_stats = set(), {}, {}

    for fname in reports:
        try:
            with open(os.path.join(REPORTS_DIR, fname), "r") as f:
                data = json.load(f)
        except:
            continue
        
        # ... (Lógica de contagem de mensagens permanece a mesma, pois lê JSON)
        # ...

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
    print(f"📊 summary.json atualizado ({len(reports)} relatórios)")

# === ZMQ SETUP ===
ctx = zmq.Context()
rep = ctx.socket(zmq.REP)
rep.bind("tcp://*:5556")

pub = ctx.socket(zmq.PUB)
pub.connect("tcp://proxy:5557")

print("🧠 Servidor iniciado com suporte a MessagePack")
update_summary()

while True:
    packed_msg = rep.recv()
    msg = msgpack.unpackb(packed_msg, raw=False)

    service = msg.get("service")
    data = msg.get("data", {})
    timestamp = datetime.now().isoformat(timespec="seconds")

    users = load_data(USERS_FILE)
    channels = load_data(CHANNELS_FILE)
    messages = load_data(MESSAGES_FILE)

    # Função auxiliar para empacotar respostas REP
    def send_rep_ok():
        # Usamos use_bin_type=True para evitar problemas de codificação
        rep.send(msgpack.packb({"data": {"status": "OK"}}, use_bin_type=True))
        
    # --- Login ---
    if service == "login":
        user = data["user"]
        if user not in users:
            users.append(user)
            save_data(USERS_FILE, users)
        send_rep_ok()

    # --- Channel ---
    elif service == "channel":
        ch = data["channel"]
        user = data["user"]
        if ch not in channels:
            channels.append(ch)
            save_data(CHANNELS_FILE, channels)
        send_rep_ok()

    # --- Publish (CORREÇÃO PUB/SUB) ---
    elif service == "publish":
        user = data["user"]
        channel = data["channel"]
        message = data["message"]
        
        # Payload completo a ser enviado via PUB (em MessagePack)
        pub_payload = {
            "type": "publica",
            "from": user,
            "channel": channel,
            "message": message
        }

        # 1. Envia o TÓPICO como string (ZMQ envelope)
        pub.send_string(channel, zmq.SNDMORE) 
        # 2. Envia o PAYLOAD como binário MessagePack (corpo)
        pub.send(msgpack.packb(pub_payload, use_bin_type=True)) 

        messages.append({"type": "public", "from": user, "to": channel, "message": message, "timestamp": timestamp})
        save_data(MESSAGES_FILE, messages)
        update_summary()
        send_rep_ok()

    # --- Message (CORREÇÃO PUB/SUB para Mensagens Privadas) ---
    elif service == "message":
        src = data["src"]
        dst = data["dst"]
        message = data["message"]

        # Payload completo a ser enviado via PUB (em MessagePack)
        pub_payload = {
            "type": "privada",
            "from": src,
            "to": dst,
            "message": message
        }
        
        # 1. Envia o DESTINATÁRIO (que é o tópico de subscrição) como string
        pub.send_string(dst, zmq.SNDMORE)
        # 2. Envia o PAYLOAD como binário MessagePack
        pub.send(msgpack.packb(pub_payload, use_bin_type=True))

        messages.append({"type": "private", "from": src, "to": dst, "message": message, "timestamp": timestamp})
        save_data(MESSAGES_FILE, messages)
        update_summary()
        send_rep_ok()

    # --- Report ---
    elif service == "report":
        summary_path = os.path.join(REPORTS_DIR, "summary.json")
        try:
            with open(summary_path, "r") as f:
                summary_data = json.load(f)
            rep.send(msgpack.packb({"data": summary_data}, use_bin_type=True))
        except FileNotFoundError:
            rep.send(msgpack.packb({"data": {"error": "summary.json not found"}}, use_bin_type=True))
        except Exception:
             rep.send(msgpack.packb({"data": {"error": "Error reading summary file"}}, use_bin_type=True))

    # --- Unknown ---
    else:
        rep.send(msgpack.packb({"data": {"status": "unknown"}}, use_bin_type=True))