FROM node:18
WORKDIR /app
COPY index.js .
RUN npm install zeromq msgpack-lite
CMD ["node", "index.js"]
