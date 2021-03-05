# Piccolo OS
Piccolo OS is a small multitasking OS for the Raspberry Pi Pico. It is designed primarily as a teaching tool.
It demonstrates the fundamentals of a co-operative multitasking OS and the Arm Cortex-M0+.

## Limitations
Many! Including lack of per-task memory, multicore support, mutexes, queues, a file system, networking, a shell, and so on...

## Design
First to define some terminology. The _kernel_ is the `main()` function (and later `piccolo_start()` which is called by `main()` and never returns.) The job of the 
kernel is to allow for tasks to be created and then, in a round-robin fashion, pick the next task that needs to be run, save the kernel stack, restore the task's stack and jump to the program counter (PC) last used by the user task.

A _task_ (i.e. _user task_) is a function that is run by Piccolo in a round-robin fashion along with the other _tasks_. For example, a function that flashes the onboard LED. Each _task_ has its own stack, separate from the main stack (which is used by the kernel).

So, there are two types of stack, the Main Stack Pointer (MSP) and Process Stack Pointer (PSP). The Process Stack Pointer (PSP) is used by the current task, and the MSP is used by OS Kernel and exception handlers.

To switch from the kernel to a task, Piccolo needs to save the kernel state on the main stack, restore the user state from the process stack, and jump to the task PC that was saved. To switch from a task to the kernel, the opposite happens, in that the user stack is saved, the kernel stack is restored. The task to kernel switch happens via an interrupt, a SVC.

Piccolo OS uses a set of stacks, one for each task. The stacks are defined in `piccolo_os_internals_t` along with the number of created tasks, plus the index to the current task.

### piccolo_init()
`piccolo_init()` initializes the number of created tasks to zero, then calls the standard Pico SDK initialization function `stdio_init_all()`. After reset, the processor is
in thread (privileged) mode. __piccolo_task_init_stack() switches to handler mode to ensure an appropriate exception return.

Once `piccolo_init()` has been called the rest of `main()`, and any other functions like `piccolo_start()` will be run in handler mode. This can cause problems with the Pico C/C++ SDK, especially with the timers as they are hardware/interrupt based.

### piccolo_create_task()
To create a task the initial stack frame is created. It needs to mimic what would be saved by hardware and by the software. Once the stack is initialized, `__piccolo_pre_switch()` is called to simulate a return from the exception state. The stack is then ready to be used for context switching.

### piccolo_start()
This is an infinite loop that picks the next stack (i.e. next task) to use in a round-robin fashion. When `piccolo_yield()` or `piccolo_syscall()` is called an exception is raised (a SVC exception), which causes the interrupt handler `isr_svcall` to be called.

### piccolo_yield() / piccolo_syscall()
This function is very simple:

```
nop
svc 0
nop
bx lr
```

The SVC instruction causes an exception which is handled by `isr_svcall`.

### isr_svcall()
This is invoked via the SVC exception. It saves the current user task onto the PSP and then restores the kernel stack. It then returns to the last PC used by the kernel before it was switched out. Control returns to the kernel (`main()` or  `piccolo_start()`).

### __piccolo_pre_switch()
`__piccolo_pre_switch()` saves the kernel state, i.e. R4 to R12 (which contains the PSR) and the LR (the return address), onto the main stack. Then, the task state (the register R4 to R11 and the LR) are restored from the task's PSP stack. This is in R0, which is used to set the PSP register. The code then jumps to the LR (restored from the PSP).

If the LR is THREAD_PSP (i.e. 0xFFFFFFFD, a special return address recognized by the CPU) then THREAD_PSP forces a return to Thread mode, execution continues using the PSP.

### piccolo_sleep()
Since Piccolo OS isn't preemptive, then using the Pico's C/C++ sleep functions will cause execution to block. `piccolo_sleep()` is a replacement function that calls `piccolo_yield()` while waiting for the specified amount of time to pass.

