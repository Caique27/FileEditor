import socket
import threading

# Função que lida com cada cliente conectado
def client(socket):
        print(f"Conexão estabelecida com {socket.getpeername()}")
        
        try:
            while True:
                # Recebe dados do cliente
                data = socket.recv(1024).decode('utf-8')
                print(f"Dados recebidos: {data}")
                
                # Envia de volta os dados recebidos (echo)
                if data != 'keep-alive':
                    socket.sendall(b'OK')
        finally:
           socket.close()
       

def main():
    # Cria um socket de servidor TCP/IPv4
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Associa o socket a um endereço e porta
    server.bind(('0.0.0.0', 8080))
    
    # Coloca o socket em modo de escuta
    server.listen(5)
    print("Servidor Iniciado")

    while True:
        # Aceita uma nova conexão
        client_socket, addr = server.accept()
        print(f"Client Address {addr}")
        
        # Cria uma nova thread para lidar com o cliente
        client_thread = threading.Thread(target=client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    main()

