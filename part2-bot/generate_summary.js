const fs = require("fs");
const path = require("path");

const REPORTS_DIR = path.join("data", "reports");
const SUMMARY_PATH = path.join(REPORTS_DIR, "summary.json");

function generateSummary() {
  const reports = fs.readdirSync(REPORTS_DIR)
    .filter(f => f.startsWith("report_") && f.endsWith(".json"))
    .map(f => JSON.parse(fs.readFileSync(path.join(REPORTS_DIR, f), "utf-8")));

  let totalPublic = 0;
  let totalPrivate = 0;
  let users = new Set();
  let channels = new Map();
  let userStats = {};

  for (const r of reports) {
    users.add(r.user);

    // Contar mensagens enviadas
    for (const msg of r.sent_messages) {
      if (msg.includes("(privada)")) totalPrivate++;
      else totalPublic++;
    }

    // Contar mensagens recebidas
    for (const msg of r.received_messages) {
      if (msg.type === "privada") totalPrivate++;
      else if (msg.type === "pública" && msg.channel) {
        totalPublic++;
        channels.set(msg.channel, (channels.get(msg.channel) || 0) + 1);
      }

      userStats[msg.from] = (userStats[msg.from] || 0) + 1;
    }
  }

  const summary = {
    total_users: users.size,
    total_reports: reports.length,
    total_messages_public: totalPublic,
    total_messages_private: totalPrivate,
    top_channels: Object.fromEntries(
      [...channels.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5)
    ),
    top_users: Object.fromEntries(
      Object.entries(userStats).sort((a, b) => b[1] - a[1]).slice(0, 5)
    ),
    generated_at: new Date().toISOString()
  };

  fs.writeFileSync(SUMMARY_PATH, JSON.stringify(summary, null, 2));
  console.log(`📊 Resumo global atualizado em ${SUMMARY_PATH}`);
}

generateSummary();
