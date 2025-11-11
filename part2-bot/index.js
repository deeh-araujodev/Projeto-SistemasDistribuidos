const zmq = require("zeromq");
const fs = require("fs");
const path = require("path");
const { randomInt } = require("crypto");

const REQ_ADDR = "tcp://server:5556";
const SUB_ADDR = "tcp://proxy:5558";

const users = [
  "Ana", "Bruno", "Carlos", "Diana", "Eduardo", "Maria",
  "Pedro", "Marcela", "Leticia", "Val", "Monica", "Sara",
  "Arthur", "Luisa", "Sonia", "Laura", "Anderson"
];
const channels = [
  "Resenha", "Desenvolvedores", "Games", "Musica", "Filmes",
  "Doramas", "Trilhas", "Corridas", "Ciclistas", "Cozinha"
];
const mensagens = [
  "Olá pessoal!", "Alguém aí?", "Trabalhando no projeto 😎",
  "Hoje está um dia agradável!", "Quero ir à praia", "Deus é fiel",
  "Testando mensagens automáticas", "Pub/Sub funcionando!",
  "Vamos jogar depois?", "Bug resolvido 🎉", "Mensagem de teste",
  "Enviando mais uma!"
];

const MAX_CHANNELS_PER_BOT = 2;
const REPORTS_DIR = path.join("data", "reports");
if (!fs.existsSync(REPORTS_DIR)) fs.mkdirSync(REPORTS_DIR, { recursive: true });

async function main() {
  const username = users[randomInt(users.length)];
  console.log(`🤖 Bot iniciado como: ${username}`);

  const req = new zmq.Request();
  await req.connect(REQ_ADDR);

  const sub = new zmq.Subscriber();
  await sub.connect(SUB_ADDR);

  const report = {
    user: username,
    start_time: new Date().toISOString(),
    channels_joined: [],
    channels_created: [],
    sent_messages: [],
    received_messages: []
  };

  // === LOGIN ===
  await req.send(JSON.stringify({ service: "login", data: { user: username } }));
  await req.receive();

  // === ENTRA EM CANAIS ===
  const myChannels = [];
  while (myChannels.length < randomInt(1, MAX_CHANNELS_PER_BOT + 1)) {
    const c = channels[randomInt(channels.length)];
    if (!myChannels.includes(c)) myChannels.push(c);
  }
  console.log(`📡 ${username} entrou nos canais: ${myChannels.join(", ")}`);
  report.channels_joined = myChannels;

  for (const ch of myChannels) {
    await req.send(JSON.stringify({ service: "channel", data: { channel: ch, user: username } }));
    const [reply] = await req.receive();
    const res = JSON.parse(reply.toString());
    if (res.data.status === "OK") report.channels_created.push(ch);
  }

  // === SUBSCRIBE: nome do usuário + canais ===
  sub.subscribe(username);
  myChannels.forEach(c => sub.subscribe(c));

  // === RECEBIMENTO ===
  (async () => {
    for await (const [msg] of sub) {
      const m = msg.toString();
      let tipo = "pública";
      let origem = "";
      let canalOuUser = "";

      const privado = /\[Privado de ([^\]]+)\]: (.+)/.exec(m);
      const publico = /^(\w+) \[([^\]]+)\]: (.+)/.exec(m);

      if (privado) {
        tipo = "privada";
        origem = privado[1];
        canalOuUser = username;
        console.log(`💌 (${username}) recebeu mensagem privada de ${origem}`);
        report.received_messages.push({
          from: origem,
          type: tipo,
          content: privado[2],
          timestamp: new Date().toISOString()
        });
      } else if (publico) {
        canalOuUser = publico[1];
        origem = publico[2];
        console.log(`📥 (${username}) recebeu mensagem pública de ${origem} no canal ${canalOuUser}`);
        report.received_messages.push({
          from: origem,
          type: tipo,
          channel: canalOuUser,
          content: publico[3],
          timestamp: new Date().toISOString()
        });
      } else {
        console.log(`📨 (${username}) recebeu: ${m}`);
        report.received_messages.push({
          type: "desconhecido",
          content: m,
          timestamp: new Date().toISOString()
        });
      }
    }
  })();

  // === SALVAMENTO AUTOMÁTICO A CADA 10 SEGUNDOS ===
  async function saveReport() {
    try {
      report.end_time = new Date().toISOString();
      const jsonPath = path.join(REPORTS_DIR, `report_${username}.json`);
      const txtPath = path.join(REPORTS_DIR, `report_${username}.txt`);

      fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2));

      const txt = [
        `🧾 Relatório de ${username}`,
        `Entrou nos canais: ${report.channels_joined.join(", ")}`,
        `Criou canais: ${report.channels_created.join(", ")}`,
        ``,
        `📤 Mensagens enviadas:`,
        ...report.sent_messages.map(m => `  - ${m}`),
        ``,
        `📥 Mensagens recebidas:`,
        ...report.received_messages.map(m =>
          m.type === "privada"
            ? `  - (Privada) de ${m.from}: "${m.content}"`
            : `  - (Pública) de ${m.from} em ${m.channel}: "${m.content}"`
        )
      ].join("\n");

      fs.writeFileSync(txtPath, txt);
      console.log(`📁 [${username}] Relatório salvo`);
    } catch (err) {
      console.error(`❌ Erro ao salvar relatório de ${username}:`, err);
    }
  }

  // chama a cada 10 segundos
  setInterval(saveReport, 10000);

  // === LOOP DE ENVIO ===
  let running = true;
  process.on("SIGINT", async () => {
    running = false;
    await saveReport();
    process.exit(0);
  });

  const delay = randomInt(5, 15) * 1000;
  console.log(`⏳ ${username} aguardando ${delay / 1000}s antes de enviar mensagens...`);
  await new Promise(r => setTimeout(r, delay));

  while (running) {
    const isPrivate = randomInt(100) < 30;
    const text = mensagens[randomInt(mensagens.length)];
    let msg;

    if (isPrivate) {
      const dst = users[randomInt(users.length)];
      if (dst !== username) {
        msg = { service: "message", data: { src: username, dst, message: text } };
        console.log(`📨 (${username}) enviou mensagem privada para ${dst}`);
        report.sent_messages.push(`(privada) para ${dst}: "${text}"`);
      }
    } else {
      const ch = myChannels[randomInt(myChannels.length)];
      msg = { service: "publish", data: { user: username, channel: ch, message: text } };
      console.log(`💬 (${username}) enviou mensagem pública para canal ${ch}`);
      report.sent_messages.push(`(pública) para canal ${ch}: "${text}"`);
    }

    if (msg) {
      await req.send(JSON.stringify(msg));
      await req.receive();
    }

    await new Promise(r => setTimeout(r, randomInt(2000, 4000)));
  }
}

main().catch(console.error);
