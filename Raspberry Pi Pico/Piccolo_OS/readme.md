# Piccolo OS
Piccolo OS is a small multitasking OS for the Raspberry Pi Pico. It is designed primarily as a teaching tool.
It demonstrates the fundamentals of a co-operative multitasking OS and the Arm Cortex-M0+.

## Limitations
Many! Including lack of per-task memory, multicore support, mutexes, queues, a file system, networking, a shell, and so on...

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
        |  PC  | Pointer to task function
        |  LR  | 
        |  R12 | 
        |  R3  | 
        |  R2  | 
        |  R1  | 
        |  R0  | 
        +------+
        Registers saved by the software (isr_svcall):
        +------+
        |  LR  | THREAD_PSP i.e. 0xFFFFFFFD
        |  R7  | 
        |  R6  | 
        |  R5  | 
        |  R4  | 
        |  R11 | 
        |  R10 | 
        |  R9  | 
        |  R8  | 
        +------+
```

### Main Stack Pointer
```
        Exception frame saved by the hardware onto stack:
        +------+
        | xPSR | 0x01000000 i.e. PSR Thumb bit
        |  PC  | Pointer to task function
        |  LR  | 
        |  R12 | 
        |  R3  | 
        |  R2  | 
        |  R1  | 
        |  R0  | 
        +------+
        Registers saved by the software (isr_svcall):
        +------+
        |  LR  |
        |  R7  |
        |  R6  |
        |  R5  |
        |  R4  |
        |  R12 | NB: R12  (i.e IP) is included, unlike user state
        |  R11 |
        |  R10 |
        |  R9  |
        |  R8  | 
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
