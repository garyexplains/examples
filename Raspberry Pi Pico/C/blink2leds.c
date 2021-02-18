#include "pico/stdlib.h"
#include <stdio.h>

int main() {
  stdio_init_all();

  const uint LED_PIN25 = 25;
  gpio_init(LED_PIN25);
  gpio_set_dir(LED_PIN25, GPIO_OUT);
  const uint LED_PIN14 = 14;
  gpio_init(LED_PIN14);
  gpio_set_dir(LED_PIN14, GPIO_OUT);
  while (true) {
    gpio_put(LED_PIN25, 1);
    gpio_put(LED_PIN14, 0);
    printf("ON/OFF\n");
    sleep_ms(1000);
    gpio_put(LED_PIN25, 0);
    gpio_put(LED_PIN14, 1);
    printf("OFF/ON\n");
    sleep_ms(1000);
  }
  return 0;
}
