# Introduction
This summary document accompanies my video review of the Arduino Nano ESP32.

You might find the following videos, documents and code useful:

- [Dual Core Programming for the Raspberry Pi Pico, ESP32, and ESP32-S3 Using the Arduino IDE](https://www.youtube.com/watch?v=w5YigjvSaF4)
- [Examples files for my video "Dual Core Programming for the Raspberry Pi Pico, ESP32, and ESP32-S3 Using the Arduino IDE"](https://github.com/garyexplains/examples/tree/master/Dual_Core_for_RP2040_ESP32_ESP32-S3)
- [Dual Core Microcontroller Battle Royale - Performance and Power Efficiency](https://www.youtube.com/watch?v=CD9c6UK_uis)
- [Arduino Nano ESP32 Cheat Sheet](https://docs.arduino.cc/tutorials/nano-esp32/cheat-sheet)

# Arduino Nano ESP32
The Nano ESP32 brings the ESP32-S3 to the world of Arduino and MicroPython programming. It uses the
well-known Arduino Nano form factor and includes Wi-Fi and Bluetooth. It supports Arduino and MicroPython programming and works (from August 2023 onwards) with Arduino IoT Cloud.

## ESP32-S3
The processor used by the board is the u-blox® NORA-W106 (ESP32-S3).

- CPU: Xtensa LX7, 240 MHz dual-core
- RAM: 512 kB
- Flash: 8192 kB

### Wi-Fi
The NORA-W106-10B module supports the Wi-Fi® 4 IEEE 802.11 standards b/g/n, with an output power EIRP at up
to 10 dBm. The max range for this module is 500 meters.
- 802.11b: 11 Mbit/s
- 802.11g: 54 Mbit/s
- 802.11n: 72 Mbit/s max at HT-20 (20 MHz), 150 Mbit/s max at HT-40 (40 MHz)

### Bluetooth
The NORA-W106-10B module supports Bluetooth® LE v5.0 with an output power EIRP at up to 10 dBm and data
rates up to 2 Mbps. It has the option to scan and advertise simultaneously, as well as supporting multiple
connections in peripheral/central mode.

### Pinout
![Arduino Nano ESP32 pinout](https://github.com/garyexplains/examples/blob/master/arduino%20nano%20esp32%20pinout.jpg)

## Arduino IDE
Use Arduino IDE 2.x. Go to the Board Manager, and type "esp32" into the search box. Install "esp32 by Arduino". This is different from "esp32 by Espressif". The Arduino-supplied package includes support for the Arduino Nano ESP32.

Make sure you select the Arduino Nano ESP32 with the DFU port, not the COM port. Under Tools->Port pick from the "dfu ports" list, not from "Serial ports".

## Read from a potentiometer and publish over MQTT
The middle pin of the potentiometer is connected to pin A0 on the Nano ESP32.

```
#include <ArduinoMqttClient.h>
#include <WiFi.h>

#include "arduino_secrets.h"
///////please enter your sensitive data in the Secret tab/arduino_secrets.h
char ssid[] = SECRET_SSID;        // your network SSID (name)
char pass[] = SECRET_PASS;    // your network password (use for WPA, or use as key for WEP)

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

const char broker[] = "test.mosquitto.org"; // Address of the MQTT server
int        port     = 1883;
const char topic[]  = "CsHfaWQD";
const char topicA[]  = "CsHfaWQDA";
const char topicC[]  = "CsHfaWQDC";
int counter = 0;
int oldvalue = 0;

void setup() {
  Serial.begin(115200);
  delay(5000);
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_BLUE, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_BLUE, HIGH);
  digitalWrite(LED_GREEN, HIGH);

  // attempt to connect to Wifi network:
  Serial.print("Attempting to connect to WPA SSID: ");
  Serial.println(ssid);
  WiFi.begin(ssid, pass);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("Connected to the network!");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println();

  digitalWrite(LED_RED, HIGH);
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_BLUE, HIGH);

  // You can provide a username and password for authentication
  // mqttClient.setUsernamePassword("user", "password");
  Serial.print("Attempting to connect to the MQTT broker: ");
  Serial.println(broker);

  while (!mqttClient.connect(broker, port)) {
    Serial.print("MQTT connection failed! Error code = ");
    Serial.println(mqttClient.connectError());
  }

  Serial.println("You're connected to the MQTT broker!");
  Serial.println();

  digitalWrite(LED_RED, HIGH);
  digitalWrite(LED_GREEN, HIGH);
  digitalWrite(LED_BLUE, HIGH);
  digitalWrite(LED_BUILTIN, HIGH);
}


// the loop routine runs over and over again forever:
void loop() {
  // read the input on analog pin 0 (which goes from 0 - 4095)
  int sensorValue = analogRead(A0);
  if (abs(sensorValue - oldvalue) > 75) {
    oldvalue = sensorValue;
    Serial.print("Analog: "); Serial.println(sensorValue);
    Serial.print("Counter: "); Serial.println(counter);

    // Text log
    mqttClient.beginMessage(topic);
    mqttClient.print("Analog: "); mqttClient.println(sensorValue);
    mqttClient.print("Counter: "); mqttClient.println(counter);
    mqttClient.endMessage();
    Serial.print("Sent MQTT message for ");
    Serial.println(topic);

    // Potentiometer
    mqttClient.beginMessage(topicA);
    mqttClient.print(sensorValue);
    mqttClient.endMessage();
    Serial.print("Sent MQTT message for ");
    Serial.println(topicA);

    // Counter
    mqttClient.beginMessage(topicC);
    mqttClient.print(counter);
    mqttClient.endMessage();
    Serial.print("Sent MQTT message for ");
    Serial.println(topicC);

    counter++;
    delay(100);
  }
}
```

You will also need a `arduino_secrets.h` file like this:
```
#define SECRET_SSID "MYWIFINET"
#define SECRET_PASS "secretpassword"
```
