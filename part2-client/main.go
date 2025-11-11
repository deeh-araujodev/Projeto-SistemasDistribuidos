package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"strings"
	"time"

	zmq "github.com/pebbe/zmq4"
)

type Message struct {
	Service string                 `json:"service"`
	Data    map[string]interface{} `json:"data"`
}

func main() {
	rand.Seed(time.Now().UnixNano())

	req, err := zmq.NewSocket(zmq.REQ)
	if err != nil {
		log.Fatal(err)
	}
	defer req.Close()

	req.Connect("tcp://localhost:5556")
	fmt.Println("💻 Cliente Go conectado ao servidor JSON")

	// ==== CONFIGURAÇÃO ====
	userList := "Ana,Bruno,Carlos,Diana,Eduardo,Fernanda,Gabriel,Helena,Igor,Juliana,Lucas,Mariana,Nicolas,Olivia,Paulo,Rafaela,Sofia,Thiago,Vanessa,William"
	channelList := "geral,dev,games,random,suporte,offtopic"

	// Converte as strings separadas por vírgula em slices
	users := strings.Split(userList, ",")
	channels := strings.Split(channelList, ",")

	// Seleciona aleatoriamente alguns usuários (ex: 5 por execução)
	randomUsers := getRandomSubset(users, 5)

	// ==== TESTE 1: CRIAR USUÁRIOS ALEATÓRIOS ====
	fmt.Println("\n👤 Criando usuários...")
	for _, user := range randomUsers {
		msg := Message{
			Service: "login",
			Data: map[string]interface{}{
				"user":      strings.TrimSpace(user),
				"timestamp": time.Now().Format(time.RFC3339),
			},
		}
		sendAndReceive(req, msg)
	}

	// ==== TESTE 2: LISTAR USUÁRIOS ====
	fmt.Println("\n📋 Listando todos os usuários...")
	sendAndReceive(req, Message{
		Service: "users",
		Data: map[string]interface{}{
			"timestamp": time.Now().Format(time.RFC3339),
		},
	})

	// ==== TESTE 3: CRIAR CANAIS ====
	fmt.Println("\n💬 Criando canais...")
	for _, ch := range channels {
		msg := Message{
			Service: "channel",
			Data: map[string]interface{}{
				"channel":   strings.TrimSpace(ch),
				"timestamp": time.Now().Format(time.RFC3339),
			},
		}
		sendAndReceive(req, msg)
	}

	// ==== TESTE 4: LISTAR CANAIS ====
	fmt.Println("\n📢 Listando todos os canais...")
	sendAndReceive(req, Message{
		Service: "channels",
		Data: map[string]interface{}{
			"timestamp": time.Now().Format(time.RFC3339),
		},
	})

	fmt.Println("\n✅ Testes finalizados com sucesso!")
}

func sendAndReceive(req *zmq.Socket, msg Message) {
	bytes, _ := json.Marshal(msg)
	req.SendBytes(bytes, 0)
	replyBytes, _ := req.RecvBytes(0)

	var reply Message
	json.Unmarshal(replyBytes, &reply)

	fmt.Printf("📩 [%s] → %v\n", msg.Service, reply.Data)
}

// getRandomSubset escolhe 'n' elementos aleatórios de uma lista
func getRandomSubset(list []string, n int) []string {
	if n >= len(list) {
		return list
	}
	rand.Shuffle(len(list), func(i, j int) {
		list[i], list[j] = list[j], list[i]
	})
	return list[:n]
}
