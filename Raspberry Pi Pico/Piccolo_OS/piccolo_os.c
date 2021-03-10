/*
 * Copyright (C) 2021 Gary Sims
 * All rights reserved.
 * 
 * Portions copyright (C) 2017 Scott Nelson
 * Portions copyright (C) 2015-2018 National Cheng Kung University, Taiwan
 * Portions copyright (C) 2014-2017 Chris Stones
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include "pico/stdlib.h"
#include <stdio.h>
#include "piccolo_os.h"

unsigned int *__piccolo_os_create_task(unsigned int *stack,
                                       void (*start)(void));
void __piccolo_task_init(void);
unsigned int *__piccolo_pre_switch(unsigned int *stack);
void __piccolo_task_init_stack(unsigned int *stack);

piccolo_os_internals_t piccolo_ctx;

/* Initialize user task stack and execute it once only
 * We set THREAD_PSP to LR so that exception return
 * works correctly.
 * THREAD_PSP means: Return to Thread mode.
 *                   Exception return gets state from the process stack.
 *                   Execution uses PSP after return.
 * See:
 * http://infocenter.arm.com/help/index.jsp?topic=/com.arm.doc.dui0552a/Babefdjc.html
 */
unsigned int *__piccolo_os_create_task(unsigned int *task_stack,
                                       void (*pointer_to_task_function)(void)) {

  /* This task_stack frame needs to mimic would be saved by hardware and by the
   * software (in isr_svcall) */

  /*
        Exception frame saved by the hardware onto task_stack:
        +------+
        | xPSR | task_stack[16] 0x01000000 i.e. PSR Thumb bit
        |  PC  | task_stack[15] pointer_to_task_function
        |  LR  | task_stack[14]
        |  R12 | task_stack[13]
        |  R3  | task_stack[12]
        |  R2  | task_stack[11]
        |  R1  | task_stack[10]
        |  R0  | task_stack[9]
        +------+
        Registers saved by the software (isr_svcall):
        +------+
        |  LR  | task_stack[8]	(THREAD_PSP i.e. 0xFFFFFFFD)
        |  R7  | task_stack[7]
        |  R6  | task_stack[6]
        |  R5  | task_stack[5]
        |  R4  | task_stack[4]
        |  R11 | task_stack[3]
        |  R10 | task_stack[2]
        |  R9  | task_stack[1]
        |  R8  | task_stack[0]
        +------+
        */

  task_stack += PICCOLO_OS_STACK_SIZE - 17; /* End of task_stack, minus what we are about to push */
  task_stack[8] = (unsigned int) PICCOLO_OS_THREAD_PSP;
  task_stack[15] = (unsigned int) pointer_to_task_function;
  task_stack[16] = (unsigned int) 0x01000000; /* PSR Thumb bit */
  task_stack = __piccolo_pre_switch(task_stack);

  return task_stack;
}

int piccolo_create_task(void (*pointer_to_task_function)(void)) {
  if (piccolo_ctx.task_count >= PICCOLO_OS_TASK_LIMIT)
    return -1;
  int tc = piccolo_ctx.task_count; // Just for readability
  piccolo_ctx.the_tasks[tc] =
      __piccolo_os_create_task(piccolo_ctx.task_stacks[tc], pointer_to_task_function);
  piccolo_ctx.task_count++;

  return piccolo_ctx.task_count - 1;
}

void piccolo_sleep(piccolo_sleep_t *start, int ticks) {
  *start = to_ms_since_boot(get_absolute_time());
  while (to_ms_since_boot(get_absolute_time()) < *start + ticks) {
    piccolo_yield();
  }
}

/* After a reset, processor is in thread mode
 * Switch to handler mode, so that the Piccolo OS kernel runs in handler mode,
 * and to ensure the correct return from an exception/interrupt later
 * when switching to a task
 */
void __piccolo_task_init(void) {
  unsigned int dummy[32];
  __piccolo_task_init_stack(dummy + 32);
}

void piccolo_init() {
  piccolo_ctx.task_count = 0;
  stdio_init_all();
  __piccolo_task_init();
}

void piccolo_start() {
  piccolo_ctx.current_task = 0;

  while (1) {
    piccolo_ctx.the_tasks[piccolo_ctx.current_task] =
        __piccolo_pre_switch(piccolo_ctx.the_tasks[piccolo_ctx.current_task]);

    piccolo_ctx.current_task++;
    if (piccolo_ctx.current_task >=
        piccolo_ctx.task_count)
      piccolo_ctx.current_task = 0;
  }
}