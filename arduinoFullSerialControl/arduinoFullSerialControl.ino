#include <Servo.h>
void setup() {
	Serial.begin(2000000);
}

volatile uint8_t ISR1TR = 0;
volatile uint8_t ISR2TR = 0;
volatile uint32_t ISR1TRT = 0;
volatile uint32_t ISR2TRT = 0;
volatile uint32_t ISR1TRTM = 0;
volatile uint32_t ISR2TRTM = 0;

Servo myServo[6];


void ISR1(){
  if (micros() - ISR1TRT > ISR1TRTM){
    ISR1TR = 1;
    ISR1TRT = micros();
  }
}
void ISR2(){
    if (micros() - ISR2TRT > ISR2TRTM){
    ISR2TR = 1;
    ISR2TRT = micros();
  }
}


void loop() {
  while (Serial.available()) {
    uint8_t data;
    Serial.readBytes(&data, 1);
    switch (data) {
      case 0x00: { // pinMode
        uint8_t pin;
        uint8_t mode;
        Serial.readBytes(&pin, 1);
        Serial.readBytes(&mode, 1);
        pinMode(pin, mode);
        break;  // Added break to prevent fall-through
      }
      case 0x01: { // digitalWrite
        uint8_t pin;
        uint8_t value;
        Serial.readBytes(&pin, 1);
        Serial.readBytes(&value, 1);
        digitalWrite(pin, value);
        break;  // Added break to prevent fall-through
      }
      case 0x02: { // digitalRead
        uint8_t pin;
        Serial.readBytes(&pin, 1);
        Serial.write((uint8_t)digitalRead(pin));
        break;  // Added break to prevent fall-through
      }
      case 0x03: { // analogWrite
        uint8_t pin;
        uint8_t val;
        Serial.readBytes(&pin, 1);
        Serial.readBytes(&val, 1);
        analogWrite(pin, val);
        break;  // Added break to prevent fall-through
      }
      case 0x04: { // analogRead
        uint8_t pin;
        Serial.readBytes(&pin, 1);
        uint16_t value = analogRead(pin);
        Serial.write(value >> 8);
        Serial.write(value & 0xff);
        break;  // Added break to prevent fall-through
      }
      case 0x05: { // analogWrite with trigger
        uint8_t signalPin;
        uint8_t triggerPin;
        uint8_t signalVal;
        uint32_t triggerTime;
        Serial.readBytes(&triggerPin, 1);
        Serial.readBytes(&signalPin, 1);
        Serial.readBytes(&signalVal, 1);
        Serial.readBytes((uint8_t*)&triggerTime, 4);
        
        analogWrite(signalPin, signalVal);
        delayMicroseconds(triggerTime);
        
        uint16_t value = analogRead(signalPin);
        Serial.write(value >> 8);
        Serial.write(value & 0xff);
        break;  // Added break to prevent fall-through
      }
      case 0x06:{
        uint8_t op;
        Serial.readBytes(&op, 1);
        uint8_t pin;
        Serial.readBytes(&pin, 1);
        uint8_t mode;
        Serial.readBytes(&mode, 1);
        uint32_t timeout;
        Serial.readBytes((uint8_t*)&timeout, 4);
        if (pin == 2){
          if (op == 1){
          pinMode(2, mode&0b11);
          ISR1TRTM = timeout;
          attachInterrupt(digitalPinToInterrupt(2), ISR1, (mode>>2)&0b11);
          } else {
            detachInterrupt(2);
          }
        } else if (pin == 3){
          if (op == 1){
          pinMode(3, mode&0b11);
          attachInterrupt(digitalPinToInterrupt(3), ISR2, (mode>>2)&0b11);
          ISR2TRTM = timeout;
          } else {
            detachInterrupt(3);
          }
        }
        break;
      }
      case 0x07:{//Servo
        uint8_t op;
        uint8_t servo;
        Serial.readBytes(&op, 1);
        Serial.readBytes(&servo, 1);
        switch (op){
          case 0x00:{
            uint8_t pin;
            Serial.readBytes(&pin, 1);
            myServo[servo].attach(pin);
            break;
          }
          case 0x01:{
            myServo[servo].detach();
            break;
          }
          case 0x02:{
            uint8_t pos;
            Serial.readBytes(&pos, 1);
            myServo[servo].write(pos);
            break;
          }
            
        }
        break;
      }
      case 0xff:{
        Serial.write(ISR1TR);
        Serial.write(ISR2TR);
        ISR1TR = 0;
        ISR2TR = 0;
      }
    }
  }
}