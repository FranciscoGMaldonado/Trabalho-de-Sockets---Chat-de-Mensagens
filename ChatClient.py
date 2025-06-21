import socket
import threading

class ChatClient:
    def __init__(self, host='127.0.0.1', port=55555):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def receive(self):
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if not message:
                    break
                print(message)
            except (ConnectionError, OSError):
                print("\nConexão perdida com o servidor.")
                break
        self.running = False

    def send_message(self):
        while self.running:
            message = input()
            try:
                self.client.send(message.encode('utf-8'))
                if message.lower() == '/quit':
                    self.running = False
                    break
            except (ConnectionError, OSError):
                break

    def start(self):
        nickname = input("Escolha seu nickname: ").strip()
        if not nickname:
            print("Nickname não pode ser vazio!")
            return

        try:
            self.client.connect((self.host, self.port))
            self.client.send(nickname.encode('utf-8'))
            response = self.client.recv(1024).decode('utf-8')
            if response.startswith("ERRO"):
                print(response)
                return

            print(response)
            self.running = True

            receive_thread = threading.Thread(target=self.receive, daemon=True)
            send_thread = threading.Thread(target=self.send_message, daemon=True)

            receive_thread.start()
            send_thread.start()

            receive_thread.join()
        except ConnectionRefusedError:
            print("Não foi possível conectar ao servidor.")
        finally:
            self.client.close()
            print("Desconectado do servidor.")

if __name__ == "__main__":
    client = ChatClient()
    client.start()