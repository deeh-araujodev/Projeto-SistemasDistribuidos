package main

import (
	"fmt"
	"math/rand"
	"strings"
	"time"

	"github.com/vmihailenco/msgpack/v5"
	zmq "github.com/pebbe/zmq4"
)

type Message struct {
	Service string                 `msgpack:"service"`
	Data    map[string]interface{} `msgpack:"data"`
}

func main() {
	// Remover log e strings não utilizados no código principal
	
	rand.Seed(time.Now().UnixNano())
	req, _ := zmq.NewSocket(zmq.REQ)
	defer req.Close()
	req.Connect("tcp://server:5556")
	fmt.Println("💻 Cliente Go conectado ao servidor MessagePack")

	users := strings.Split("Ana,Bruno,Carlos,Diana,Eduardo", ",")
	channels := strings.Split("Resenha,Games,Filmes", ",")

	for _, user := range users {
		sendAndReceive(req, Message{"login", map[string]interface{}{"user": user}})
	}

	for _, ch := range channels {
		sendAndReceive(req, Message{"channel", map[string]interface{}{"channel": ch, "user": "Admin"}})
	}

	fmt.Println("✅ Testes concluídos.")
}

func sendAndReceive(req *zmq.Socket, msg Message) {
	bytes, _ := msgpack.Marshal(msg)
	req.SendBytes(bytes, 0)
	replyBytes, _ := req.RecvBytes(0)
	var reply Message
	msgpack.Unmarshal(replyBytes, &reply)
	fmt.Printf("📩 [%s] → %v\n", msg.Service, reply.Data)
}