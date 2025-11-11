FROM node:18

WORKDIR /app

# 1. Copia o arquivo principal
COPY index.js .

# 2. Instala o ZeroMQ
RUN npm install zeromq

# 3. Executa o bot
CMD ["node", "index.js"]