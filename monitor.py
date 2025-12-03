import paho.mqtt.client as mqtt
import threading
import time

#script responsável por gerar o "monitor"/controller. Exibe temperatura atual, temperatura maxima e média. Permite alterar a temperatura máxima 

#conexão com o cluster HiveMQ + definição dos topicos

BROKER = "0b4097f4e21f40fda95d96a52d8fbcea.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "controller"
PASSWORD = "Coxinha123"

TOPIC_TEMPERATURA = "dht22/temperatura"
TOPIC_LIMITE = "dht22/limite"

#variaveis globais
temperatura_atual = None
temperatura_max = None
historico_temperaturas = []

lock = threading.Lock()

#conexao MQTT

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Conectado ao HiveMQ Cloud!")
        client.subscribe(TOPIC_TEMPERATURA)
        client.subscribe(TOPIC_LIMITE)
        print(f"[MQTT] Assinado nos tópicos: {TOPIC_TEMPERATURA}, {TOPIC_LIMITE}")  #ele precisa receber as 2 infos para gerar a tela de monitoramento
    else:
        print("[MQTT] Falha ao conectar. Código:", rc)

#mensagens recebidas
def on_message(client, userdata, msg):
    global temperatura_atual, temperatura_max, historico_temperaturas
    try:
        payload = float(msg.payload.decode())
    except ValueError:
        return

    with lock:
        if msg.topic == TOPIC_TEMPERATURA:
            temperatura_atual = payload
            historico_temperaturas.append(payload)
            if len(historico_temperaturas) > 100:  # mantem historico limitado
                historico_temperaturas.pop(0)
        elif msg.topic == TOPIC_LIMITE:
            temperatura_max = payload

#frontend, gera no terminal as saidas a cada 10s

def mostrar_status():
    while True:
        time.sleep(10)
        with lock:
            if temperatura_atual is not None and temperatura_max is not None:
                media = sum(historico_temperaturas) / len(historico_temperaturas)
                print("\n===== STATUS =====")
                print(f"Temperatura atual : {temperatura_atual:.1f} °C")
                print(f"Temperatura máxima: {temperatura_max:.1f} °C")
                print(f"Média das últimas leituras: {media:.1f} °C")
                print("==================\n")

#solicitação de nova temperatura, já validado se esta na faixa aceita pelo dht22. as temperaturas podem ser valores quebrados como 29.5

def alterar_limite():
    global temperatura_max
    while True:
        novo_limite = input("Digite nova temperatura máxima (ou ENTER para manter): ")
        if novo_limite.strip() == "":
            continue
        try:
            valor = float(novo_limite)
            if 5 <= valor <= 80:
                client.publish(TOPIC_LIMITE, valor) #publica no topico o novo limite, para ser interpretado pelo codigo detector e messager
                print(f"[MQTT] Novo limite enviado: {valor} °C")
                print(f"[MQTT] Novo limite enviado: {valor} °C")
            else:
                print("Valor inválido. Digite entre 5 e 80.")
        except ValueError:
            print("Valor inválido. Digite um número válido.")

#configuracao mqtt
client = mqtt.Client(protocol=mqtt.MQTTv311)
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set() #HiveMQ obrigado o uso do TLS
client.on_connect = on_connect
client.on_message = on_message

print("[MQTT] Conectando ao HiveMQ Cloud...")
client.connect(BROKER, PORT, 60)
client.loop_start()

#inicia as threads
thread_status = threading.Thread(target=mostrar_status, daemon=True)
thread_input = threading.Thread(target=alterar_limite, daemon=True)

thread_status.start()
thread_input.start()

#loop para manter script rodando
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nEncerrando...")
    client.loop_stop()
    client.disconnect()
    print("Finalizado.")
