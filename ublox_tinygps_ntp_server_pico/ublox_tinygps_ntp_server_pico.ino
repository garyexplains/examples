#include <WiFi.h>
#include <WiFiUdp.h>

#include <TimeLib.h>
#include <TinyGPSPlus.h>

#include "arduino_secrets.h"
///////please enter your sensitive data in the Secret tab/arduino_secrets.h
char ssid[] = SECRET_SSID;        // your network SSID (name)
char pass[] = SECRET_PASS;    // your network password (use for WPA, or use as key for WEP)

WiFiClient wifiClient;
WiFiUDP Udp;
unsigned int ntpPort = 123;  // ntp port to listen on

// buffers for receiving and sending data
char packetBuffer[UDP_TX_PACKET_MAX_SIZE + 1];  // buffer to hold incoming packet,

#define rxPin 1   // Raspberry Pi Pico W
#define txPin 0   // Raspberry Pi Pico W

// The TinyGPSPlus object
TinyGPSPlus gps;
int last_gps_time_sync = 0;
unsigned long millis_at_last_gps_time_sync = 0;
int SYNC_TIME_GPS_INTERVAL = 60; // In seconds


typedef struct ntp_time
{
  uint32_t seconds;
  uint32_t fraction;
} NTPTime;

// NTP data structures
typedef struct ntp_packet
{
  uint8_t  flags;
  uint8_t  stratum;
  uint8_t  poll;
  int8_t   precision;
  uint32_t delay;
  uint32_t dispersion;
  uint8_t  ref_id[4];
  NTPTime  ref_time;
  NTPTime  orig_time;
  NTPTime  recv_time;
  NTPTime  xmit_time;
} NTPPacket;

#define NTP_get_leap_indicator(value)    ((value>>6)&0x03)
#define NTP_get_version(value)  ((value>>3)&0x07)
#define NTP_get_mode(value)  (value&0x07)

#define NTP_set_leap_indicator(value)    ((value&0x03)<<6)
#define NTP_set_version(value)  ((value&0x07)<<3)
#define NTP_set_mode(value)  ((value&0x07))


#define LI_NONE         0
#define LI_SIXTY_ONE    1
#define LI_FIFTY_NINE   2
#define LI_NOSYNC       3

#define MODE_RESERVED   0
#define MODE_ACTIVE     1
#define MODE_PASSIVE    2
#define MODE_CLIENT     3
#define MODE_SERVER     4
#define MODE_BROADCAST  5
#define MODE_CONTROL    6
#define MODE_PRIVATE    7

#define NTP_VERSION     4

#define REF_ID          "GPS "

#define YEARS70   2208988800L
#define to_UNIX_epoch(t)      ((uint32_t)t-YEARS70) // 1970
#define to_NTP_epoch(t)        ((uint32_t)t+YEARS70) // 1900

void set_date_time_from_gps() {
  int Year, Month, Day, Hour, Minute, Second;
  tmElements_t tm;

  if ( (gps.time.isValid()) && (gps.date.isValid()) ) {
    tm.Second = gps.time.second();
    tm.Minute = gps.time.minute();
    tm.Hour = gps.time.hour();
    tm.Day = gps.date.day();
    tm.Month = gps.date.month();
    tm.Year = gps.date.year() - 1970;
    time_t t = makeTime(tm);
    setTime(t);
  }
}

void print_date_time() {
  // print date and time
  Serial.printf("%02d:%02d:%02d %02d/%02d/%02d\n", hour(), minute(), second(), day(), month(), year());
}

void print_time_t(time_t t, bool newline) {
  tmElements_t tm;
  breakTime(t, tm);
  Serial.printf("%02d:%02d:%02d %02d/%02d/%d", tm.Hour, tm.Minute, tm.Second, tm.Day, tm.Month, tm.Year + 1970);
  if (newline)
    Serial.println();
}

void print_ntp_time(NTPTime *ntp_t, bool newline) {
  tmElements_t tm;
  breakTime(to_UNIX_epoch(ntp_t->seconds), tm);
  uint32_t usec = (uint32_t)((double)ntp_t->fraction * 1.0e6 / (double)(1LL << 32));
  Serial.printf("%02d:%02d:%02d.%d %02d/%02d/%d", tm.Hour, tm.Minute, tm.Second, usec / 1000, tm.Day, tm.Month, tm.Year + 1970);
  if (newline)
    Serial.println();
}

void print_digits(int digits) {
  Serial.print(":");
  if (digits < 10)
    Serial.print('0');
  Serial.print(digits);
}

