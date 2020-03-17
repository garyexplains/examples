/*
  My Smart Switch
  March 2020
  by Gary Sims
*/

#include <SPI.h>
#include <WiFi101.h>

#include "arduino_secrets.h"
// the IP address for the smart switch
IPAddress ip(192, 168, 1, 222);

///////please enter your sensitive data in the Secret tab/arduino_secrets.h
char ssid[] = SECRET_SSID;        // your network SSID (name)
char pass[] = SECRET_PASS;    // your network password (use for WPA, or use as key for WEP)
int keyIndex = 0;                 // your network key Index number (needed only for WEP)
String fixedf = "<P>" + String(__DATE__) + " " + String(__TIME__);

enum request_type {
  root,
  on,
  off,
  other,
  favicon,
  none
};

int status = WL_IDLE_STATUS;
#define RELAY_PIN1 7
#define RELAY_PIN2 8

WiFiServer server(80);

void setup() {
  // Very first thing is to configure the relay and make sure it is off
  pinMode(RELAY_PIN1, OUTPUT);
  digitalWrite(RELAY_PIN1, HIGH);
  pinMode(RELAY_PIN2, OUTPUT);
  digitalWrite(RELAY_PIN2, HIGH);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  //Initialize serial
  Serial.begin(9600);

  // check for the presence of the shield:
  if (WiFi.status() == WL_NO_SHIELD) {
    Serial.println("WiFi shield not present");
    // don't continue:
    while (true);
  }

  // Configure a static IP address
  WiFi.config(ip);

  // attempt to connect to WiFi network:
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to WiFi network.");
    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    status = WiFi.begin(ssid, pass);

    // wait 10 seconds for connection:
    delay(10000);
  }
  server.begin();
  // you're connected now, so print out the status:
  printWiFiStatus();
  digitalWrite(LED_BUILTIN, LOW);
}

void send_header(WiFiClient client) {
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: text/html");
  client.println("Connection: close");
  client.println();
}

void send_menu_in_html(WiFiClient client) {
  client.println("<P><button class=\"block\" onclick=\"window.location.href = '/on';\">ON</button>");
  client.println("<P><button class=\"block\" onclick=\"window.location.href = '/off';\">OFF</button>");
}

void send_html_head_and_open_body(WiFiClient client) {
  client.println("<!DOCTYPE HTML>");
  client.println("<html>");
  client.println("<head>");
  client.println("<style>");
  client.println(".block {");
  client.println("display: block;");
  client.println("width: 100%;");
  client.println("border: none;");
  client.println("background-color: #4CAF50;");
  client.println("padding: 32px 32px;");
  client.println("font-size: 32px;");
  client.println("cursor: pointer;");
  client.println("text-align: center;");
  client.println("}");
  client.println("</style>");
  client.println("</head>");
  client.println("<body>");
}

void send_html_closing_tags(WiFiClient client) {
  client.println(fixedf.c_str());
  client.println("</body>");
  client.println("</html>");
}
String req_buffer;
request_type rt = none;

void loop() {

  req_buffer = "";
  rt = none;

  // listen for incoming clients
  WiFiClient client = server.available();
  if (client) {
    Serial.println("new client");
    // an http request ends with a blank line
    bool currentLineIsBlank = true;
    while (client.connected()) {
      if (client.available()) {
        char c = client.read();
        req_buffer = req_buffer + c;

        //Serial.write(c);

        if (c == '\n' && currentLineIsBlank == false) {
          // End of a line and not a blank line
          //Serial.write(req_buffer.c_str());

          if (req_buffer.startsWith("GET ")) rt = other;
          if (req_buffer.startsWith("GET / ")) rt = root;
          if (req_buffer.startsWith("GET /on ")) rt = on;
          if (req_buffer.startsWith("GET /off ")) rt = off;
          if (req_buffer.startsWith("GET /favicon.ico ")) rt = favicon;
          //Serial.println(rt);
          req_buffer = "";
        }

        // if you've gotten to the end of the line (received a newline
        // character) and the line is blank, the http request has ended,
        // so you can send a reply
        if (c == '\n' && currentLineIsBlank) {

          // send a standard http response header
          send_header(client);

          if (rt == root) {
            send_html_head_and_open_body(client);
            client.println("<h1>Menu</h1>");
            send_menu_in_html(client);
            send_html_closing_tags(client);
          } else if (rt == on) {
            send_html_head_and_open_body(client);
            client.println("<p><strong>ON</strong>");
            send_menu_in_html(client);
            send_html_closing_tags(client);
          } else if (rt == off) {
            send_html_head_and_open_body(client);
            client.println("<p><strong>OFF</strong>");
            send_menu_in_html(client);
            send_html_closing_tags(client);
          } else {
            // Send blank line
            client.println("");
          }
          break;
        }
        if (c == '\n') {
          // you're starting a new line
          currentLineIsBlank = true;
        }
        else if (c != '\r') {
          // you've gotten a character on the current line
          currentLineIsBlank = false;
        }
      }
    }
    // give the web browser time to receive the data
    delay(1);

    // close the connection:
    client.stop();
    Serial.println("client disconnected");

    if (rt == on) {
      digitalWrite(RELAY_PIN1, LOW);
      digitalWrite(RELAY_PIN2, LOW);
      digitalWrite(LED_BUILTIN, HIGH);
      Serial.println("ON");
    } else if (rt == off) {
      digitalWrite(RELAY_PIN1, HIGH);
      digitalWrite(RELAY_PIN2, HIGH);
      digitalWrite(LED_BUILTIN, LOW);
      Serial.println("OFF");
    }
  }
}


void printWiFiStatus() {

  // print your WiFi shield's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}
