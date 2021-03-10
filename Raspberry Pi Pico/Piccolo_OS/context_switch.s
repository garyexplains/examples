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
 
.thumb
.syntax unified

.type isr_svcall, %function
.global isr_svcall
isr_svcall:
	mrs r0, psp

    /* Save r4, r5, r6, r7, and lr first
    even though that isn't the stack order, as we need
    to use those registers in a moment */

    subs r0, #4
    mov r1, lr
    str r1, [r0]

    subs r0, #16
    stmia r0!, {r4,r5, r6, r7}
    
    mov	r4, r8
	mov	r5, r9
	mov	r6, r10
	mov	r7, r11
    subs r0, #32
    stmia r0!, {r4,r5, r6, r7}
    subs r0, #16 /* fix r0 to point to end of stack frame, 36 bytes from original r0 */

	/* load kernel state from stack*/

    /*
	+------+
	|  LR  |
	|  R7  |
	|  R6  |
	|  R5  |
	|  R4  |
	|  R12 | NB: R12  (i.e IP which holds the PSR) is included, unlike user state
	|  R11 |
	|  R10 |
	|  R9  |
	|  R8  | <- POP from here
	+------+
	*/

    pop {r1, r2, r3, r4, r5}
    mov r8, r1
    mov r9, r2
    mov r10, r3
    mov r11, r4
    mov r12, r5 /* r12 is ip */
    pop {r4, r5, r6, r7}       

	msr psr_nzcvq, ip

    pop {pc}

.global __piccolo_pre_switch
__piccolo_pre_switch:
	/* save kernel state */
    /*
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
	*/

	mrs ip, psr
    push {r4, r5, r6, r7, lr}
    mov r1, r8
    mov r2, r9
    mov r3, r10
    mov r4, r11
    mov r5, r12
    push {r1, r2, r3, r4, r5}    

	/* load user state */ 
    /*
	+------+
	|  LR  |
	|  R7  |
	|  R6  |
	|  R5  |
	|  R4  |
	|  R11 |
	|  R10 |
	|  R9  |
	|  R8  | <- r0
	+------+
	*/

    ldmia	r0!,{r4-r7}
	mov	r8, r4
	mov	r9, r5
	mov	r10, r6
	mov	r11, r7
	ldmia	r0!,{r4-r7}
    ldmia	r0!,{r1}
    mov lr, r1
	msr psp, r0 /* r0 is usertask_stack_start from activate(usertask_stack_start); */

	/* jump to user task */
	bx lr

.global __piccolo_task_init_stack
__piccolo_task_init_stack:
	/* save kernel state */
    /*
	+------+
	|  LR  |
	|  R7  |
	|  R6  |
	|  R5  |
	|  R4  |
	|  R12 | NB: R12 (i.e IP which holds the PSR) is included, unlike user state
	|  R11 |
	|  R10 |
	|  R9  |
	|  R8  | 
	+------+
	*/

	mrs ip, psr
    push {r4, r5, r6, r7, lr}
    mov r1, r8
    mov r2, r9
    mov r3, r10
    mov r4, r11
    mov r5, r12
    push {r1, r2, r3, r4, r5}    

	/* switch to process stack */
	msr psp, r0
	movs r0, #3
	msr control, r0
	isb
	/* intentionally continue down into piccolo_syscall */
	/* same as bl piccolo_syscall, if the code wasn't below */

.global piccolo_yield
.global piccolo_syscall
piccolo_yield:
piccolo_syscall:
    nop
	svc 0
	nop
	bx lr
