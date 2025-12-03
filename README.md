# DHT22_MQTT
Projeto desenvolvido para as matérias de Microcontroladores e Redes de Computadores I. O projeto foi feito em um arduino uno (sem conexão com a internet), sendo necessário criar um script para realizar as comunicações arduino-->serial-->script-->Broker


O projeto, basicamente, se consiste em:
Um cricuito na placa Arduino UNO, que recebe os valores de temperatura atual de um sensor DHT22. É definido um valor máximo da temperatura, disparando o buzzer quando atingida. Um display LCD exibe tempAtual, tempMAX e Estado (alerta ou normal)

Através do serial, o arduino faz o output dos dados, que são consumidos por um script python (detector). Esse script é responsável por realizar a intermediação entre o Arduino e o Broker.
Com as informações publicadas em um tópico do Broker MQTT, existem outros 2 scripts:
1 responsável por disparar alertas via email (messager.py), quando temperatura fica acima do máximo por longo período. Nesse arquivo, foram removidas os emails e a senha do app..
1 responsável por exibir um "dashboard" com temperatura atual, temperatura máxima e temperatura média das últimas 100 medições. Ele também permite públicar no MQTT um novo valor para TempMAX, realizando a atualização no circuito.

Foi utilizado um broker HiveMQ Cloud Free.
