// Copyright (C) 2021 Gary Sims
// Use a simple FSM to verify a floating point number (as a string)
//
// Compile with:
// gcc -O3 -o floating_point_verification floating_point_verification.c

#include <stdio.h>
#include <string.h>

typedef enum {
  START,
  AFTER_MINUS,
  AFTER_DOT,
  internal_VALID_END_STATES,
  SECOND_DIGIT_ONWARDS,
  MANTISSA,
  internal_LAST_STATE
} FSM_STATES;

typedef struct {
  FSM_STATES state;
  char *tokens;
  FSM_STATES next_state;
} FSM_STATE_INFO;

int run(FSM_STATES start_state, FSM_STATE_INFO *state_machine, char *cargo) {

  FSM_STATE_INFO *p;
  FSM_STATES current_state = start_state;
  FSM_STATE_INFO *found;
  char *c = cargo;

  while (*c != 0) {
    found = NULL;
    p = state_machine;
    while (p->state != internal_LAST_STATE) {
      if (p->state == current_state) {
        if (strchr(p->tokens, *c) != NULL) {
          found = p;
          break;
        }
      }
      p++;
    }
    if (found != NULL) {
      current_state = p->next_state;
      c++;
    } else {
      printf("%s is bad. Failed at %c\n", cargo, *c);
      return -1;
    }
  }
  if (current_state > internal_VALID_END_STATES) {
    printf("%s is good.\n", cargo);
    return 1;
  } else {
    printf("%s is bad. More needed.\n", cargo);
    return -2;
  }
}

int main(int argc, char *argv[]) {
  static FSM_STATE_INFO state_machine[] = {
      {START, "1234567890", SECOND_DIGIT_ONWARDS},
      {START, "-", AFTER_MINUS},
      {AFTER_MINUS, "1234567890", SECOND_DIGIT_ONWARDS},
      {SECOND_DIGIT_ONWARDS, "1234567890", SECOND_DIGIT_ONWARDS},
      {SECOND_DIGIT_ONWARDS, ".", AFTER_DOT},
      {AFTER_DOT, "1234567890", MANTISSA},
      {MANTISSA, "1234567890", MANTISSA},
      {internal_LAST_STATE, "", internal_LAST_STATE}};

  run(START, state_machine, "3.14");
  run(START, state_machine, "-7");
  run(START, state_machine, "-22.0");
  run(START, state_machine, "--22.0");
  run(START, state_machine, "-22.a0");
  run(START, state_machine, "-1.");
  run(START, state_machine, "-");
}