void dump_NTP_packet(NTPPacket *ntp)
{
  time_t n = now();
  Serial.print("Time NTP Epoch: ");
  Serial.println(to_NTP_epoch(n));
  Serial.printf("Time UNIX Epoch: %d\n", n);
  Serial.print("Now: ");
  print_time_t(n, true);
  Serial.print("size:");
  Serial.println(sizeof(*ntp));
  Serial.print("li: ");
  Serial.println(NTP_get_leap_indicator(ntp->flags));
  Serial.print("version: ");
  Serial.println(NTP_get_version(ntp->flags));
  Serial.print("mode: ");
  Serial.println(NTP_get_mode(ntp->flags));
  Serial.print("stratum: ");
  Serial.println(ntp->stratum);
  Serial.print("poll: ");
  Serial.println(ntp->poll);
  Serial.print("precision: ");
  Serial.println(ntp->precision);
  Serial.print("delay: ");
  Serial.println(ntp->delay);
  Serial.print("dispersion: ");
  Serial.println(ntp->dispersion);
  Serial.print("ref_id: ");
  Serial.print(ntp->ref_id[0]);
  Serial.print(ntp->ref_id[1]);
  Serial.print(ntp->ref_id[2]);
  Serial.println(ntp->ref_id[3]);
  Serial.print("ref_time: ");
  Serial.print(ntp->ref_time.seconds);
  Serial.print(".");
  Serial.println(ntp->ref_time.fraction);
  Serial.print("ref_time: ");
  print_ntp_time(&ntp->ref_time, true);
  Serial.print("orig_time: ");
  Serial.print(ntp->orig_time.seconds);
  Serial.print(".");
  Serial.println(ntp->orig_time.fraction);
  Serial.print("orig_time: ");
  print_ntp_time(&ntp->orig_time, true);
  Serial.print("recv_time: ");
  Serial.print(ntp->recv_time.seconds);
  Serial.print(".");
  Serial.println(ntp->recv_time.fraction);
  Serial.print("recv_time: ");
  print_ntp_time(&ntp->recv_time, true);
  Serial.print("xmit_time: ");
  Serial.print(ntp->xmit_time.seconds);
  Serial.print(".");
  Serial.println(ntp->xmit_time.fraction);
  Serial.print("xmit_time: ");
  print_ntp_time(&ntp->xmit_time, true);
}

void ntp_reply(NTPPacket *ntpin, NTPPacket *ntpout, NTPTime *r) {
  //
  // Build the response
  //
  ntpout->flags      = NTP_set_leap_indicator(LI_NONE) | NTP_set_version(NTP_VERSION) | NTP_set_mode(MODE_SERVER);
  ntpout->stratum    = 1;
  ntpout->precision  = 0; // 1 second???
  // TODO: compute actual root delay, and root dispersion
  ntpout->delay = 1;      //(uint32)(0.000001 * 65536.0);
  ntpout->dispersion = 1; //(uint32_t)(_gps.getDispersion() * 65536.0); // TODO: pre-calculate this?
  strncpy((char*)ntpout->ref_id, REF_ID, sizeof(ntpin->ref_id));
  ntpout->orig_time.seconds  = ntpin->xmit_time.seconds;
  ntpout->orig_time.fraction  = ntpin->xmit_time.fraction;
  ntpout->recv_time.seconds  = r->seconds;
  ntpout->recv_time.fraction  = r->fraction;
  ntpout->ref_time.seconds = to_NTP_epoch(last_gps_time_sync);
  ntpout->ref_time.fraction = 0;
  ntpout->xmit_time.seconds = to_NTP_epoch(now());
  unsigned long mi = millis();
  unsigned long xmit_usec = ((mi - millis_at_last_gps_time_sync) - ((to_UNIX_epoch(ntpout->xmit_time.seconds) - last_gps_time_sync) * 1000) ) * 1000;
  ntpout->xmit_time.fraction = (uint32_t)((double)(xmit_usec + 1) * (double)(1LL << 32) * 1.0e-6);
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(500);
  }
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());
  Serial.printf("UDP server on port %d\n", ntpPort);
  Udp.begin(ntpPort);
}

void setup1() {
  Serial1.setRX(rxPin);
  Serial1.setTX(txPin);
  Serial1.setFIFOSize(128);
  Serial1.begin(9600);
}

