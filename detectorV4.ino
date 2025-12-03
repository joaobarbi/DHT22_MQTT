#include <DHT.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <EEPROM.h>

//DHT e Buzzer
#define DHTPIN 2
#define DHTTYPE DHT22
#define BUZZER_PIN 5

//botoes
#define BTN_UP 6
#define BTN_DOWN 7

#define EEPROM_ADDR 0
#define HISTERESIS 0.5

float TempMAX = 30.0;

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal_I2C lcd(0x27, 16, 2);

bool alarmeAtivo = false;
unsigned long lastDebounce = 0;
const unsigned long debounceDelay = 150; //tratar para evitar falsos cliques

void setup() {
  Serial.begin(115200);
  dht.begin();
  pinMode(BUZZER_PIN, OUTPUT);
  noTone(BUZZER_PIN);
  pinMode(BTN_UP, INPUT_PULLUP);
  pinMode(BTN_DOWN, INPUT_PULLUP);

  EEPROM.get(EEPROM_ADDR, TempMAX);
  if (isnan(TempMAX) || TempMAX < 5 || TempMAX > 80) TempMAX = 30.0;

  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("Sistema Ativo");
  delay(1500);
  lcd.clear();
}

void salvarTempMaxNaEEPROM() {
  EEPROM.put(EEPROM_ADDR, TempMAX);
}

void verificaBotoes() {
  if (millis() - lastDebounce < debounceDelay) return;

  if (digitalRead(BTN_UP) == LOW) {
    TempMAX += 0.5;
    if (TempMAX > 80) TempMAX = 80;
    salvarTempMaxNaEEPROM();
    lastDebounce = millis();
  }

  if (digitalRead(BTN_DOWN) == LOW) {
    TempMAX -= 0.5;
    if (TempMAX < 5) TempMAX = 5;
    salvarTempMaxNaEEPROM();
    lastDebounce = millis();
  }
}

void processaSerial() {
  while (Serial.available()) {
    String msg = Serial.readStringUntil('\n');
    msg.trim();

    if (msg == "REQ") {
      Serial.print("NOVO_MAX=");
      Serial.println(TempMAX);
    } 
    else if (msg.startsWith("SET_LIMITE:")) {
      float novoLimite = msg.substring(11).toFloat();
      if (novoLimite >= 5 && novoLimite <= 80) {
        TempMAX = novoLimite;
        salvarTempMaxNaEEPROM();
        Serial.print("LIMITE_ATUALIZADO=");
        Serial.println(TempMAX);
      } else {
        Serial.println("ERRO: LIMITE INVALIDO");
      }
    }
  }
}

void loop() {
  verificaBotoes();

  float temperature = dht.readTemperature();
  if (!isnan(temperature)) {
    // Envia temperatura e limite via Serial
    Serial.print("TEMP=");
    Serial.print(temperature);
    Serial.print(";MAX=");
    Serial.println(TempMAX);

    lcd.setCursor(0,0);
    lcd.print("T:");
    lcd.print(temperature,1);
    lcd.print("C ");
    lcd.print("M:");
    lcd.print(TempMAX,1);

    if (!alarmeAtivo && temperature >= TempMAX) {
      alarmeAtivo = true;
      tone(BUZZER_PIN, 2500);
    }
    if (alarmeAtivo && temperature <= (TempMAX - HISTERESIS)) {
      alarmeAtivo = false;
      noTone(BUZZER_PIN);
    }

    lcd.setCursor(0,1);
    lcd.print(alarmeAtivo ? "ALERTA !!!     " : "Normal         ");
  }

  processaSerial();

  delay(300);
}
