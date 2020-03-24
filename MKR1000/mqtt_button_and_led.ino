/*
  Arduino MQTT DEMO
*/

#include <ArduinoMqttClient.h>
//#include <WiFiNINA.h> // for MKR1000 change to: #include <WiFi101.h>
#include <WiFi101.h>


#include "arduino_secrets.h"
///////please enter your sensitive data in the Secret tab/arduino_secrets.h
char ssid[] = SECRET_SSID;        // your network SSID (name)
char pass[] = SECRET_PASS;    // your network password (use for WPA, or use as key for WEP)

// To connect with SSL/TLS:
// 1) Change WiFiClient to WiFiSSLClient.
// 2) Change port value from 1883 to 8883.
// 3) Change broker value to a server with a known SSL/TLS root certificate
//    flashed in the WiFi module.

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

const char broker[] = "192.168.1.123"; // Address of the MQTT server
int        port     = 1883;
const char topic[]  = "arduino/simple";
const char subtopic[]  = "arduino/cmd";

const long interval = 1000;
unsigned long previousMillis = 0;

int count = 0;
const int buttonPin = 1;
int buttonPrevState = 0;
int buttonState = 0;         // variables for reading the pushbutton status
String subMessage = "";

void setup() {
  //Initialize serial
  Serial.begin(9600);

  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // attempt to connect to Wifi network:
  Serial.print("Attempting to connect to WPA SSID: ");
  Serial.println(ssid);
  while (WiFi.begin(ssid, pass) != WL_CONNECTED) {
    // failed, retry
    Serial.print(".");
    delay(5000);
  }

  Serial.println("You're connected to the network");
  Serial.println();

  // You can provide a unique client ID, if not set the library uses Arduino-millis()
  // Each client must have a unique client ID
  // mqttClient.setId("clientId");

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
  // subscribe to a topic
  mqttClient.subscribe(subtopic);
  digitalWrite(LED_BUILTIN, LOW);
}

void loop() {
  // call poll() regularly to allow the library to send MQTT keep alives which
  // avoids being disconnected by the broker
  //mqttClient.poll();

  int messageSize = mqttClient.parseMessage();
  if (messageSize) {
    subMessage = "";
    // we received a message, print out the topic and contents
    Serial.print("Received a message with topic '");
    Serial.print(mqttClient.messageTopic());
    Serial.print("', length ");
    Serial.print(messageSize);
    Serial.println(" bytes:");

    // use the Stream interface to print the contents
    while (mqttClient.available()) {
      subMessage = subMessage + (char)mqttClient.read();
    }
    Serial.println(subMessage);

    if(subMessage == "ON") {
      digitalWrite(LED_BUILTIN, HIGH);
    } else {
      digitalWrite(LED_BUILTIN, LOW);
    }
  }

  // read the state of the pushbutton value:
  buttonState = digitalRead(buttonPin);
  // check if the pushbutton is pressed. If it is, the buttonState is HIGH:
  if (buttonState == HIGH)
    buttonPrevState = HIGH;

  if ( (buttonState == LOW) && (buttonPrevState == HIGH) ) {
    count++;
    // send message, the Print interface can be used to set the message contents
    mqttClient.beginMessage(topic);
    mqttClient.print("BUTTON ");
    mqttClient.print(count);
    mqttClient.endMessage();
    buttonPrevState = LOW;
    Serial.println("Sent MQTT message.");

  }
}
