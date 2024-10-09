import os
import shutil
import socket
import threading
import time

# Declaração de variáveis globais
users = []
max_id = 0
files = []
lock = threading.Lock()
# Declaração de constantes
INSTRUCTION_MAX_LENGTH = 6

# -------Funções da aplicação--------------------------------

# Função que define o id usuário ser criado(evitando repetições)
def get_id():
   global max_id
   max_id = max_id+1
   return max_id 

# Função que cria um usuário e retorna seu id
def connect(message):
    global users
    user = next((user for user in users if user["username"] == message["username"]), None)

    if user == None:
        new_user = {
            "username": message["username"],
            "id": str(get_id()),
            "status": "online" 
        }
        users.append(new_user)
        return {"code":"SUCCESS","message":new_user["id"]}
    else:
        for user in users:
            if user['username'] == message['username']:
                user["status"] = 'online'
        return {"code":"SUCCESS","message":user["id"]}

# Função que cria um novo arquivo
def create(message):
    user = next((user for user in users if user["id"] == message["user_id"]), None)
    if user == None or user['status'] != 'online':
        return {"code":"ERROR","message":"O usuário não existe ou está desconectado"}

    if os.path.exists(f'files/{message["filename"]}.txt'):
        return {"code":"ERROR","message":"Já existe um arquivo com esse nome"}
    new_file = {
        "name":message["filename"],
        "last_modifier": message['user_id'],
        "comment":""
    }
    files.append(new_file)
    print(files)
    with open(f'files/{message["filename"]}.txt', 'x'):
        return {"code":"SUCCESS","message":"Arquivo criado"}

# Função que apaga um arquivo
def delete(message):
    user = next((user for user in users if user["id"] == message["user_id"]), None)
    if user == None or user['status'] != 'online':
        return {"code":"ERROR","message":"O usuário não existe ou está desconectado"}

    if not os.path.exists(f'files/{message["filename"]}.txt'):
        return {"code":"ERROR","message":"O arquivo não existe"}

    os.remove(f'files/{message["filename"]}.txt')

    global files
    files = [file for file in files if file["name"] != message["filename"]] # Apaga arquivo do registro
    return {"code":"SUCCESS","message":"O arquivo foi apagado"}

# Função que busca o conteúdo de um arquivo
def get(message):
    user = next((user for user in users if user["id"] == message["user_id"]), None)
    if user == None or user['status'] != 'online':
        return {"code":"ERROR","message":"O usuário não existe ou está desconectado"}

    if not os.path.exists(f'files/{message["filename"]}.txt'):
        return {"code":"ERROR","message":"O arquivo não existe"}

    with open(f'files/{message["filename"]}.txt') as file:
        file_content = file.read()
        return {"code":"SUCCESS","message":file_content}

# Função que atualiza um arquivo
def update(message):
    user = next((user for user in users if user["id"] == message["user_id"]), None)
    if user == None or user['status'] != 'online':
        return {"code":"ERROR","message":"O usuário não existe ou está desconectado"}

    if not os.path.exists(f'files/{message["filename"]}.txt'):
        return {"code":"ERROR","message":"O arquivo não existe"}

    if message["update_mode"] not in ["append","override"]:
        return {"code":"ERROR","message":"Modo de alteração desconhecido"}

    if message["update_mode"] == "append":
        with open(f'files/{message["filename"]}.txt',"a") as file:
            file.write(message["content"])
    elif message["update_mode"] == "override":
        with open(f'files/{message["filename"]}.txt',"w") as file:
            file.write(message["content"])
    global files
    for file in files:
        if file['name'] == message['filename']:
            file["last_modifier"] = message['user_id']
            file["comment"] = message['comment']
    return {"code":"SUCCESS","message":"Arquivo atualizado com sucesso"}


# Função que desconecta um usuário, definindo seu status como offline
def disconnect(message):
    global users
    user = next((user for user in users if user["id"] == message["user_id"]), None)
    if user == None or user['status'] != 'online':
        return {"code":"ERROR","message":"O usuário não existe ou já está desconectado"}
    for user in users:
        if user['id'] == message['user_id']:
            user["status"] = 'offline'
    return {"code":"SUCCESS","message":user["id"]}


# -------Funções da lógica de comunicação cliente-servidor----

# Função que recebe a mensagem do cliente e identifica os campos
def decode_instruction(message):
    splitted_message = message.split('|')
    while len(splitted_message)< INSTRUCTION_MAX_LENGTH:
        splitted_message.append(None)
    types = {
        "CONNECT":{
            "code":"CONNECT",
            "username": splitted_message[1]
        },
        "CREATE":{
            "code":"CREATE",
            "user_id":splitted_message[1],
            "filename":splitted_message[2]
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
                
                if data == 'KEEP-ALIVE':
                    continue

                try:
                    formatted_instruction = decode_instruction(data)
                    print(formatted_instruction)
                except:
                    connection.sendall(b'FORMATO DE MENSAGEM INCORRETO')
                    continue # Pula para a próxima mensagem

                functions = {
                    "CONNECT": connect,
                    "CREATE": create,
                    "DELETE": delete,
                    "GET": get,
                    "UPDATE":update,
                    "DISCONNECT": disconnect
                }

                with lock:
                    function_response = functions.get(formatted_instruction["code"])(formatted_instruction)
                    print(function_response)
                    formatted_response = f"{function_response['code']}|{function_response['message']}"
                    global users
                    print(users)
                    global files
                    print(files)
                    connection.sendall(formatted_response.encode('utf-8'))

        finally:
           connection.close()

def main():
    # Limpa os arquivos gerados na execução anterior do servidor
    shutil.rmtree("files")
    os.mkdir("files")

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

