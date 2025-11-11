FROM golang:1.22-alpine
WORKDIR /app
COPY . .
RUN apk add --no-cache build-base zeromq-dev
RUN go mod init client || true
RUN go get github.com/pebbe/zmq4 github.com/vmihailenco/msgpack/v5
RUN go build -o client .
CMD ["./client"]