## Thread mode and Handler mode in the Cortex-M0+
When the Cortex-M0+ processor is running a program it can be either in Thread mode or Handler mode. Thread mode and Handler mode are almost completely the same.
The only difference is that Thread mode uses (if desired) the Process Stack Pointer (PSP) rather than the Main Stack Pointer (MSP).

After reset, the processor is in Thread mode.

## Context Switching
The Cortex-M0 and Cortex-M0+ processors (also applicable to Cortex-M3/M4/M7) have two Stack Pointers (SPs).
There are two types of stack, the Main Stack Pointer (MSP) and Process Stack Pointer (PSP).
The Process Stack Pointer (PSP) is used by the current task, and the MSP is used by OS Kernel and exception handlers. The stack pointer selection is
determined by the CONTROL register, a special registers.
When a context switch occurs the status is saved on the stack.

### Overview
1. Piccolo OS -> save kernel state on MSP ->
2. restore TASK1 state from PSP_1 -> TASK1 -> save TASK1 state to PSP_1 ->
3. restore kernel state from MSP -> Piccolo OS -> save kernel on MSP ->
4. restore TASK2 state from PSP_2 -> TASK2 -> save TASK2 state to PSP_2 ->
5. restore kernel state from MSP -> Piccolo OS -> save kernel on MSP ->
6. restore TASK3 state from PSP_3 -> TASK3 -> save TASK3 state to PSP_3 ->
7. restore kernel state from MSP -> Go to step 1.

### Process Stack Pointer
```
        Exception frame saved by the hardware onto stack:
        +------+
        | xPSR | 0x01000000 i.e. PSR Thumb bit
        |  PC  | Pointer to task function
        |  LR  | 
        |  R12 | 
        |  R3  | 
        |  R2  | 
        |  R1  | 
        |  R0  | 
        +------+
        Registers saved by the software (isr_svcall):
        +------+
        |  LR  | THREAD_PSP i.e. 0xFFFFFFFD
        |  R7  | 
        |  R6  | 
        |  R5  | 
        |  R4  | 
        |  R11 | 
        |  R10 | 
        |  R9  | 
        |  R8  | 
        +------+
```

### Main Stack Pointer
```
        Exception frame saved by the hardware onto stack:
        +------+
        | xPSR | 0x01000000 i.e. PSR Thumb bit
        |  PC  | Pointer to task function
        |  LR  | 
        |  R12 | 
        |  R3  | 
        |  R2  | 
        |  R1  | 
        |  R0  | 
        +------+
        Registers saved by the software (isr_svcall):
        +------+
        |  LR  |
        |  R7  |
        |  R6  |
        |  R5  |
        |  R4  |
        |  R12 | NB: R12  (i.e IP) is included, unlike user state
        |  R11 |
        |  R10 |
        |  R9  |
        |  R8  | 
        +------+
```

### R0 to R3
When the CPU is interrupted, the hardware will store R0 to R3, the PC etc., onto the stack. It is automatic. In a function like `isr_svcall()` that wants to save the whole context then R4 to R11, etc., are saved. This means all the registered are saved. However, you may have noticed that when there is a switch from the _kernel_ to a _task_ via `__piccolo_pre_switch()` then this is software only (no SVC, no interrupt) and so R0 to R3 are not saved. The reason is that the calling ARM calling convention (when you call a function) states that R0 to R3 are scratch registers and you can't rely on their contents after a branch to another bit of code. So R0 to R3 don't need to be saved as the C compiler knows not to rely on the value of those registers after a function call, and invoking `piccolo_yield()` (when the user task is saved to the PSP stack) is a function call!

## Typical sequence of events

Let say you have two tasks, _task1_ and _task2_. All they do is yield control back to the kernel. Like this:

```
void task1(void) {
  while (true) {
    piccolo_yield();
  }
}
```

Below, {T} means Thread mode, {H} means Handler mode, {I} means Interrupt.

Remember that, the _kernel_ is the `main()` function and later `piccolo_start()` (which is called by `main()` and never returns).

