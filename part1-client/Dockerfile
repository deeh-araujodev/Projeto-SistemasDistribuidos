FROM golang:1.22-alpine

WORKDIR /app

RUN apk add --no-cache zeromq-dev pkgconfig gcc musl-dev

COPY go.mod .
RUN go mod download

COPY . .

RUN go build -o client main.go

CMD ["./client"]
