#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/aon_timer.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/time.h>


#include "hardware/pll.h"
#include "hardware/clocks.h"
#include "hardware/structs/pll.h"
#include "hardware/structs/clocks.h"


#include "sha256.h"

#define BUFFER_SZ 4096

/**************************** DATA TYPES ****************************/
typedef struct lfsr128_t {
  uint64_t lfsr_h;
  uint64_t lfsr_l;
} lfsr128_t;

typedef struct lfsr128x3_t {
  lfsr128_t lfsr[3];
} lfsr128x3_t;

lfsr128x3_t lfsr;

uint8_t buffer[BUFFER_SZ];

void lfsr128_set_password(lfsr128_t *l, unsigned char *p);
void lfsr128_init(lfsr128_t *l, uint64_t lfsr_h, uint64_t lfsr_l);
uint64_t lfsr128_shift(lfsr128_t *l);
uint64_t lfsr128_shiftn(lfsr128_t *l, uint8_t n);
uint64_t lfsr128_shift_with_mult_dec(lfsr128x3_t *l);
uint64_t lfsr128_shiftn_with_mult_dec(lfsr128x3_t *l, uint8_t n);
uint64_t lfsr128_shift_return_carry(lfsr128_t *l);
void lfsr128x3_set_password(lfsr128x3_t *l, unsigned char *p);
uint64_t lfsr128_shift_with_mult_dec(lfsr128x3_t *l);

//
// LED stuff
//

//#define MYLED LED_BUILTIN
#define MYLED PC13 // Blackpill or Bluepill
//#define MYLED 14
//#define MYLED 19  // ESP-C3-12F

#define YIELDNEEDED 0

#define NEOPIXEL 0
#define ESP32NEOPIXEL 0

#define ESP_WIFI_SLEEP 0

#if ESP_WIFI_SLEEP
#include <WiFi.h>
#endif

#if NEOPIXEL
//#define LED_PIN 11  // Jade Pebble
//#define LED_PIN 2         // Carbon V3 - ESP32
//#define LED_ENABLE_PIN 4  // Carbon V3 - ESP32
#define LED_PIN 1         // Carbon S2 - ESP32-S2
#define LED_ENABLE_PIN 2  // Carbon S2 - ESP32-S2
#define LED_COUNT 1
#define BRIGHTNESS 50
#include <Adafruit_NeoPixel.h>
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

void colorWipe(uint32_t color, int wait) {
  for (int i = 0; i < strip.numPixels(); i++) {  // For each pixel in strip...
    strip.setPixelColor(i, color);               //  Set pixel's color (in RAM)
    strip.show();                                //  Update strip to match
    delay(wait);                                 //  Pause for a moment
  }
}

#endif

#if ESP_WIFI_SLEEP
void initWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin("KIDS", "12345678sims");
  //Serial.print("Connecting to WiFi ..");
  while (WiFi.status() != WL_CONNECTED) {
    //Serial.print('.');
    delay(1000);
  }
  //Serial.println(WiFi.localIP());
}

void sleepWiFi() {
  WiFi.setSleep(WIFI_PS_MAX_MODEM);
  //Serial.println("Modem asleep");
}

#endif


void lfsr128_set_password(lfsr128_t *l, unsigned char *p) {
  BYTE buf[SHA256_BLOCK_SIZE];
  SHA256_CTX ctx;
  uint64_t lfsr_h;
  uint64_t lfsr_l;

  sha256_init(&ctx);
  sha256_update(&ctx, p, strlen((char *)p));
  sha256_final(&ctx, buf);
  memcpy(&lfsr_h, buf, sizeof(uint64_t));
  memcpy(&lfsr_l, buf + sizeof(uint64_t), sizeof(uint64_t));
  lfsr128_init(l, lfsr_h, lfsr_l);
}

void lfsr128x3_set_from_captain(lfsr128_t *captain, lfsr128x3_t *l) {
  l->lfsr[0].lfsr_h = lfsr128_shiftn(captain, 64);
  l->lfsr[0].lfsr_l = lfsr128_shiftn(captain, 64);
  l->lfsr[1].lfsr_h = lfsr128_shiftn(captain, 64);
  l->lfsr[1].lfsr_l = lfsr128_shiftn(captain, 64);
  l->lfsr[2].lfsr_h = lfsr128_shiftn(captain, 64);
  l->lfsr[2].lfsr_l = lfsr128_shiftn(captain, 64);
}

void lfsr128x3_set_password(lfsr128x3_t *l, unsigned char *p) {
  lfsr128_t lfsr128_captain;

  lfsr128_set_password(&lfsr128_captain, p);
  lfsr128x3_set_from_captain(&lfsr128_captain, l);
}