void loop() {
    NTPPacket ntp, ntpreply;
    NTPTime   recv_time;
    unsigned long mi;
    unsigned long xmit_usec;
  
    int packetSize = Udp.parsePacket();
    if (packetSize) {
      recv_time.seconds = to_NTP_epoch(now());
      mi = millis();
      xmit_usec = ((mi - millis_at_last_gps_time_sync) - ((to_UNIX_epoch(recv_time.seconds) - last_gps_time_sync) * 1000) ) * 1000;
      recv_time.fraction = (uint32_t)((double)(xmit_usec + 1) * (double)(1LL << 32) * 1.0e-6);
      Serial.printf("Received packet from %s:%d\n", Udp.remoteIP().toString().c_str(), Udp.remotePort());
      
      // read the packet into packetBufffer
      int n = Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);
      packetBuffer[n] = 0;
      memcpy(&ntp, packetBuffer, sizeof(ntp));
      
      // Deal with network byte order
      ntp.delay              = ntohl(ntp.delay);
      ntp.dispersion         = ntohl(ntp.dispersion);
      ntp.orig_time.seconds  = ntohl(ntp.orig_time.seconds);
      ntp.orig_time.fraction = ntohl(ntp.orig_time.fraction);
      ntp.ref_time.seconds   = ntohl(ntp.ref_time.seconds);
      ntp.ref_time.fraction  = ntohl(ntp.ref_time.fraction);
      ntp.recv_time.seconds  = ntohl(ntp.recv_time.seconds);
      ntp.recv_time.fraction = ntohl(ntp.recv_time.fraction);
      ntp.xmit_time.seconds  = ntohl(ntp.xmit_time.seconds);
      ntp.xmit_time.fraction = ntohl(ntp.xmit_time.fraction);

      // Bit of debug output
      Serial.printf("Time on client is ");
      print_ntp_time(&ntp.xmit_time, true);
      //dump_NTP_packet(&ntp);
      
      // Create the reply
      ntp_reply(&ntp, &ntpreply, &recv_time);

      // Bit more debug output
      Serial.printf("Sending reply at ");
      print_ntp_time(&ntpreply.xmit_time, true);
      //dump_NTP_packet(&ntpreply);

      ntpreply.delay              = htonl(ntpreply.delay);
      ntpreply.dispersion         = htonl(ntpreply.dispersion);
      ntpreply.orig_time.seconds  = htonl(ntpreply.orig_time.seconds);
      ntpreply.orig_time.fraction = htonl(ntpreply.orig_time.fraction);
      ntpreply.ref_time.seconds   = htonl(ntpreply.ref_time.seconds);
      ntpreply.ref_time.fraction  = htonl(ntpreply.ref_time.fraction);
      ntpreply.recv_time.seconds  = htonl(ntpreply.recv_time.seconds);
      ntpreply.recv_time.fraction = htonl(ntpreply.recv_time.fraction);
      ntpreply.xmit_time.seconds  = htonl(ntpreply.xmit_time.seconds);
      ntpreply.xmit_time.fraction = htonl(ntpreply.xmit_time.fraction);  

      Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
      Udp.write((uint8_t*) &ntpreply, sizeof(ntpreply));
      Udp.endPacket();
    }
}
void loop1() {
  while (Serial1.available() > 0) {
    gps.encode(Serial1.read());
    if ( (last_gps_time_sync == 0) || (now() - last_gps_time_sync > SYNC_TIME_GPS_INTERVAL) ) {
      set_date_time_from_gps();
      print_date_time();
      //displayInfo();
      last_gps_time_sync = now();
      millis_at_last_gps_time_sync = millis();
    }
  }

  if (millis() > 5000 && gps.charsProcessed() < 10)
  {
    Serial.println(F("No GPS detected: check wiring."));
    while (true);
  }
}

void displayInfo()
{
  Serial.print(F("Location: "));
  if (gps.location.isValid())
  {
    Serial.print(gps.location.lat(), 6);
    Serial.print(F(","));
    Serial.print(gps.location.lng(), 6);
  }
  else
  {
    Serial.print(F("INVALID"));
  }

  Serial.print(F("  Date/Time: "));
  if (gps.date.isValid())
  {
    Serial.print(gps.date.month());
    Serial.print(F("/"));
    Serial.print(gps.date.day());
    Serial.print(F("/"));
    Serial.print(gps.date.year());
  }
  else
  {
    Serial.print(F("INVALID"));
  }

  Serial.print(F(" "));
  if (gps.time.isValid())
  {
    if (gps.time.hour() < 10) Serial.print(F("0"));
    Serial.print(gps.time.hour());
    Serial.print(F(":"));
    if (gps.time.minute() < 10) Serial.print(F("0"));
    Serial.print(gps.time.minute());
    Serial.print(F(":"));
    if (gps.time.second() < 10) Serial.print(F("0"));
    Serial.print(gps.time.second());
    Serial.print(F("."));
    if (gps.time.centisecond() < 10) Serial.print(F("0"));
    Serial.print(gps.time.centisecond());
  }
  else
  {
    Serial.print(F("INVALID"));
  }

  if (gps.location.isValid()) { // Assume that if the location is valid then so are the other attributes
    Serial.print(F("  # of satellites in use: "));
    Serial.print(gps.satellites.value());
    Serial.print(F("  Alt: "));
    Serial.print(gps.altitude.kilometers());
  }

  Serial.println();
}
