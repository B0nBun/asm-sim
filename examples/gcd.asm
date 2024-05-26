hex_prefix: "0x"
hex: "0123456789ABCDEF"
start:
    addi $1, $0, 3233
    addi $2, $0, 3127

loop:
    beq $2, $0, print_a
    bleq $1, $2, branch
    sub $1, $1, $2
    beq $0, $0, loop
branch:
    sub $2, $2, $1
    beq $0, $0, loop

print_a:
    lw $2, $0, hex_prefix
    sw $2, $0, output
    addi $2, $0, 1
    lw $2, $2, hex_prefix
    sw $2, $0, output
print_loop:
    andi $2, $1, 15
    lw $2, $2, hex
    sw $2, $0, output
    shr $1, $1, 4
    beq $1, $0, break
    beq $0, $0, print_loop
break:
    halt
