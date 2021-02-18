#include "pico/stdlib.h"
#include <stdio.h>

int main() {
  stdio_init_all();

  const uint LED_PIN = 25;
  gpio_init(LED_PIN);
  gpio_set_dir(LED_PIN, GPIO_OUT);
  while (true) {
    gpio_put(LED_PIN, 1);
    printf("ON\n");
    sleep_ms(1000);
    gpio_put(LED_PIN, 0);
    printf("OFF\n");
    sleep_ms(1000);
  }
  return 0;
}
