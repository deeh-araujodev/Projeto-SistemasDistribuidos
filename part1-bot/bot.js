import zmq from "zeromq";

const SERVER_ADDR = "tcp://server:5556";

function now() {
  return Date.now();
}

async function sendRequest(socket, msg) {
  const data = Buffer.from(JSON.stringify(msg));
  await socket.send(data);
  const [replyBytes] = await socket.receive();
  return JSON.parse(replyBytes.toString());
}

async function main() {
  const sock = new zmq.Request();

  console.log("🤖 Bot conectando ao servidor:", SERVER_ADDR);
  sock.connect(SERVER_ADDR);

  // 1️⃣ LOGIN
  const loginReq = {
    service: "login",
    data: {
      user: "bot123",
      timestamp: now(),
    },
  };
  console.log("📤 Enviando login...");
  let resp = await sendRequest(sock, loginReq);
  console.log("📩 Resposta login:", resp);

  // 2️⃣ LISTAR USUÁRIOS
  const usersReq = {
    service: "users",
    data: { timestamp: now() },
  };
  console.log("📤 Listando usuários...");
  resp = await sendRequest(sock, usersReq);
  console.log("📩 Usuários:", resp.data.users);

  // 3️⃣ CRIAR CANAL ESPECIAL DO BOT
  const channelReq = {
    service: "channel",
    data: {
      channel: "bot-zone",
      timestamp: now(),
    },
  };
  console.log("📤 Criando canal bot-zone...");
  resp = await sendRequest(sock, channelReq);
  console.log("📩 Resposta criação canal:", resp);

  // 4️⃣ LISTAR CANAIS
  const channelsReq = {
    service: "channels",
    data: { timestamp: now() },
  };
  console.log("📤 Listando canais...");
  resp = await sendRequest(sock, channelsReq);
  console.log("📩 Canais disponíveis:", resp.data.channels);

  console.log("✅ Bot finalizado com sucesso!");
}

main().catch((err) => {
  console.error("Erro no bot:", err);
});
