import socket
import threading
import json
from datetime import datetime
import os

class ChatServer:
    def __init__(self, host='0.0.0.0', port=55555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen()
        self.server.settimeout(1)
        self.clients = {}
        self.running = False
        self.chat_history = []
        
        if os.path.exists('chat_history.json'):
            with open('chat_history.json', 'r') as chat:
                self.chat_history = json.load(chat)

    def save_chat_history(self):
        with open('chat_history.json', 'w') as chat:
            json.dump(self.chat_history, chat)

    def broadcast(self, message, sender=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        
        self.chat_history.append(formatted_msg)
        if len(self.chat_history) > 100:
            self.chat_history.pop(0)
        self.save_chat_history()
        
        for client_socket in list(self.clients.keys()):
            if client_socket != sender:
                try:
                    client_socket.send(formatted_msg.encode('utf-8'))
                except (ConnectionError, OSError):
                    self.remove_client(client_socket)

    def handle_client(self, client_socket):
        try:
            nickname = client_socket.recv(1024).decode('utf-8').strip()
                
            if not nickname or nickname in self.clients.values():
                client_socket.send("ERRO: Nickname inválido ou já em uso.".encode('utf-8'))
                client_socket.close()
                return

            self.clients[client_socket] = nickname
            self.broadcast(f"{nickname} entrou no chat!", client_socket)
            
            if self.chat_history:
                client_socket.send("\nHistórico de mensagens:\n".encode('utf-8'))
                for msg in self.chat_history[-10:]:
                    client_socket.send(f"{msg}\n".encode('utf-8'))
            
            client_socket.send(f"Bem-vindo, {nickname}! Comandos disponíveis: /quit, /list, /help".encode('utf-8'))

            while self.running:
                try:
                    message = client_socket.recv(1024).decode('utf-8').strip()
                except (ConnectionError, OSError):
                    break

                if not message:
                    continue
                    
                if message.lower() == '/quit':
                    break
                    
                elif message.lower() == '/list':
                    online_users = ", ".join(self.clients.values())
                    client_socket.send(f"Usuários online: {online_users}".encode('utf-8'))
                    
                elif message.lower() == '/help':
                    help_msg = """
                                Comandos disponíveis:
                                /quit - Sair do chat
                                /list - Listar usuários online
                                /help - Mostrar esta ajuda
                                """
                    client_socket.send(help_msg.encode('utf-8'))
                        
                else:
                    self.broadcast(f"{self.clients[client_socket]}: {message}", client_socket)
                    
        finally:
            self.remove_client(client_socket)

    def remove_client(self, client_socket):
        if client_socket in self.clients:
            nickname = self.clients[client_socket]
            del self.clients[client_socket]
            self.broadcast(f"{nickname} saiu do chat.", client_socket)
            try:
                client_socket.close()
            except Exception:
                pass

    def run(self):
        self.running = True
        print(f"Servidor rodando em {self.server.getsockname()}...")
        try:
            while self.running:
                try:
                    client_socket, addr = self.server.accept()
                    print(f"Conexão de {addr}")
                    threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
                except socket.timeout:
                    continue
        except KeyboardInterrupt:
            print("\nDesligando servidor...")
        finally:
            self.shutdown()

    def shutdown(self):
        self.running = False
        for client in list(self.clients.keys()):
            self.remove_client(client)
        self.server.close()
        self.save_chat_history()

if __name__ == "__main__":
    server = ChatServer()
    server.run()