The typical sequence of events, from start-up, is:

1. {T} The processor starts in Thread mode
2. {T} `piccolo_init()` which calls `__piccolo_task_init()`
 * `__piccolo_task_init()` creates a dummy stack and calls `__piccolo_task_init_stack()`
 * `__piccolo_task_init_stack()` saves the kernel state, i.e. R4 to R12 (which contains the PSR) and the LR (the return address), onto the main stack.
 * It then switches to the PSP (which is, in fact, a dummy stack) and triggers an interrupt
3. {I} `isr_svcall()` handles the interrupt. It saves the current task state (R4 to R11 and the LR) onto the PSP (the dummy stack).
 * {I} It then restores the kernel state from the main stack and returns to the kernel using the LR saved on the main stack in 2.
4. {H} After the interrupt, processing continues in `__piccolo_task_init()` and eventually `piccolo_init()` but now in Handler mode.
5. {H} Next _task1_ is created via `piccolo_create_task(&task1);`
6. {H} In `__piccolo_os_create_task()` a new stack is initialized for the task, including the frames saved by the hardware when an interrupt is called (see Context Switching above).
7. {H} Once the stack has been set up, `__piccolo_pre_switch()` is called passing the stack as a parameter.
8. {H} `__piccolo_pre_switch()` saves the kernel state, i.e. R4 to R12 (which contains the PSR) and the LR (the return address), onto the main stack.
9. {H} The task state (the register R4 to R11 and the LR) are restored from the stack passed in at step 7. This is in R0.
10. {H} R0 is set as the PSP and a jump is made to the LR, which is actually THREAD_PSP (i.e. 0xFFFFFFFD, a special return address recognized by the CPU)
11. {T} THREAD_PSP forces a return to Thread mode, execution continues using the PSP. The PSP has the address of _task1_, as set up in step 6. See `stack[15] = (unsigned int)start;` in `__piccolo_os_create_task()`
12. {T} _task1_ is just a loop that calls `piccolo_yield()`
13. {T} `piccolo_yield()` intentionally calls SVC and forces an interrupt that will be handled by `isr_svcall()`
14. {I} `isr_svcall()` handles the interrupt. It saves the state of _tasks1_ task (R4 to R11 and the LR) onto the PSP belonging _task1_ (see steps 10. and 11.).
 * {I} It then restores the kernel state from the main stack and returns to the kernel using the LR saved on the main stack in 8.
15. {H} After the interrupt, processing continues in `main()`
16. {H} Next _task2_ is created via `piccolo_create_task(&task2);`
17. Steps 6. to 15. are repeated, but now for _task2_
18. {H} After the interrupt, processing continues in `main()`. Now that our tasks are created and running, we call `piccolo_start();` 
19. {H} Using a simple round-robin algorithm, `piccolo_start();` just picks the next task and calls `__piccolo_pre_switch()` passing the tasks stack as a parameter.
 * {H} `__piccolo_pre_switch()` saves the kernel state, i.e. R4 to R12 (which contains the PSR) and the LR (the return address), onto the main stack.
 * {H} The task state (the register R4 to R11 and the LR) are restored from the stack passed as the parameter to `__piccolo_pre_switch()`. This is in R0.
 * {H} R0 is set as the PSP and a jump is made to the LR, which is actually THREAD_PSP (i.e. 0xFFFFFFFD, a special return address recognized by the CPU)
 * {T} THREAD_PSP forces a return to Thread mode, execution continues using the PSP. The PSP has the address of where to continue in the task. This address was saved into the LR (and saved onto the PSP stack) when the call to `piccolo_yield()` was made.
 * {T} Execution continues until `piccolo_yield()` is called again.
20. {T} `piccolo_yield()` intentionally calls SVC and forces an interrupt that will be handled by `isr_svcall()`
21. {I} `isr_svcall()` handles the interrupt. It saves the state of the current task (R4 to R11 and the LR) onto the PSP belonging to the task.
 * {I} It then restores the kernel state from the main stack and returns to the kernel using the LR saved on the main stack.
