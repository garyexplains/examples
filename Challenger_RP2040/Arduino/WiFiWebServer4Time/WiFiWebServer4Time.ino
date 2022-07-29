/*
  WiFi Web Server for Challenger 2040 Wi-Fi/BLE Board

  A simple web server that shows the current time.

  Requires:
    Board support for Pico from: Raspberry Pi Pico Arduino core, for all RP2040 boards from https://github.com/earlephilhower/arduino-pico
    Adafruit_NeoPixel from https://github.com/adafruit/Adafruit_NeoPixel
    WiFiEspAT library from https://github.com/JAndrassy/WiFiEspAT
    Time by Paul Stoffregen from https://github.com/PaulStoffregen/Time
    EspATMQTT from https://github.com/PontusO/EspATMQTT

    Note:
    Since the Challenger 2040 Wi-Fi/BLE Board has an AT firmware version higher than 2.1.0 then you need to
    open the folder for the library (normally Documents/Arduino/libraries/WiFiEspAT)and open the
    file src/utility/EspAtDrvTypes.h in a text editor and comment out the
    line #define WIFIESPAT1 like this //#define WIFIESPAT1

    Note:
    To turn off the debug statemens coming from EspATMQTT you need to open the folder of the library and set DEBUG to 0 in EACH
    of the .cpp files.

 */
#include <WiFiEspAT.h>
#include <ChallengerWiFi.h>
#include <Adafruit_NeoPixel.h>
#include <TimeLib.h>
#include <EspATMQTT.h>

#ifndef STASSID
#define STASSID "YOUR-SSID"
#define STAPSK "password1234"
#endif

const char* ssid = STASSID;
const char* password = STAPSK;
WiFiServer server(80);
EspATMQTT mqtt;

#define PIN        D14
#define NUMPIXELS 1
Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

const int timeZone = 3;      // Eastern European Summer Time
//const int timeZone = 1;     // Central European Time
//const int timeZone = -5;  // Eastern Standard Time (USA)
//const int timeZone = -4;  // Eastern Daylight Time (USA)
//const int timeZone = -8;  // Pacific Standard Time (USA)
//const int timeZone = -7;  // Pacific Daylight Time (USA)
//etc
//NB: Won't work for timezones with half hour increments like India

void setNEO(int red, int green, int blue) {
  pixels.clear();
  pixels.setPixelColor(0, pixels.Color(red, green, blue));
  pixels.show();  
}

void setup() {

  setNEO(128,128,128);
  Serial.begin(115200);
  while (!Serial);

  //Serial1.begin(AT_BAUD_RATE);
  if (Challenger2040WiFi.reset())
    Serial.println(F("WiFi Chip reset OK !"));
  else {
    Serial.println(F("Could not reset WiFi chip !"));
    setNEO(255,0,0);
    while(true);
  }
  
  WiFi.init(Serial2);

  if (WiFi.status() == WL_NO_MODULE) {
      Serial.println("Communication with WiFi module failed!");
      setNEO(255,255,0);
      // don't continue
      while (true);
  }
  
  // waiting for connection to Wifi network set with the SetupWiFiConnection sketch
  setNEO(0,0,255);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
  }

  mqtt.begin();
  mqtt.enableNTPTime(true, NULL, 3, "0.pool.ntp.org", NULL, NULL);
  char *time_from_ESP;
  mqtt.getNTPTime(&time_from_ESP);
  Serial.println(time_from_ESP);
  server.begin();

  IPAddress ip = WiFi.localIP();
  Serial.println();
  Serial.println("Connected to WiFi network.");
  Serial.print("To access the server, enter \"http://");
  Serial.print(ip);
  Serial.println("/\" in web browser.");
  setNEO(0,128,0);
}

void loop() {

  WiFiClient client = server.available();
  if (client) {
    IPAddress ip = client.remoteIP();
    Serial.print("new client ");
    Serial.println(ip);
    delay(300);

    while (client.connected()) {
      if (client.available()) {
        String line = client.readStringUntil('\n');
        line.trim();
        Serial.println(line);

        // if you've gotten to the end of the HTTP header (the line is blank),
        // the http request has ended, so you can send a reply
        if (line.length() == 0) {
          // send a standard http response header
          Serial.println("Send response");
          client.println("HTTP/1.1 200 OK");
          client.println("Content-Type: text/html");
          client.println("Connection: close");  // the connection will be closed after completion of the response
          client.println("Refresh: 5");  // refresh the page automatically every 5 sec
          client.println();
          client.println("<!DOCTYPE HTML>");
          client.println("<html>");
          client.println("<p>");
          char *time_from_ESP;
          mqtt.getNTPTime(&time_from_ESP);
          client.println(time_from_ESP);
          client.println("</html>");
          client.flush();
          break;
        }
      }
    }

    // close the connection:
    client.stop();
    Serial.println("client disconnected");
  }
}
