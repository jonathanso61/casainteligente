import paho.mqtt.client as mqtt
from pymongo import MongoClient
import tkinter as tk
import random

# Conectar ao MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["casa"]
usuarios_collection = db["usuarios"]
mensagens_collection = db["mensagens"]

# Configurações MQTT
mqtt_broker = "localhost"
mqtt_port = 1883
mqtt_topic_control = "casa/controle"

# Função para lidar com a conexão ao servidor MQTT
def on_connect(client, userdata, flags, rc):
    print("Conectado ao MQTT Broker com código de resultado: " + str(rc))
    client.subscribe(mqtt_topic_control)

# Função para lidar com a mensagem recebida
def on_message(client, userdata, message):
    payload = message.payload.decode()
    print("Mensagem recebida: " + payload)
    controlar_dispositivos(payload)

# Função para lidar com o evento do botão "Conectar"
def conectar():
    nome_usuario = entrada_nome.get()
    print(f"Usuário {nome_usuario} conectado ao sistema.")
    usuarios_collection.insert_one({"nome": nome_usuario})

# Função para lidar com os botões de ligar/desligar
def controlar_dispositivos(acao):
    nome_usuario = entrada_nome.get()
    dispositivos_selecionados = [dispositivo for dispositivo, estado in dispositivos.items() if estado.get()]
    
    for dispositivo in dispositivos_selecionados:
        # Publica uma mensagem MQTT para ligar/desligar o dispositivo
        mqtt_client.publish(mqtt_topic_control, f"{acao} {dispositivo} por {nome_usuario}")
    
    print(f"Usuário {nome_usuario} controlou os dispositivos: {', '.join(dispositivos_selecionados)}")

# Inicializar o cliente MQTT e definir os callbacks
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Iniciar a interface gráfica
root = tk.Tk()
root.title("Controle de Casa Inteligente")

# Adicionar entrada de texto para o nome do usuário
label_nome = tk.Label(root, text="Digite seu nome:")
label_nome.pack()
entrada_nome = tk.Entry(root)
entrada_nome.pack()

# Adicionar botão para conectar
botao_conectar = tk.Button(root, text="Conectar", command=conectar)
botao_conectar.pack()

# Lista de dispositivos controláveis
dispositivos = {
    "Televisão da Sala": tk.BooleanVar(),
    "lâmpada Inteligente da sala": tk.BooleanVar(),
    "Alexa": tk.BooleanVar(),
    "Fechadura da porta principal": tk.BooleanVar()
}

# Adicionar botões de ligar/desligar
for dispositivo, estado in dispositivos.items():
    estado_checkbox = tk.Checkbutton(root, text=dispositivo.capitalize(), variable=estado)
    estado_checkbox.pack()

# Adicionar botões de ligar/desligar
botao_ligar = tk.Button(root, text="Ligar Dispositivos", command=lambda: controlar_dispositivos("ligar"))
botao_ligar.pack()
botao_desligar = tk.Button(root, text="Desligar Dispositivos", command=lambda: controlar_dispositivos("desligar"))
botao_desligar.pack()

# Função para adicionar nomes na coleção usuários no banco de dados
def listar_usuarios():
    usuarios = usuarios_collection.find()
    for usuario in usuarios:
        print(usuario["nome"])

# Adicionar botão para listar usuários
botao_listar_usuarios = tk.Button(root, text="Listar Usuários", command=listar_usuarios)
botao_listar_usuarios.pack()

# Função para excluir usuários do banco de dados
def excluir_usuario():
    nome_usuario = entrada_nome.get()
    resultado = usuarios_collection.delete_one({"nome": nome_usuario})
    if resultado.deleted_count > 0:
        print(f"Usuário {nome_usuario} excluído do banco de dados.")
    else:
        print(f"Usuário {nome_usuario} não encontrado no banco de dados.")

# Adicionar botão para excluir usuário
botao_excluir_usuario = tk.Button(root, text="Excluir Usuário", command=excluir_usuario)
botao_excluir_usuario.pack()

# Função para enviar mensagem para alguém da casa
def enviar_mensagem():
    nome_usuario = entrada_nome.get()
    mensagem = entrada_mensagem.get()
    destinatario = entrada_destinatario.get()
    mensagens_collection.insert_one({"remetente": nome_usuario, "destinatario": destinatario, "mensagem": mensagem})
    print(f"Mensagem para {destinatario} enviada por {nome_usuario}: {mensagem}")

# Adicionar campos de entrada para destinatário e mensagem
label_destinatario = tk.Label(root, text="Destinatário:")
label_destinatario.pack()
entrada_destinatario = tk.Entry(root)
entrada_destinatario.pack()

label_mensagem = tk.Label(root, text="Mensagem:")
label_mensagem.pack()
entrada_mensagem = tk.Entry(root)
entrada_mensagem.pack()

# Adicionar botão para enviar mensagem
botao_enviar_mensagem = tk.Button(root, text="Enviar Mensagem", command=enviar_mensagem)
botao_enviar_mensagem.pack()

# Função para listar mensagens no MongoDB
def listar_mensagens():
    mensagens = mensagens_collection.find()
    for mensagem in mensagens:
        print(f"De: {mensagem['remetente']} Para: {mensagem['destinatario']} - {mensagem['mensagem']}")

# Adicionar botão para listar mensagens
botao_listar_mensagens = tk.Button(root, text="Listar Mensagens", command=listar_mensagens)
botao_listar_mensagens.pack()

label_sensor = tk.Label(root, text="")
label_sensor.pack()

# Função para verificar se a câmera esta funcionando
def verificar_sensor_movimento():
    global label_sensor
    fps = random.randint(1, 10)  # Gera aleatoriamente o número de "fps" da câmera
    if fps > 1:
        mensagem_sensor = "Sensor de Movimento da Câmera: Funcionando"
    else:
        mensagem_sensor = "Sensor de Movimento da Câmera: Não Funcionando"
    
    # Atualiza o texto na interface gráfica com o status do sensor
    label_sensor.config(text=mensagem_sensor)
    
    # Agenda a próxima verificação do sensor após 15 segundos
    root.after(15000, verificar_sensor_movimento)

    # Publica uma mensagem MQTT com o status e o valor de FPS
    mqtt_client.publish(mqtt_topic_control, f"Sensor de Movimento: {mensagem_sensor}, FPS: {fps}")
    
    # Imprime a informação
    print(f"Sensor de Movimento: {mensagem_sensor}, FPS: {fps}")

# Iniciar a verificação do sensor de movimento
verificar_sensor_movimento()

# Conectar ao Broker MQTT
mqtt_client.connect(mqtt_broker, mqtt_port, 60)

# Loop MQTT
mqtt_client.loop_start()

# Iniciar a interface gráfica
root.mainloop()