void lfsr128x3_set_init_state(lfsr128x3_t *l, lfsr128_t *initState) {
  l->lfsr[0].lfsr_h = initState->lfsr_h;
  l->lfsr[0].lfsr_l = initState->lfsr_l;
  l->lfsr[1].lfsr_h = initState->lfsr_h;
  l->lfsr[1].lfsr_l = initState->lfsr_l;
  l->lfsr[2].lfsr_h = initState->lfsr_h;
  l->lfsr[2].lfsr_l = initState->lfsr_l;
}

void lfsr128x3_set_cap_state(lfsr128x3_t *l, lfsr128_t *initState) {
  lfsr128_t lfsr128_captain;

  lfsr128_init(&lfsr128_captain, initState->lfsr_h, initState->lfsr_l);
  lfsr128x3_set_from_captain(&lfsr128_captain, l);
}

void lfsr128_init(lfsr128_t *l, uint64_t lfsr_h, uint64_t lfsr_l) {
  l->lfsr_h = lfsr_h;
  l->lfsr_l = lfsr_l;
}

uint64_t lfsr128_shift(lfsr128_t *l) {
  uint64_t bit, bit_h, r;
  r = l->lfsr_l & 1;
  bit = ((l->lfsr_l >> 0) ^ (l->lfsr_l >> 1) ^ (l->lfsr_l >> 2) ^ (l->lfsr_l >> 7)) & 1;
  bit_h = l->lfsr_h & 1;
  l->lfsr_l = (l->lfsr_l >> 1) | (bit_h << 63);
  l->lfsr_h = (l->lfsr_h >> 1) | (bit << 63);

  return r;
}

/* 
 * Return the carry bit, not the shited out bit
 */
uint64_t lfsr128_shift_return_carry(lfsr128_t *l) {
  uint64_t bit, bit_h;
  bit = ((l->lfsr_l >> 0) ^ (l->lfsr_l >> 1) ^ (l->lfsr_l >> 2) ^ (l->lfsr_l >> 7)) & 1;
  bit_h = l->lfsr_h & 1;
  l->lfsr_l = (l->lfsr_l >> 1) | (bit_h << 63);
  l->lfsr_h = (l->lfsr_h >> 1) | (bit << 63);

  return bit;
}

uint64_t lfsr128_shiftn(lfsr128_t *l, uint8_t n) {
  uint64_t r = 0;
  int i;
  r = lfsr128_shift(l);
  for (i = 0; i < n - 1; i++) {
    r = r << 1;
    r = r | lfsr128_shift(l);
  }

  return r;
}

uint64_t lfsr128_shift_with_mult_dec(lfsr128x3_t *l) {
  uint64_t r0, r1, r2;

  r0 = lfsr128_shift(&l->lfsr[0]);
  r1 = lfsr128_shift(&l->lfsr[1]);
  r2 = lfsr128_shift_return_carry(&l->lfsr[2]);

  if (r2 == 1) {
    /* Decimate r0 by 1 bit, r2 by 2 bits*/
    r0 = lfsr128_shift(&l->lfsr[0]);
    r1 = lfsr128_shift(&l->lfsr[1]);
    r1 = lfsr128_shift(&l->lfsr[1]);
  }

  return r0 ^ r1;
}

uint64_t lfsr128_shiftn_with_mult_dec(lfsr128x3_t *l, uint8_t n) {
  uint64_t r = 0;
  int i;

  r = lfsr128_shift_with_mult_dec(l);
  for (i = 0; i < n - 1; i++) {
    r = r << 1;
    r = r | lfsr128_shift_with_mult_dec(l);
  }

  return r;
}

void code_buffer(uint8_t *b, lfsr128x3_t *l, int sz) {
  for (int i = 0; i < sz; i++) {
    b[i] = b[i] ^ (uint8_t)lfsr128_shiftn_with_mult_dec(l, 8);
  }
}

void do_print_random_numbers(lfsr128x3_t *l, int sz) {
  uint64_t ln = 0;

  do {
    ln++;
    printf("%03d\n", (uint8_t)lfsr128_shiftn_with_mult_dec(l, 8));
  } while (ln < sz);
}

void measure_freqs(void) {
    uint f_pll_sys = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_PLL_SYS_CLKSRC_PRIMARY);
    uint f_pll_usb = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_PLL_USB_CLKSRC_PRIMARY);
    uint f_rosc = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_ROSC_CLKSRC);
    uint f_clk_sys = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_CLK_SYS);
    uint f_clk_peri = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_CLK_PERI);
    uint f_clk_usb = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_CLK_USB);
    uint f_clk_adc = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_CLK_ADC);
#ifdef CLOCKS_FC0_SRC_VALUE_CLK_RTC
    uint f_clk_rtc = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_CLK_RTC);
