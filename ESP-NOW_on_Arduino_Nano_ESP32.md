# ESP-NOW on Arduino Nano ESP32

## Introduction
Supporting code and comments for my video on using ESP-NOW on the Arduino Nano ESP32.

ESP-NOW needs to ESP32 boards. I use the Arduino Nano ESP32 and the Carbon V3.

- [Arduino Nano ESP32 Review - Official ESP32-S3 Board from Arduino](https://youtu.be/zZ569ieGJts)
- [ESP32 and ESP32-S2 Microcontroller Boards Made in Europe, Not in China](https://youtu.be/QPiCqPqnnFU)

You can get the Carbon V3 here: [https://ardushop.ro/ro/home/2061-placa-de-dezvoltare-carbon-v3.html](https://ardushop.ro/ro/home/2061-placa-de-dezvoltare-carbon-v3.html)

## Minimum Code
An example of how to send a number from the Arduino Nano ESP32 is sent to the secondary ESP32 unit over ESP-NOW.

### Minimum Primary
```
#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h> // only for esp_wifi_set_channel()

// Global copy of Secondary
esp_now_peer_info_t secondary;
#define CHANNEL 1

// Scan for Secondarys in AP mode
void ScanForSecondary() {
  int16_t scanResults = WiFi.scanNetworks(false, false, false, 300, CHANNEL); // Scan only on one channel
  memset(&secondary, 0, sizeof(secondary));

  if (scanResults != 0) {
    for (int i = 0; i < scanResults; ++i) {
      String SSID = WiFi.SSID(i);
      int32_t RSSI = WiFi.RSSI(i);
      String BSSIDstr = WiFi.BSSIDstr(i);

      delay(10);
      if (SSID.indexOf("ESPNOW") == 0) {
        int mac[6];
        if ( 6 == sscanf(BSSIDstr.c_str(), "%x:%x:%x:%x:%x:%x",  &mac[0], &mac[1], &mac[2], &mac[3], &mac[4], &mac[5] ) ) {
          for (int ii = 0; ii < 6; ++ii ) {
            secondary.peer_addr[ii] = (uint8_t) mac[ii];
          }
        }
        secondary.channel = CHANNEL;
        secondary.encrypt = 0;
        break;
      }
    }
  }

  WiFi.scanDelete();
}

// Check if the secondary is already paired with the primary.
// If not, pair the secondary with primary
bool manageSecondary() {
  if (secondary.channel == CHANNEL) {
    bool exists = esp_now_is_peer_exist(secondary.peer_addr);
    if (!exists) {
      // Secondary not paired, attempt pair
      if (esp_now_add_peer(&secondary) == ESP_OK) {
        char macStr[18];
        snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x", MAC2STR(secondary.peer_addr));
        Serial.print("Peer added: "); Serial.println(macStr);
        return true;
      } else {
        return false;
      }
    }
    return true;
  }
  return false;
}

uint8_t data = 0;
void sendData() {
  data++;
  const uint8_t *peer_addr = secondary.peer_addr;
  Serial.print("Sending: "); Serial.print(data);
  char macStr[18];
  snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x", MAC2STR(secondary.peer_addr));
  Serial.print(" to: "); Serial.println(macStr);
  esp_now_send(peer_addr, &data, sizeof(data));
}

// callback when data is sent from Primary to Secondary
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  // Do nothing
}


void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_STA);
  esp_wifi_set_channel(CHANNEL, WIFI_SECOND_CHAN_NONE);

  WiFi.disconnect();
  esp_now_init();
  esp_now_register_send_cb(OnDataSent);
}

void loop() {
  ScanForSecondary();
  if (manageSecondary()) {
     sendData();
  }
  delay(3000);
}
```
### Minimum Secondary
```
#include <esp_now.h>
#include <WiFi.h>

#define CHANNEL 1

void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_AP);
  String SSID = "ESPNOW-" + WiFi.macAddress();
  String Password = "123456789";
  WiFi.softAP(SSID.c_str(), Password.c_str(), CHANNEL, 0);

  WiFi.disconnect();
  esp_now_init();
  esp_now_register_recv_cb(OnDataRecv);
}

// callback when data is recv from Master
void OnDataRecv(const uint8_t *mac_addr, const uint8_t *data, int data_len) {
  char macStr[18];
  snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x",
           mac_addr[0], mac_addr[1], mac_addr[2], mac_addr[3], mac_addr[4], mac_addr[5]);
  Serial.print("R: "); Serial.print(*data); Serial.print(" from: "); Serial.println(macStr);
}

void loop() {
  // Chill
  delay(1000);
}
```
## NEO Pixel Code
The value of a potentiometer on the Arduino Nano ESP32 is sent to the secondary ESP32 unit over ESP-NOW. On the receiver, the NEOPIXEL is set according to the value received.

### NEO Pixel Primary
```
#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h> // only for esp_wifi_set_channel()

// Global copy of Secondary
esp_now_peer_info_t secondary;
#define CHANNEL 1
int oldvalue;
int sensorValue;

// Scan for Secondarys in AP mode
void ScanForSecondary() {
  int16_t scanResults = WiFi.scanNetworks(false, false, false, 300, CHANNEL); // Scan only on one channel
  memset(&secondary, 0, sizeof(secondary));

  if (scanResults != 0) {
    for (int i = 0; i < scanResults; ++i) {
      String SSID = WiFi.SSID(i);
      int32_t RSSI = WiFi.RSSI(i);
      String BSSIDstr = WiFi.BSSIDstr(i);

      delay(10);
      if (SSID.indexOf("ESPNOW") == 0) {
        int mac[6];
        if ( 6 == sscanf(BSSIDstr.c_str(), "%x:%x:%x:%x:%x:%x",  &mac[0], &mac[1], &mac[2], &mac[3], &mac[4], &mac[5] ) ) {
          for (int ii = 0; ii < 6; ++ii ) {
            secondary.peer_addr[ii] = (uint8_t) mac[ii];
          }
        }
        secondary.channel = CHANNEL;
        secondary.encrypt = 0;
        break;
      }
    }
  }

  WiFi.scanDelete();
}

// Check if the secondary is already paired with the primary.
// If not, pair the secondary with primary
bool manageSecondary() {
  if (secondary.channel == CHANNEL) {
    bool exists = esp_now_is_peer_exist(secondary.peer_addr);
    if (!exists) {
      // Secondary not paired, attempt pair
      if (esp_now_add_peer(&secondary) == ESP_OK) {
        char macStr[18];
        snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x", MAC2STR(secondary.peer_addr));
        Serial.print("Peer added: "); Serial.println(macStr);
        return true;
      } else {
        return false;
      }
    }
    return true;
  }
  return false;
}

void sendData() {
  const uint8_t *peer_addr = secondary.peer_addr;
  Serial.print("Sending: "); Serial.print(sensorValue);
  char macStr[18];
  snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x", MAC2STR(secondary.peer_addr));
  Serial.print(" to: "); Serial.println(macStr);
  esp_now_send(peer_addr, (uint8_t*) &sensorValue, sizeof(sensorValue));
}

// callback when data is sent from Primary to Secondary
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  // Do nothing
}

void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_STA);
  esp_wifi_set_channel(CHANNEL, WIFI_SECOND_CHAN_NONE);

  WiFi.disconnect();
  esp_now_init();
  esp_now_register_send_cb(OnDataSent);

  oldvalue = 0;
}

void loop() {
  ScanForSecondary();
  // read the input on analog pin 0 (which goes from 0 - 4095)
  sensorValue = analogRead(A0);
  if (abs(sensorValue - oldvalue) > 75) {
    oldvalue = sensorValue;
    if (manageSecondary()) {
      sendData();
    }
  }
  delay(300);
}
```
### NEO Pixel Secondary
```
#include <esp_now.h>
#include <WiFi.h>

#define CHANNEL 1

// NEOPIXEL on Carbon V2
#define LED_PIN    2
#define LED_ENABLE_PIN 4
#define LED_COUNT  1
#define BRIGHTNESS 50

#include <Adafruit_NeoPixel.h>
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

void colorWipe(uint32_t color, int wait) {
  for(int i=0; i<strip.numPixels(); i++) { // For each pixel in strip...
    strip.setPixelColor(i, color);         //  Set pixel's color (in RAM)
    strip.show();                          //  Update strip to match
    delay(wait);                           //  Pause for a moment
  }
}

// From AdaFruit NeoPixel library
uint32_t Wheel(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) {
    return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  }
  if(WheelPos < 170) {
    WheelPos -= 85;
    return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
  WheelPos -= 170;
  return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
}
// END

void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_AP);
  String SSID = "ESPNOW-" + WiFi.macAddress();
  String Password = "123456789";
  WiFi.softAP(SSID.c_str(), Password.c_str(), CHANNEL, 0);

  WiFi.disconnect();
  esp_now_init();
  esp_now_register_recv_cb(OnDataRecv);

  // NEOPIXEL Init
  strip.begin();           // INITIALIZE NeoPixel strip object (REQUIRED)
  strip.show();            // Turn OFF all pixels ASAP
  strip.setBrightness(50); // Set BRIGHTNESS to about 1/5 (max = 255)
  colorWipe(strip.Color(0, 0, 0), 500);  
}

// callback when data is recv from Master
void OnDataRecv(const uint8_t *mac_addr, const uint8_t *data, int data_len) {
  int sensorValue;
  memcpy(&sensorValue, (void *) data, data_len);
  char macStr[18];
  snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x",
           mac_addr[0], mac_addr[1], mac_addr[2], mac_addr[3], mac_addr[4], mac_addr[5]);
  Serial.print("R: "); Serial.print(sensorValue); Serial.print(" from: "); Serial.println(macStr);
  colorWipe(Wheel(sensorValue/16), 250);
}

void loop() {
  // Chill
  delay(1000);
}
```