22. {H} After the interrupt, processing continues in `piccolo_start();`
23. Jump to step 19.

### TL;DR

Below, {T} means Thread mode, {H} means Handler mode, {I} means Interrupt.

Remember that, the _kernel_ is the `main()` function and later `piccolo_start()` (which is called by `main()` and never returns).

1. {T} The processor starts in Thread mode, switch to Handler mode
2. {H} Create _task1_
  * {H} Initialize a stack for the task, including the frames saved by the hardware when an interrupt is called (see Context Switching above).
  * {H} `__piccolo_pre_switch()` saves the kernel state, onto the main stack; and restores the task state from the process stack (PSP).
  * {T} Force a return to Thread mode, execution continues using the program counter stored in the PSP.
  * {T} Execution continues until `piccolo_yield()` is called.
3. {T} `piccolo_yield()` intentionally calls SVC and forces an interrupt that will be handled by `isr_svcall()`
4. {I} `isr_svcall()` saves the state of _tasks1_ onto the PSP.  It then restores the kernel state from the main stack and returns to the kernel.
5. {H} Create _task2_
  * {H} Initialize a stack for the task, including the frames saved by the hardware when an interrupt is called (see Context Switching above).
  * {H} `__piccolo_pre_switch()` saves the kernel state, onto the main stack; and restores the task state from the process stack (PSP).
  * {T} Force a return to Thread mode, execution continues using the program counter stored in the PSP.
  * {T} Execution continues until `piccolo_yield()` is called.
6. Now that our tasks are created and running, we call `piccolo_start();` 
7. {H} Using a simple round-robin algorithm, `piccolo_start();` just picks the next task and calls `__piccolo_pre_switch()` passing the tasks stack as a parameter.
 * {H} `__piccolo_pre_switch()` saves the kernel state, onto the main stack.
 * {H} The task state are restored from the task's PSP
 * {T} Force a return to Thread mode, execution continues using the program counter stored in the PSP.
 * {T} Execution continues until `piccolo_yield()` is called again.
8. {T} `piccolo_yield()` intentionally calls SVC and forces an interrupt that will be handled by `isr_svcall()`
9. {I} `isr_svcall()` saves the state of the task onto its PSP.  It then restores the kernel state from the main stack and returns to the kernel (i.e. `piccolo_start();`)
10. Go to step 7.

### Still too long

Below, {T} means Thread mode, {H} means Handler mode, {I} means Interrupt.

Remember that, the _kernel_ is the `main()` function and later `piccolo_start()` (which is called by `main()` and never returns).

1. {T} The processor starts in Thread mode, switch to Handler mode
2. {H} Create _task1_
  * {H} Initialize a stack for it (PSP) then save the kernel state, onto the main stack; and restore the task state from the process stack (PSP).
  * {T} Force a return to Thread mode, execution continues using the program counter stored in the PSP until `piccolo_yield()` is called.
3. {T} `piccolo_yield()` intentionally forces an interrupt that saves the state of _tasks1_ onto the PSP and restores the kernel state from the main stack. Execution continues in the kernel.
4. {H} Create _task2_
  * {H} Initialize a stack for it (PSP) then save the kernel state, onto the main stack; and restore the task state from the process stack (PSP).
  * {T} Force a return to Thread mode, execution continues using the program counter stored in the PSP until `piccolo_yield()` is called.
5. {T} `piccolo_yield()` intentionally forces an interrupt that saves the state of _tasks2_ onto the PSP and restores the kernel state from the main stack. Execution continues in the kernel.
6. Now that our tasks are created and running, we call `piccolo_start()`
7. `piccolo_start()` just picks the next task and calls `__piccolo_pre_switch()` to saves the kernel state, onto the main stack; and then restored the next task from the task's PSP
 * {T} Force a return to Thread mode, execution continues using the program counter stored in the PSP.
 * {T} Execution continues until `piccolo_yield()` is called again.
