# Use uma versão mais nova do Go (1.25 ou superior)
FROM golang:1.22-alpine AS build

WORKDIR /app

COPY . .

# 💡 CORREÇÃO AQUI: Instalar as ferramentas C/C++ e o DEV ZeroMQ
RUN apk add --no-cache build-base g++ zeromq-dev 

# Garante que o Go baixe automaticamente a toolchain se precisar
ENV GOTOOLCHAIN=auto

# Inicializa o módulo Go (caso ainda não exista)
RUN [ ! -f go.mod ] && go mod init server || true

# Instala dependência do ZeroMQ
RUN go get github.com/pebbe/zmq4
RUN go mod tidy

# Compila o servidor
RUN go build -o server .

EXPOSE 5555 5556

CMD ["./server"]