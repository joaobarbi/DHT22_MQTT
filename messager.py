import time
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import paho.mqtt.client as mqtt

#esse código é responsável por fazer disparos de email para alertas de temperatura, conforme regras de negocio

#conexão com o cluster HiveMQ + definição dos topicos


BROKER = "0b4097f4e21f40fda95d96a52d8fbcea.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "agent"         
PASSWORD = "Coxinha123"     

TOPIC_TEMP = "dht22/temperatura"
TOPIC_LIMIT = "dht22/limite"
TOPIC_LIMIT_REQUEST = "dht22/limite/get" #para, quando iniciado, conseguir obter a ultima temperatura maxima postada no topico. Dessa forma, já iniciar verificando a situação


#
EMAIL_FROM = ""
EMAIL_TO = ""
EMAIL_PASSWORD = ""  # senha de app do gmail, é necessário gerar uma "Senha de app" para permitir que a aplicação use o email para realiar envios

#tempo necessário com temperatura acima do limite para disparar alerta
TEMPO_ALERTA = 5


#variaveis de controle

temp_atual = 0.0
temp_max = 0.0
acima_desde = None
email_enviado = False

#envio de email
def enviar_email(temperatura, limite):
    global email_enviado
    print("[EMAIL] Enviando email de alerta...")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "ALERTA: Temperatura crítica detectada"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    texto = f"""
A temperatura ficou acima do limite por mais de 1 minuto.

Temperatura atual: {temperatura} °C
Limite configurado: {limite} °C
Hora: {time.ctime()}
"""
    msg.attach(MIMEText(texto, "plain"))
    contexto = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=contexto) as server: #usando servidor smtp do google/gmail. Para outros serviços, é necessário alterar os parametros
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    print("[EMAIL] Email enviado com sucesso!")
    email_enviado = True

#conexao mqtt
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Conectado ao HiveMQ!")
        client.subscribe(TOPIC_TEMP)
        client.subscribe(TOPIC_LIMIT) #se inscreve em ambos os topicos, para veriicar se a temp atual esta acima da maxima
  
        print("[MQTT] Solicitando limite atual ao Arduino...")
        client.publish(TOPIC_LIMIT_REQUEST, "REQ") #faz uma publicacao pedindo a ultima temp maxima postada no topico
    else:
        print("[MQTT] Falha ao conectar. RC =", rc)

def on_message(client, userdata, msg):
    global temp_atual, temp_max, acima_desde, email_enviado
    payload = msg.payload.decode()


#verificações para o recebimento da temperatura atual

    if msg.topic == TOPIC_TEMP:
        temp_atual = float(payload)
        if temp_atual > temp_max: #verifica se a temp atual é maior q a max
            if acima_desde is None:
                acima_desde = time.time()
               #se atingir tempo definido, chama func de enviar o email
                print("[ALERTA] Temperatura acima do limite. Temporizando...")
            elif time.time() - acima_desde >= TEMPO_ALERTA and not email_enviado:
                enviar_email(temp_atual, temp_max)
        else:
            acima_desde = None
            email_enviado = False
    elif msg.topic == TOPIC_LIMIT:
        temp_max = float(payload)
        print(f"[MQTT] Limite atualizado recebido: {temp_max}")

#configuração cliente MQTT
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set() #HiveMQ obriga o uso de TLS
client.on_connect = on_connect
client.on_message = on_message

print("[MQTT] Conectando ao HiveMQ Cloud...")
client.connect(BROKER, PORT, 60)
client.loop_forever()
