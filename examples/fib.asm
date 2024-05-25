hex_prefix: "0x"
hex: "0123456789ABCDEF"
start:
addi $1, $0, 1         ; uint32_t x = 1;
addi $2, $0, 1         ; uint32_t y = 1;
addi $3, $0, 0         ; uint32_t z = 0;
addi $4, $0, 0         ; uint32_t sum = 0;
addi $5, $0, 4000000   ; uint32_t until = 4000000;
loop:                  ; do {
    add $3, $1, $2     ;   z = x + y;
    addi $1, $2, 0     ;   x = y;
    addi $2, $3, 0     ;   y = z;
    add $4, $4, $2     ;   sum += z;
    add $3, $1, $2     ;   z = x + y;
    add $3, $3, $2     ;   z += y;
    add $1, $1, $2     ;   x += y;
    addi $2, $3, 0     ;   y = z;
    bleq $2, $5, loop  ; } while (y <= until);

lw $1, $0, hex_prefix
sw $1, $0, output
addi $1, $0, 1
lw $1, $1, hex_prefix
sw $1, $0, output
print_loop:
    andi $1, $4, 15
    lw $1, $1, hex
    sw $1, $0, output
    shr $4, $4, 4
    beq $4, $0, break
    beq $0, $0, print_loop
break:
    halt

