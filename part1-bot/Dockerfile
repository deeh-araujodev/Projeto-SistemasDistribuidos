FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache zeromq-dev pkgconfig g++ make python3

COPY package*.json ./
RUN npm install

COPY . .

CMD ["node", "bot.js"]