#endif

    printf("pll_sys  = %dkHz\n", f_pll_sys);
    printf("pll_usb  = %dkHz\n", f_pll_usb);
    printf("rosc     = %dkHz\n", f_rosc);
    printf("clk_sys  = %dkHz\n", f_clk_sys);
    printf("clk_peri = %dkHz\n", f_clk_peri);
    printf("clk_usb  = %dkHz\n", f_clk_usb);
    printf("clk_adc  = %dkHz\n", f_clk_adc);
#ifdef CLOCKS_FC0_SRC_VALUE_CLK_RTC
    printf("clk_rtc  = %dkHz\n", f_clk_rtc);
#endif

    // Can't measure clk_ref / xosc as it is the ref
}

static void alarm_callback(void) {
    printf("Alarm fired\n");
    stdio_flush();
}

int main() {
    stdio_init_all();

#if NEOPIXEL
#if ESP32NEOPIXEL
  pinMode(LED_ENABLE_PIN, OUTPUT);
  digitalWrite(LED_ENABLE_PIN, 0);
#endif
  strip.begin();            // INITIALIZE NeoPixel strip object (REQUIRED)
  strip.show();             // Turn OFF all pixels ASAP
  strip.setBrightness(50);  // Set BRIGHTNESS to about 1/5 (max = 255)
  colorWipe(strip.Color(0, 0, 0), 500);
#endif

  // initialize digital pin MYLED as an output.
#if MYLED
  pinMode(MYLED, OUTPUT);
  digitalWrite(MYLED, LOW);
#endif
  printf("Init...\n");
  sleep_ms(5000);
  printf("Start...\n");
#if MYSERIAL
  mySerial.println(F("mySerial Start..."));
#endif

#if ESP_WIFI_SLEEP
  //initWiFi();
  sleepWiFi();
#endif

  lfsr128x3_set_password(&lfsr, (unsigned char *)"password1234");
  for (int i = 0; i < BUFFER_SZ; i++) {
    buffer[i] = (uint8_t)i % 256;
  }

#if MYLED
  digitalWrite(MYLED, HIGH);
#endif

#if PICO_RP2350
    printf("I'm an RP2350 ");
    #ifdef __riscv
        printf("running RISC-V\n");
    #else
        printf("running ARM\n");
    #endif
#endif

  int count = 0;

  clock_t startt = clock();
  printf("Started at %u\n", startt);
  //Serial.printf("%02x %02x %02x %02x\n", buffer[0],buffer[1],buffer[2],buffer[3]);
  for (count = 0; count < 600; count++) {
#if YIELDNEEDED
    vTaskDelay(1);
    taskYIELD();
#endif
    code_buffer(buffer, &lfsr, BUFFER_SZ);
  }

  clock_t endt = clock();
  printf("Ended at %u\n", endt);
  printf("%d\n", count);
  printf("%d\n", (int) (endt - startt));



    measure_freqs();

    // Change clk_sys to be 48MHz. The simplest way is to take this from PLL_USB
    // which has a source frequency of 48MHz
    clock_configure(clk_sys,
                    CLOCKS_CLK_SYS_CTRL_SRC_VALUE_CLKSRC_CLK_SYS_AUX,
                    CLOCKS_CLK_SYS_CTRL_AUXSRC_VALUE_CLKSRC_PLL_USB,
                    48 * MHZ,
                    48 * MHZ);

    // Turn off PLL sys for good measure
    pll_deinit(pll_sys);

    // CLK peri is clocked from clk_sys so need to change clk_peri's freq
    clock_configure(clk_peri,
                    0,
                    CLOCKS_CLK_PERI_CTRL_AUXSRC_VALUE_CLK_SYS,
                    48 * MHZ,
                    48 * MHZ);

    // Re init uart now that clk_peri has changed
    stdio_init_all();

    measure_freqs();
    printf("Hello, 48MHz\n");

sleep_ms(10000);

struct timespec ts;
struct timeval tv;
gettimeofday(&tv, NULL);
ts.tv_sec = tv.tv_sec;
ts.tv_nsec = tv.tv_usec * 1000;
ts.tv_sec = ts.tv_sec + 10;
aon_timer_enable_alarm (&ts, (aon_timer_alarm_handler_t) alarm_callback, false);

printf("Go into loop\n");
stdio_flush();

  for (;;) {
#if NEOPIXEL
    colorWipe(strip.Color(255, 0, 0), 500);  // Blue
#endif
#if MYLED
    digitalWrite(MYLED, HIGH);  // turn the LED on (HIGH is the voltage level)
#endif
    sleep_ms(250);  // wait for a second
#if NEOPIXEL
    colorWipe(strip.Color(0, 0, 0), 500);  // Blue
#endif
#if MYLED
    digitalWrite(MYLED, LOW);  // turn the LED off by making the voltage LOW
#endif
    sleep_ms(250);  // wait for a second
  }
}