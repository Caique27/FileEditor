import socket
import threading
import time

# Função que envia mensagens de keep-alive periodicamente
def send_keep_alive(client_socket, interval=5):
    while True:
        try:
            # Envia a mensagem de keep-alive ao servidor
            client_socket.sendall(b'keep-alive')
            time.sleep(interval)  # Aguarda o intervalo antes de enviar novamente
        except (BrokenPipeError, OSError):
            print("Erro ao enviar keep-alive, desconectando...")
            break  # Encerra a thread se a conexão falhar

# Função principal do cliente
def client_program():
    # Cria o socket do cliente
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Conecta-se ao servidor
    server_address = ('127.0.0.1', 8080)  # Altere para o endereço do servidor
    print(f"Conectando-se ao servidor {server_address}")
    client_socket.connect(server_address)
    
    # Inicia a thread de keep-alive
    keep_alive_thread = threading.Thread(target=send_keep_alive, args=(client_socket,))
    keep_alive_thread.daemon = True  # Define como daemon para que ela seja encerrada ao fechar o programa
    keep_alive_thread.start()
    
    try:
        while True:
            # Envia uma mensagem personalizada ao servidor
            message = input("Digite a mensagem para o servidor: ")
            if message.lower() == 'sair':
                break  # Encerra a conexão se o usuário digitar 'sair'
            client_socket.sendall(message.encode())
            print(f"Mensagem '{message}' enviada ao servidor.")
            
            # Recebe a resposta do servidor
            response = client_socket.recv(1024)
            print(f"Resposta do servidor: {response.decode('utf-8')}")
    
    except (BrokenPipeError, OSError) as e:
        print(f"Erro de conexão: {e}")
    
    finally:
        # Encerra a conexão ao sair do loop
        print("Encerrando a conexão com o servidor...")
        client_socket.close()

if __name__ == "__main__":
    client_program()
