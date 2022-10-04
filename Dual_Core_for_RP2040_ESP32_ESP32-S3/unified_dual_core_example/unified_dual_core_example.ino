// Unified dual-core example
// Gary Sims October 2022

// RP2040: Arduino code will normally execute only on core 0,
// with the 2nd core sitting idle in a low power state.

// ESP32: Arduino code will run on which core is selected under
// "Arduino Runs On" menu

#if !defined(ESP_PLATFORM) && !defined(ARDUINO_ARCH_MBED_RP2040) && !defined(ARDUINO_ARCH_RP2040)
#pragma message("Unsupported platform")
#endif

// ESP32:
#if defined(ESP_PLATFORM)
TaskHandle_t task_loop1;
void esploop1(void* pvParameters) {
  setup1();
  
  for (;;)
    loop1();
}
#endif

#if defined(ARDUINO_ARCH_MBED_RP2040) || defined(ARDUINO_ARCH_RP2040)
#include <FreeRTOS.h>
#define xPortGetCoreID get_core_num
#endif

int count0, count1;

void setup() {

  Serial.begin(115200);
  while (!Serial) {
    delay(1);  // wait for serial port to connect.
  }

#if defined(ESP_PLATFORM)
  xTaskCreatePinnedToCore(
    esploop1,               /* Task function. */
    "loop1",                /* name of task. */
    10000,                  /* Stack size of task */
    NULL,                   /* parameter of the task */
    1,                      /* priority of the task */
    &task_loop1,            /* Task handle to keep track of created task */
    !ARDUINO_RUNNING_CORE); /* pin task to core 0 */
#endif

  count0 = 0;
}

void setup1() {
  count1 = 1000;
}

void loop() {
  Serial.printf("loop%d(): %d\n", xPortGetCoreID(), count0);
  count0++;
  if (count0 > 1000)
    count0 = 0;
  delay(1000);
}

void loop1() {
  Serial.printf("loop%d(): %d\n", xPortGetCoreID(), count1);
  count1--;
  if (count1 <= 0)
    count1 = 1000;
  delay(2500);
}