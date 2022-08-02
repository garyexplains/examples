; Assemble with:
; vasm6502_oldstyle -Fbin -dotdir loop.s

  .org $0000
start:
  LDX #$08
decrement:
  DEX
  STX $0200
  CPX #$03
  BNE decrement
  STX $0201
  JMP start

  .org $fffc
  .word start
  .word $0000
