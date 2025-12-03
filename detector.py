import serial
import paho.mqtt.client as mqtt
import time
import threading

#script responsável por:
#receber o valor da temperatura atual do arduino e postar no topico dht22/temperatura
#receber possíveis alterações de valor máximo no tópico dht22/limite e repassar para o arduino 

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200 #importante definir o mesmo baud_rate no código do arduino, se não as informações saem iegiveis 

#conexão com o cluster HiveMQ + definição dos topicos
BROKER = "0b4097f4e21f40fda95d96a52d8fbcea.s1.eu.hivemq.cloud"         
PORT = 8883
USERNAME = "detector"       
PASSWORD = "Coxinha123"       

TOPIC_PUBLISH = "dht22/temperatura"
TOPIC_SUBSCRIBE = "dht22/limite"


#inicializa serial, para fazer comunicação com o arduino

try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    print(f"[OK] Conectado ao Arduino em {SERIAL_PORT}")
except Exception as e:
    print("[ERRO] Não foi possível abrir a porta serial:")
    print(e)
    exit()


#conexão MQTT, evidenciando que assinou o topico de limite para receber informações de alterações do tempmax

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Conectado ao HiveMQ Cloud!")
        client.subscribe(TOPIC_SUBSCRIBE)
        print(f"[MQTT] Assinado no tópico: {TOPIC_SUBSCRIBE}")
    else:
        print("[MQTT] Falha ao conectar. Código:", rc)


#quando receber mensagem no topico inscrito enviar para o arduino

def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"[MQTT] Mensagem recebida -> {msg.topic}: {payload}")

#setar o novo limite no arduino

    if msg.topic == TOPIC_SUBSCRIBE:
        comando = f"SET_LIMITE:{payload}\n"
        print(f"[SERIAL] Enviando ao Arduino: {comando.strip()}")
        arduino.write(comando.encode())


#ler arduino e publicar mqtt

def ler_arduino():
    while True:
        try:
            linha = arduino.readline().decode(errors="ignore").strip()

            if linha:
                print(f"[ARDUINO] {linha}")

                if linha.startswith("TEMP="):
                    partes = linha.split(";")
                    temp = partes[0].replace("TEMP=", "")
                    client.publish(TOPIC_PUBLISH, temp) #publicar a temperatura no topico de temperatura atual
                    print(f"[MQTT] Publicado -> {TOPIC_PUBLISH}: {temp}")

        except Exception as e:
            print("[ERRO] Problema ao ler serial:")
            print(e)

        time.sleep(0.1)


#configurção do mqtt

client = mqtt.Client(protocol=mqtt.MQTTv311)
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set() #definição de TLS, já que o HiveMQ obriga o uso de TLS

client.on_connect = on_connect
client.on_message = on_message

print("[MQTT] Conectando ao HiveMQ Cloud...")
client.connect(BROKER, PORT, 60)

#loop em thred
client.loop_start()


#loop da aplicação


print("[INICIADO] Sistema rodando. Pressione CTRL+C para encerrar.\n")

try:
    ler_arduino()

except KeyboardInterrupt:
    print("\nEncerrando...")
    client.loop_stop()
    client.disconnect()
    arduino.close()
    print("Finalizado.")
