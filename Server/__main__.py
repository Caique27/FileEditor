import socket
import threading
import time

INSTRUCTION_MAX_LENGTH = 6
#Função que recebe a mensagem do cliente e identifica os campos
def decode_instruction(message):
    splitted_message = message.split('|')
    while len(splitted_message)< INSTRUCTION_MAX_LENGTH:
        splitted_message.append(None)
    types = {
        "CONNECT":{
            "code":"CONNECT",
            "username": splitted_message[1]
        },
        "DELETE":{
            "code":"DELETE",
            "user_id":splitted_message[1],
            "filename":splitted_message[2]
        },
        "GET":{
            "code":"GET",
            "user_id":splitted_message[1],
            "filename":splitted_message[2]
        },
        "UPDATE":{
            "code":"UPDATE",
            "user_id":splitted_message[1],
            "filename":splitted_message[2],
            "content":splitted_message[3],
            "update_mode":splitted_message[4],
            "comment":splitted_message[5]
        },
        "DISCONNECT":{
            "code":"DISCONNECT",
            "user_id":splitted_message[1]
        }
    }

    formatted_response = types.get(splitted_message[0],None)
    if formatted_response == None or None in formatted_response.values():
        raise
    else:
        return formatted_response

# Função que receber o socket e lida com cada cliente conectado
def client(connection):
        print(f"Conexão estabelecida com {connection.getpeername()}")
        last_keep_alive = time.time()

        try:
            while True:

                # Recebe dados do cliente
                data = connection.recv(1024).decode('utf-8')
                print(f"Dados recebidos: {data}")
                
                if time.time()-last_keep_alive > 15:
                    print("Encerrando conexão por timeout")
                    connection.sendall(b'Encerrando conexao por timeout')
                    break
                

                last_keep_alive = time.time()
                
                if data == 'keep-alive':
                    continue

                try:
                    formatted_instruction = decode_instruction(data)
                    print(formatted_instruction)
                except:
                    connection.sendall(b'FORMATO DE MENSAGEM INCORRETO')
                    continue # Pula para a próxima mensagem

        finally:
           connection.close()

def main():
    # Cria um socket de servidor TCP/IPv4
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Associa o socket a um endereço e porta
    server.bind(('0.0.0.0', 8080))
    
    # Coloca o socket em modo de escuta
    server.listen(5)
    print("Aguardando conexões...")

    while True:
        # Recebe a conexão
        client_socket, addr = server.accept()
        print(f"Cliente connectado {addr}")
        
        # Cria uma nova thread para lidar com o cliente
        client_thread = threading.Thread(target=client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    main()

