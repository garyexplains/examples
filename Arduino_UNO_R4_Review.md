# Arduino UNO R4 Review

Notes for my video review of the UNO R4: https://youtu.be/-QByW6aQ_og

## Code

```
#include "Arduino_LED_Matrix.h"
ArduinoLEDMatrix matrix;

#define ROWS 8
#define COLUMNS 12
#define HALFCOLS 6

uint8_t clearframe[ROWS][COLUMNS] = {
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
};

uint8_t frame[ROWS][COLUMNS] = {
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
};

uint8_t zeroframe[ROWS][HALFCOLS] = {
  { 0, 0, 1, 1, 1, 0 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 0, 1, 1, 1, 0 }
};

uint8_t oneframe[ROWS][HALFCOLS] = {
  { 0, 0, 0, 0, 1, 0 }, 
  { 0, 0, 0, 1, 1, 0 }, 
  { 0, 0, 0, 0, 1, 0 }, 
  { 0, 0, 0, 0, 1, 0 }, 
  { 0, 0, 0, 0, 1, 0 }, 
  { 0, 0, 0, 0, 1, 0 }, 
  { 0, 0, 0, 0, 1, 0 }, 
  { 0, 0, 0, 1, 1, 1 }
};

uint8_t twoframe[ROWS][HALFCOLS] = {
  { 0, 0, 1, 1, 1, 0 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 0, 0, 0, 0, 1 }, 
  { 0, 0, 1, 1, 1, 0 }, 
  { 0, 1, 0, 0, 0, 0 }, 
  { 0, 1, 0, 0, 0, 0 }, 
  { 0, 1, 0, 0, 0, 0 }, 
  { 0, 0, 1, 1, 1, 1 }
};

uint8_t threeframe[ROWS][HALFCOLS] = {
  { 0, 0, 1, 1, 1, 0 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 0, 0, 0, 0, 1 }, 
  { 0, 0, 1, 1, 1, 0 }, 
  { 0, 0, 0, 0, 0, 1 }, 
  { 0, 0, 0, 0, 0, 1 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 0, 1, 1, 1, 0 }
};

uint8_t fourframe[ROWS][HALFCOLS] = {
  { 0, 1, 0, 0, 0, 0 }, 
  { 0, 1, 0, 0, 0, 0 }, 
  { 0, 1, 0, 1, 0, 0 }, 
  { 0, 1, 0, 1, 0, 0 }, 
  { 0, 1, 1, 1, 1, 1 }, 
  { 0, 0, 0, 1, 0, 0 }, 
  { 0, 0, 0, 1, 0, 0 }, 
  { 0, 0, 0, 1, 0, 0 }
};

uint8_t fiveframe[ROWS][HALFCOLS] = {
  { 0, 0, 1, 1, 1, 1 }, 
  { 0, 1, 0, 0, 0, 0 }, 
  { 0, 1, 0, 0, 0, 0 }, 
  { 0, 1, 0, 0, 0, 0 }, 
  { 0, 0, 1, 1, 1, 0 }, 
  { 0, 0, 0, 0, 0, 1 }, 
  { 0, 0, 0, 0, 0, 1 }, 
  { 0, 1, 1, 1, 1, 0 }
};

uint8_t sixframe[ROWS][HALFCOLS] = {
  { 0, 0, 1, 1, 1, 0 }, 
  { 0, 1, 0, 0, 0, 0 }, 
  { 0, 1, 0, 0, 0, 0 }, 
  { 0, 1, 0, 0, 0, 0 }, 
  { 0, 1, 1, 1, 1, 0 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 0, 1, 1, 1, 0 }
};

uint8_t sevenframe[ROWS][HALFCOLS] = {
  { 0, 1, 1, 1, 1, 0 }, 
  { 0, 0, 0, 0, 0, 1 }, 
  { 0, 0, 0, 0, 0, 1 }, 
  { 0, 0, 0, 0, 1, 0 }, 
  { 0, 0, 0, 0, 1, 0 }, 
  { 0, 0, 0, 1, 0, 0 }, 
  { 0, 0, 0, 1, 0, 0 }, 
  { 0, 0, 1, 0, 0, 0 }
};

uint8_t eightframe[ROWS][HALFCOLS] = {
  { 0, 0, 1, 1, 1, 0 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 1, 1, 1, 1, 1 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 0, 1, 1, 1, 0 }
};

uint8_t nineframe[ROWS][HALFCOLS] = {
  { 0, 0, 1, 1, 1, 0 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 1, 0, 0, 0, 1 }, 
  { 0, 0, 1, 1, 1, 1 }, 
  { 0, 0, 0, 0, 0, 1 }, 
  { 0, 0, 0, 0, 0, 1 }, 
  { 0, 0, 0, 0, 0, 1 }, 
  { 0, 1, 1, 1, 1, 0 }
};

uint8_t *digits[10] = {
  (uint8_t *) zeroframe,
  (uint8_t *) oneframe,
  (uint8_t *) twoframe,
  (uint8_t *) threeframe,
  (uint8_t *) fourframe,
  (uint8_t *) fiveframe,
  (uint8_t *) sixframe,
  (uint8_t *) sevenframe,
  (uint8_t *) eightframe,
  (uint8_t *) nineframe
};

void frametwodigitnum(uint8_t d, uint8_t *dest) {
  uint8_t l, r;
  l = d / 10;
  r = d % 10;
  digitleft(l, dest);
  digitright(r, dest);
}

void digitleft(uint8_t d, uint8_t *dest) {
  copytoleft(digits[d], dest);
}

void digitright(uint8_t d, uint8_t *dest) {
  copytoright(digits[d], dest);
}

void copytoleft(uint8_t *halfframe, uint8_t *dest) {
  // Half frame (i.e. a single digit) is 8 x 6 (ROWS x HALFCOLS)
  for (int i=0;i<ROWS;i++) {
    for (int j=0;j<HALFCOLS;j++) {
      dest[(i*COLUMNS)+j] = halfframe[(i*HALFCOLS)+j];
    }
  }
}

void copytoright(uint8_t *halfframe, uint8_t *dest) {
  // Half frame (i.e. a single digit) is 8 x 6 (ROWS x HALFCOLS)
  for (int i=0;i<ROWS;i++) {
    for (int j=0;j<HALFCOLS;j++) {
      dest[(i*COLUMNS)+j+HALFCOLS] = halfframe[(i*HALFCOLS)+j];
    }
  }
}

void cls() {
    memcpy(frame, clearframe, ROWS * COLUMNS);
    matrix.renderBitmap(frame, ROWS, COLUMNS);
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  delay(1500);
  matrix.begin();
}

void loop() {
    for(int i=0;i<99;i++) {
      cls();
      frametwodigitnum(i, (uint8_t *) frame);
      matrix.renderBitmap(frame, ROWS, COLUMNS);
      delay(500);
    }
}
```
