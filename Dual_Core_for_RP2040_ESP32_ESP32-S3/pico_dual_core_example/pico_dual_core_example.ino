// RP2040 dual-core example
// Gary Sims October 2022

// RP2040: Arduino code will normally execute only on core 0,
// with the 2nd core sitting idle in a low power state.

int count0, count1;

void setup() {

  Serial.begin(115200);
  while (!Serial) {
    delay(1);  // wait for serial port to connect.
  }

  count0 = 0;
}

void setup1() {
  count1 = 1000;
}

void loop() {
  Serial.printf("loop(): %d\n", count0);
  count0++;
  if (count0 > 1000)
    count0 = 0;
  delay(1000);
}

void loop1() {
  Serial.printf("loop1(): %d\n", count1);
  count1--;
  if(count1<=0)
    count1 = 1000;
  delay(2500);
}
