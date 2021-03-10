#ifndef PICCOLO_OS_H
#define PICCOLO_OS_H

/* Size of our user task stacks in words */
#define PICCOLO_OS_STACK_SIZE 256

/* Number of user task */
#define PICCOLO_OS_TASK_LIMIT 3

/* Exception return behavior */
#define PICCOLO_OS_THREAD_PSP 0xFFFFFFFD

struct {
  unsigned int task_stacks[PICCOLO_OS_TASK_LIMIT][PICCOLO_OS_STACK_SIZE];
  unsigned int *the_tasks[PICCOLO_OS_TASK_LIMIT];
  size_t task_count;
  size_t current_task;
} typedef piccolo_os_internals_t;

typedef uint32_t piccolo_sleep_t;

void piccolo_yield(void);
void piccolo_syscall(void);
void piccolo_task_init(void);
int piccolo_create_task(void (*pointer_to_task_function)(void));
void piccolo_sleep(piccolo_sleep_t *pointer_to_task_function, int ticks);
void piccolo_init();
void piccolo_start();
#endif