8. `piccolo_yield()` forces an interrupt that saves the state of the task onto its PSP.  It then restores the kernel state from the main stack and returns to the kernel (i.e. `piccolo_start();`)
10. Go to step 7.


### Give me the Tom and Jerry version

Remember that, the _kernel_ is the `main()` function and later `piccolo_start()` (which is called by `main()` and never returns).

1. Create _task1_ and start running it using its own stack (PSP). It will run until `piccolo_yield()` is called.
2. Via an interrupt `piccolo_yield()` will saves the state of _tasks1_ onto its PSP and restore the kernel state from the main stack. Execution continues in the kernel.
3. Create _task2_ and start running it using its own stack (PSP). It will run until `piccolo_yield()` is called.
4. Via an interrupt `piccolo_yield()` will saves the state of _tasks2_ onto its PSP and restore the kernel state from the main stack. Execution continues in the kernel.
5. Now that our tasks are created and running, we call `piccolo_start()`
6. `piccolo_start()` just picks the next task, saves the kernel state, onto the main stack; and then restores the next task from the task's PSP
7. Continue executing the next task using its own stack until `piccolo_yield()` is called.
8. Via an interrupt `piccolo_yield()` will saves the state of the current task onto its PSP and restores the kernel state from the main stack. Execution continues in the kernel (i.e. in `piccolo_start()`).
9. Go to 6.

## Pre-emptive
At the moment Piccolo OS is co-operative, in that a task will continue to run until `piccolo_yield()` is called.

It should be possible to force a context switch using a timer or an interrupt like SysTick which in turns triggers a PendSV. However, my attempts to implement this have so far failed. I have ported the same code to an STM32 BluePill with a Cortex-M3 and pre-emptive tasking works via SysTick/PendSV.

My initial thoughts are that once `main()` is running in handler mode then the Pico C/C++ SDK doesn't process interrupts as expected. The "traditional" approach is to set the
interrupt priorities so that the SysTick has a high priority, however my attempts to do that that have so far been without success.

More work is needed.

## Resources
https://datasheets.raspberrypi.org/pico/raspberry-pi-pico-c-sdk.pdf

https://raspberrypi.github.io/pico-sdk-doxygen/index.html

https://interrupt.memfault.com/blog/cortex-m-rtos-context-switching

https://www.adamh.cz/blog/2016/07/context-switch-on-the-arm-cortex-m0/

https://chromium.googlesource.com/chromiumos/platform/ec/

https://github.com/n-k/cortexm-threads

https://github.com/scttnlsn/cmcm

https://github.com/chris-stones/ShovelOS

https://github.com/jserv/mini-arm-os

https://stackoverflow.com/questions/48537618/cortex-m0-setting-the-priority-of-the-system-exception

https://developer.arm.com/documentation/dui0552/a/the-cortex-m3-processor/exception-model/exception-entry-and-return

https://developer.arm.com/documentation/dui0497/a/the-cortex-m0-processor/programmers-model/core-registers

https://github.com/dwelch67/raspberrypi-pico

https://github.com/davidgiven/FUZIX/tree/rpipico/Kernel/platform-rpipico

https://archive.fosdem.org/2018/schedule/event/multitasking_on_cortexm/attachments/slides/2602/export/events/attachments/multitasking_on_cortexm/slides/2602/Slides.pdf

## License - 3-Clause BSD License
Copyright (C) 2021, Gary Sims
All rights reserved.

SPDX short identifier: BSD-3-Clause

## Additional Copyrights
Some portions of code, intentionally or unintentionally, may or may not be attributed to the following people:

Copyright (C) 2017 Scott Nelson: CMCM - https://github.com/scttnlsn/cmcm

Copyright (C) 2015-2018 National Cheng Kung University, Taiwan: mini-arm-os - https://github.com/jserv/mini-arm-os

Copyright (C) 2014-2017 Chris Stones: Shovel OS - https://github.com/chris-stones/ShovelOS
