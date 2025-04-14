#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define SS_PIN 53
#define RST_PIN 49
#define TRIG_PIN 7
#define ECHO_PIN 6
#define BUZZER_PIN 12
#define RED_PIN 9
#define GREEN_PIN 10
#define BLUE_PIN 11

MFRC522 rfid(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(0x27, 16, 2);

const byte validTag[] = {xxxx, xxxx, xxxx, xxxx};  // Valid RFID tag ID (write the tag ID of the card you want to be approved)

void setup() {
  Serial.begin(9600);
  SPI.begin();
  rfid.PCD_Init();
  lcd.init();
  lcd.backlight();
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  showInitialMessage();
}

void loop() {
  // Step 1: RFID Verification
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    bool isValid = true;
    for (byte i = 0; i < rfid.uid.size; i++) {
      if (rfid.uid.uidByte[i] != validTag[i]) {
        isValid = false;
        break;
      }
    }
    if (isValid) {
      lcd.clear();
      lcd.print("ID approved!");
      analogWrite(BLUE_PIN, 0);
      analogWrite(GREEN_PIN, 255);  // Turn on green LED
      delay(1000);
      analogWrite(GREEN_PIN, 0);    // Turn off green LED
      step2();
    } else {
      lcd.clear();
      lcd.print("wrong ID");
      analogWrite(RED_PIN, 255);  // Turn on red LED
      delay(1000);
      analogWrite(RED_PIN, 0);    // Turn off red LED
      showInitialMessage();
    }
  }
}

void showInitialMessage() {
  lcd.clear();
  lcd.print("Hold the tag");
  lcd.setCursor(0, 1);
  lcd.print("near the reader");
  analogWrite(BLUE_PIN, 10);  // Turn on blue LED
}

void step2() {
  analogWrite(RED_PIN, 100);
  analogWrite(GREEN_PIN, 0);
  analogWrite(BLUE_PIN, 0);  // Turn on blue LED
  lcd.clear();
  lcd.print("Get close to");
  lcd.setCursor(0, 1);
  lcd.print("the sensor");
  digitalWrite(BUZZER_PIN, HIGH);  // Turn on buzzer

  unsigned long startTime = millis();
  while (true) {
    digitalWrite(TRIG_PIN, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_PIN, LOW);
    long duration = pulseIn(ECHO_PIN, HIGH);
    float distance = duration * 0.034 / 2;
    Serial.print("Distance: ");
    Serial.print(distance);
    Serial.println(" cm");

    if (distance < 30) {
      if (millis() - startTime >= 3000) {
        digitalWrite(BUZZER_PIN, LOW);  // Turn off buzzer
        analogWrite(RED_PIN, 0);
        analogWrite(GREEN_PIN, 100);  // Turn on green LED
        lcd.clear();
        lcd.print("Distance approved!");
        delay(4000);
        step3();
        break;
      }
    } else {
      startTime = millis();  // Reset timer if distance is not maintained
    }
    delay(1000);
  }
}

void step3() {
  lcd.clear();
  lcd.print("!!! NOTICE !!!");
  analogWrite(GREEN_PIN, 200);  // Turn off green LED
  delay(3000);
  analogWrite(GREEN_PIN, 0);  // Turn off green LED
  analogWrite(BLUE_PIN, 200);  // Turn off green LED
  delay(3000);
  analogWrite(BLUE_PIN, 0);  // Turn off green LED    
  analogWrite(RED_PIN, 200);  // Turn off green LED
  delay(3000); 
  analogWrite(RED_PIN, 0);  // Turn off green LED
  analogWrite(BLUE_PIN, 200);  // Turn off green LED
  analogWrite(BLUE_PIN, 100);  // Turn off green LED

    lcd.clear();
  lcd.print("Please take off ");
  lcd.setCursor(0, 1);
  lcd.print("your glasses");
  delay(7000);  // Wait for 7 seconds

  lcd.clear();
  lcd.print("The process will");
  lcd.setCursor(0, 1);
  lcd.print("take few minutes");
  delay(5000);  // Wait for 5 seconds
  lcd.clear();
  lcd.print("Please be");
  lcd.setCursor(0, 1);
  lcd.print("patient...");
  delay(7000);  // Wait for 7 seconds

  
  analogWrite(GREEN_PIN, 0);  // Turn off green LED
  analogWrite(BLUE_PIN, 0);  // Turn off green LED  
  analogWrite(RED_PIN, 0);  // Turn off green LED 
  delay(1000);  // Wait for 10 seconds
  analogWrite(GREEN_PIN, 255);  // Turn on green LED
  
  lcd.clear();
  lcd.print("Remain still and");
  lcd.setCursor(0, 1);
  lcd.print("stare at camera");
  delay(10000);  // Wait for 10 seconds


  lcd.clear();
  lcd.print("rPPG started...");
  Serial.println("END_MEASUREMENT");  // Send end signal to Raspberry Pi
  analogWrite(GREEN_PIN, 200);  // Turn off green LED
  analogWrite(BLUE_PIN, 200);  // Turn off green LED  
  analogWrite(RED_PIN, 200);  // Turn off green LED 

  delay(80000);  // Run rPPG for 80secs

  analogWrite(GREEN_PIN, 0);  // Turn off green LED
  analogWrite(BLUE_PIN, 0);  // Turn off green LED  
  analogWrite(RED_PIN, 0);  // Turn off green LED 

  lcd.clear();
  lcd.print("rPPG is over! :)");
  analogWrite(GREEN_PIN, 100);  // Turn off green LED
  delay(3000);
  analogWrite(GREEN_PIN, 0);  // Turn off green LED
  analogWrite(BLUE_PIN, 100);  // Turn off green LED
  delay(3000);
  analogWrite(BLUE_PIN, 0);  // Turn off green LED    
  analogWrite(RED_PIN, 100);  // Turn off green LED
  delay(3000); 
  analogWrite(RED_PIN, 0);  // Turn off green LED
  analogWrite(BLUE_PIN, 100);  // Turn off green LED

  lcd.clear();
  lcd.print("Have a nice day!");
  lcd.setCursor(0, 1);
  lcd.print("-Ata J.S.");
  analogWrite(GREEN_PIN, 255);  // Turn on blue LED
}
