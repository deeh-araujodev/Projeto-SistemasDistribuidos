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
	// Inicializa a semente aleatória para seleção de usuários
	rand.Seed(time.Now().UnixNano())

	// Configura o socket ZeroMQ REQ (Request)
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

	// --- LÓGICA DE IMPRESSÃO APRIMORADA ---
	status, _ := reply.Data["status"].(string) // Tenta extrair o status da resposta

	switch msg.Service {
	case "login":
		// Obtém o nome do usuário da mensagem de requisição original
		userName, _ := msg.Data["user"].(string)
		if status == "sucesso" {
			fmt.Printf("📩 [Login] Usuário: **%s**, Status: **Usuário criado com sucesso**\n", userName)
		} else {
			// Caso de falha, imprime a resposta bruta do servidor
			fmt.Printf("📩 [Login] Usuário: %s, Resposta do Servidor: %v\n", userName, reply.Data)
		}
	case "channel":
		// Obtém o nome do canal da mensagem de requisição original
		channelName, _ := msg.Data["channel"].(string)
		if status == "sucesso" {
			fmt.Printf("📩 [Channel] Canal: **%s**, Status: **Canal criado com sucesso**\n", channelName)
		} else {
			// Caso de falha
			fmt.Printf("📩 [Channel] Canal: %s, Resposta do Servidor: %v\n", channelName, reply.Data)
		}
	case "users", "channels":
		// Mantém a lógica de formatação de listas por vírgula para listagens
		if msg.Service == "users" {
			if userList, ok := reply.Data["users"].([]interface{}); ok {
				var formattedUsers []string
				for _, user := range userList {
					if uStr, isStr := user.(string); isStr {
						formattedUsers = append(formattedUsers, uStr)
					}
				}
				reply.Data["users"] = strings.Join(formattedUsers, ", ")
			}
		} else if msg.Service == "channels" {
			if channelList, ok := reply.Data["channels"].([]interface{}); ok {
				var formattedChannels []string
				for _, ch := range channelList {
					if chStr, isStr := ch.(string); isStr {
						formattedChannels = append(formattedChannels, chStr)
					}
				}
				reply.Data["channels"] = strings.Join(formattedChannels, ", ")
			}
		}
		// Imprime a saída formatada para as listagens
		fmt.Printf("📩 [%s] → %v\n", msg.Service, reply.Data)
	default:
		// Saída padrão para outros serviços
		fmt.Printf("📩 [%s] → %v\n", msg.Service, reply.Data)
	}
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
