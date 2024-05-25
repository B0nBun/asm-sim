hello: "Hello, World!\0"

start:
    addi $1, $0, 0
loop:
    lw $2, $1, hello
    beq $2, $0, break
    sw $2, $0, output
    addi $1, $1, 1
    beq $0, $0, loop
break:
    halt