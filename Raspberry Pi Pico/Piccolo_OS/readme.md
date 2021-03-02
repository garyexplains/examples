# Piccolo OS
Piccolo OS is a small multitasking OS for the Raspberry Pi Pico. It is designed primarily as a teaching tool.
It demonstrates the fundamentals of a co-operative multitasking OS and the Arm Cortex-M0+.

## Limitations
Many! Including lack of per-task memory, multicore support, mutexes, queues, a file system, networking, a shell, and so on...

## Design
First to define some terminology. The _kernel_ is the `main()` function (or in this case the `piccolo_start()` which is called by `main()` and never returns.) The job of the 
kernel is to pick the next task that needs to be run, save the kernel stack, restore the tasks stack and jump to the program counter (PC) last used by the user task.

A _task_ (i.e. _user task_) is a function that is run by Piccolo in a round-robin fashion along with the other _tasks_. For example, a function that flashes the onboard LED.

To switch from the kernel to a task, Piccolo just needs to save the kernel stack, restore the user stack and jump to the PC that was saved. To switch from a task to the kernel, the opposite happens, in that the user stack is saved, the kernel stack is restored. However, this needs to happen via an interrupt, a SVC.

Piccolo OS uses a set of stacks, one for each task. The stacks are defined in `piccolo_os_internals_t` along with the number of created tasks, plus the index to the current task.

### piccolo_init()
`piccolo_init()` initializes the nyumber of created tasks to zero, then calls the standard Pico SDK initialization function `stdio_init_all()`. After reset, the processor is
in thread (privileged) mode. __piccolo_task_init_stack() switches to handler mode to ensure an appropriate exception return.

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
This is invoked via the SVC exception. It saves the current user task onto the PSP and then restores the kernel stack. It then returns to the last PC used by the kernel before it was switched out. Control returns to `piccolo_start()` where the next task is selected and the user stack restored and that task continues.

### __piccolo_pre_switch()

### piccolo_sleep()

## Context Switching
The Cortex-M0 and Cortex-M0+ processors (also applicable to Cortex-M3/M4/M7) have two Stack Pointers (SPs).
There are two types of stack, the Main Stack Pointer (MSP) and Process Stack Pointer (PSP).
The Process Stack Pointer (PSP) is used by the current task, and the MSP is used by OS Kernel and exception handlers. The stack pointer selection is
determined by the CONTROL register, a special registers.
When a context switch occurs the status is saved on the stack.

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
Copyright (C) 2021 Gary Sims

SPDX short identifier: BSD-3-Clause

## Copyrights
Some portions of code, intentionally or unintentionally, may or may not be attributed to the following people:

Copyright (C) 2017 Scott Nelson: CMCM - https://github.com/scttnlsn/cmcm

Copyright (C) 2015-2018 National Cheng Kung University, Taiwan: mini-arm-os - https://github.com/jserv/mini-arm-os

Copyright (C) 2014-2017 Chris Stones: Shovel OS - https://github.com/chris-stones/ShovelOS
