const zmq = require("zeromq");
const msgpack = require("msgpack-lite");
const fs = require("fs");
const path = require("path");
const { randomInt } = require("crypto");

const REQ_ADDR = "tcp://server:5556";
const SUB_ADDR = "tcp://proxy:5558";

const users = ["Ana","Bruno","Carlos","Diana","Eduardo","Maria","Pedro","Marcela","Leticia","Val","Monica","Sara","Arthur","Luisa","Sonia","Laura","Anderson"];
const channels = ["Resenha","Desenvolvedores","Games","Musica","Filmes","Doramas","Trilhas","Corridas","Ciclistas","Cozinha"];
const mensagens = ["Olá pessoal!","Alguém aí?","Trabalhando no projeto 😎","Hoje está um dia agradável!","Quero ir à praia","Deus é fiel","Testando mensagens automáticas","Pub/Sub funcionando!","Vamos jogar depois?","Bug resolvido 🎉","Mensagem de teste","Enviando mais uma!"];

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

    // LOGIN (REQ/REP)
    await req.send(msgpack.encode({ service: "login", data: { user: username } }));
    await req.receive();

    // JOIN (REQ/REP)
    const myChannels = [];
    while (myChannels.length < randomInt(1, MAX_CHANNELS_PER_BOT + 1)) {
        const c = channels[randomInt(channels.length)];
        if (!myChannels.includes(c)) myChannels.push(c);
    }
    console.log(`📡 ${username} entrou nos canais: ${myChannels.join(", ")}`);
    report.channels_joined = myChannels;

    for (const ch of myChannels) {
        await req.send(msgpack.encode({ service: "channel", data: { channel: ch, user: username } }));
        const [reply] = await req.receive();
        const res = msgpack.decode(reply);
        if (res.data.status === "OK") report.channels_created.push(ch);
    }

    // SUBSCRIBE (Assinatura)
    sub.subscribe(username);
    myChannels.forEach(c => sub.subscribe(c));
    await new Promise(r => setTimeout(r, 500)); // Delay para garantir subscrição

    // RECEBER MENSAGENS (SUB) - LÓGICA MESSAGEPACK CORRIGIDA
    (async () => {
        for await (const frames of sub) { // Recebe múltiplos frames (tópico + payload)
            const topic = frames[0].toString(); // Tópico (string)
            const payload = frames[1]; // Payload (Buffer binário)
            
            try {
                const messageData = msgpack.decode(payload); // Deserializa o MessagePack
                const timestamp = new Date().toISOString();
                
                if (messageData.type === "privada") {
                    console.log(`💌 (${username}) recebeu privada de ${messageData.from}`);
                    report.received_messages.push({ 
                        type: "privada", 
                        from: messageData.from, 
                        content: messageData.message, 
                        timestamp 
                    });
                } else if (messageData.type === "publica") {
                    console.log(`📥 (${username}) recebeu pública de ${messageData.from} no canal ${messageData.channel}`);
                    report.received_messages.push({ 
                        type: "pública", 
                        from: messageData.from, 
                        channel: messageData.channel, 
                        content: messageData.message, 
                        timestamp 
                    });
                }
            } catch (e) {
                console.error(`❌ Erro de MessagePack no SUB:`, e);
            }
        }
    })();

    async function saveReport() {
        report.end_time = new Date().toISOString();
        const jsonPath = path.join(REPORTS_DIR, `report_${username}.json`);
        const txtPath = path.join(REPORTS_DIR, `report_${username}.txt`);

        fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2));

        const formatTime = (isoString) => {
            if (!isoString) return 's/hora';
            return new Date(isoString).toLocaleTimeString('pt-BR');
        };

        const txt = [
            `🧾 Relatório de ${username}`,
            `Entrou nos canais: ${report.channels_joined.join(", ")}`,
            `Criou canais: ${report.channels_created.join(", ")}`,
            ``,
            `📤 Mensagens enviadas:`,
            ...report.sent_messages.map(m =>
                m.type === "privada"
                    ? `  - [${formatTime(m.timestamp)}] (privada) para ${m.to}: "${m.content}"`
                    : `  - [${formatTime(m.timestamp)}] (pública) para canal ${m.to}: "${m.content}"`
            ),
            ``,
            `📥 Mensagens recebidas:`,
            ...report.received_messages.map(m =>
                m.type === "privada"
                    ? `  - [${formatTime(m.timestamp)}] (Privada) de ${m.from}: "${m.content}"`
                    : `  - [${formatTime(m.timestamp)}] (Pública) de ${m.from} em ${m.channel}: "${m.content}"`
            )
        ].join("\n");

        fs.writeFileSync(txtPath, txt);
        console.log(`📁 [${username}] Relatório salvo`);
    }
    
    // Lógica SIGINT para garantir salvamento no encerramento
    process.on("SIGINT", async () => {
        console.log(`Stopping bot... Saving report.`);
        await saveReport();
        process.exit(0);
    });

    setInterval(saveReport, 10000);

    // ENVIO (LOOP)
    const delay = randomInt(5, 15) * 1000;
    console.log(`⏳ ${username} aguardando ${delay / 1000}s...`);
    await new Promise(r => setTimeout(r, delay));

    while (true) {
        const isPrivate = randomInt(100) < 30;
        const text = mensagens[randomInt(mensagens.length)]; // SINTAXE CORRIGIDA
        let msg;

        if (isPrivate) {
            const dst = users[randomInt(users.length)];
            if (dst !== username) {
                msg = { service: "message", data: { src: username, dst, message: text } };
                // Envia MessagePack
                await req.send(msgpack.encode(msg));
                await req.receive();

                // Salva no relatório
                report.sent_messages.push({
                    type: "privada",
                    to: dst,
                    content: text,
                    timestamp: new Date().toISOString()
                });
            }
        } else {
            const ch = myChannels[randomInt(myChannels.length)];
            msg = { service: "publish", data: { user: username, channel: ch, message: text } };
            // Envia MessagePack
            await req.send(msgpack.encode(msg));
            await req.receive();

            // Salva no relatório
            report.sent_messages.push({
                type: "publica",
                to: ch,
                content: text,
                timestamp: new Date().toISOString()
            });
        }

        await new Promise(r => setTimeout(r, randomInt(2000, 4000)));
    }
}

main().catch(console.error);