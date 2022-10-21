
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
const char topicT[]  = "CsHfaWQDT";
const char topicH[]  = "CsHfaWQDH";

#include <Adafruit_AHTX0.h>
Adafruit_AHTX0 aht;

#define LED_PIN    2
#define LED_ENABLE_PIN 4
#define LED_COUNT  1
#define BRIGHTNESS 50
#include <Adafruit_NeoPixel.h>
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

void colorWipe(uint32_t color, int wait) {
  for (int i = 0; i < strip.numPixels(); i++) { // For each pixel in strip...
    strip.setPixelColor(i, color);         //  Set pixel's color (in RAM)
    strip.show();                          //  Update strip to match
    delay(wait);                           //  Pause for a moment
  }
}

void wheel(int pos, int *r, int *g, int *b) {
  // Input a value 0 to 255 to get a color value.
  // The colours are a transition r - g - b - back to r.
  if ((pos < 0) or (pos > 255)) {
    *r = 0;
    *g = 0;
    *b = 0;
    return;
  }
  if (pos < 85) {
    *r = 255 - pos * 3;
    *g = pos * 3;
    *b = 0;
  }
  if (pos < 170) {
    pos -= 85;
    *r = 0;
    *g = 255 - pos * 3;
    *b = pos * 3;
    return;
  }
  pos -= 170;
  *r = pos * 3;
  *g = 0;
  *b = 255 - pos * 3;
}

void setup() {
  // INITIALIZE the NeoPixel
  pinMode(LED_ENABLE_PIN, OUTPUT);
  digitalWrite(LED_ENABLE_PIN, 0);
  strip.begin();           
  strip.show();
  strip.setBrightness(50);
  colorWipe(strip.Color( 255, 0, 0), 0);

  Serial.begin(115200);

  // attempt to connect to Wifi network:
  Serial.print("Attempting to connect to WPA SSID: ");
  Serial.println(ssid);
  colorWipe(strip.Color( 0, 0, 255), 0);
  WiFi.begin(ssid, pass);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("Connected to the network!");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println();

  if (! aht.begin()) {
    Serial.println("Could not find AHT? Check wiring");
    while (1) delay(10);
  }
  Serial.println("AHT10 or AHT20 found");

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

  colorWipe(strip.Color( 0, 255, 0), 0);
}

void loop() {
  int r, g, b;

  sensors_event_t humidity, temp;
  aht.getEvent(&humidity, &temp);// populate temp and humidity objects with fresh data
  Serial.print("Temperature: "); Serial.print(temp.temperature); Serial.println(" degrees C");
  Serial.print("Humidity: "); Serial.print(humidity.relative_humidity); Serial.println("% rH");

  // Text log of Temperature and Humidity
  mqttClient.beginMessage(topic);
  mqttClient.print("Temperature: "); mqttClient.print(temp.temperature); mqttClient.print(" degrees C, ");
  mqttClient.print("Humidity: "); mqttClient.print(humidity.relative_humidity); mqttClient.print("% rH");
  mqttClient.endMessage();
  Serial.print("Sent MQTT message for ");
  Serial.println(topic);
  delay(250);

  // Temperature
  mqttClient.beginMessage(topicT);
  mqttClient.print(temp.temperature);
  mqttClient.endMessage();
  Serial.print("Sent MQTT message for ");
  Serial.println(topicT);
  delay(250);

  // Humidity
  mqttClient.beginMessage(topicH);
  mqttClient.print(humidity.relative_humidity);
  mqttClient.endMessage();
  Serial.print("Sent MQTT message for ");
  Serial.println(topicH);

  for (int i = 0; i < 256; i++) {
    wheel(i, &r, &g, &b);
    colorWipe(strip.Color( r, g, b), 235); // 255 * 235 is roughly 1 minute
  }
}
