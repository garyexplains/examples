@ Assemble like this:
@ as -o loop.o loop.s
@ gcc -o loop loop.o

	.data
string:	.asciz "Loop: %d\n"
i:	.word	1

	.text
	.global main
	.extern printf

main:
	push {ip, lr}

	@ load i into r2
	ldr r2, =i
	ldr r2, [r2]

loop:
	@ print i
	ldr r0, =string
	mov r1, r2
	bl printf

	@ i = i + 1
	ldr r2, =i
	ldr r2, [r2]
	mov r3, #1
	add r2, r2, r3
	ldr r3, =i
	str r2, [r3]

	@ if i <= 10 branch to loop:
	cmp r2, #10
	ble loop

	pop {ip, pc}
